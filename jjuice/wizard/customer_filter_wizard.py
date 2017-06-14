from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

class customer_filter_wizard(models.TransientModel):
    _name = "customer.filter.wizard"
    _description = "Customer filter wizard"
    
    def get_customer_type_of_account(self,cr,type_of_account):
        cr.execute('''
            select id from res_partner where acccount_type = '%s'
        '''%(type_of_account))
        customer_list = cr.fetchall()
        return customer_list
    
    def get_customer_account_finance(self,cr,type):
        cr.execute('''
            select id from res_partner where classify_finance = '%s'
        '''%(type))
        customer_list = cr.fetchall()
        return customer_list    
    
    def get_customer_not_product_line(self,cr,attr):
        # This will return the list of customers who have order the product line with attributes id in attr
        attr_list = map(lambda x:x.id,attr)
        attr_list.append(0) # This is to avoid conversion of list with single element to tuple coz then the tuple is like (x,) and this format gives 
        #error in query
        attr_list = tuple(attr_list)
        cr.execute('''
            select invoice.partner_id from account_invoice_line as line left join account_invoice as invoice on line.invoice_id = invoice.id
                left join product_product as product on product.id   = line.product_id left join product_attribute_value_product_product_rel
                    as rel on rel.prod_id = product.id where rel.att_id in {0}
                    '''.format(attr_list))
        customer_list = cr.fetchall()
        return customer_list
    
    def get_customer_last_order_date(self,cr,last_order_date):
        # This method return the list of customers who have ordered after the given date
        cr.execute('''
            select partner_id from account_invoice where date_invoice >= '%s'
        '''%(last_order_date))
        customer_list  = cr.fetchall()
        return customer_list

    def get_all_customers(self,cr):
        cr.execute('''
            select id from res_partner where customer = true
        ''')
        customer_list = cr.fetchall()
        return customer_list

    def get_customer_sales_person(self,cr,user_ids):
        attr_list = map(lambda x: x.id,user_ids)
        attr_list.append(0)
        attr_list = tuple(attr_list)
        cr.execute('''
            select id from res_partner where user_id in {0}
        '''.format(attr_list))
        customer_list = cr.fetchall()
        return customer_list
    
    def get_customer_acquisition_source(self,cr,source):
        cr.execute('''
            select partner.id from res_partner as partner left join account_acquisition as source on source.id = partner.acquisition_id
                where source.source = '%s'
        '''%(source))
        partner_list = cr.fetchall()
        return partner_list
    
    def get_customer_acquisition_source_name(self,cr,source_id):
        cr.execute('''
            select id from res_partner as partner where acquisition_id = %s
        '''%(source_id))
        partner_list = cr.fetchall()
        return partner_list        
    
    def dummy_buttons(self,cr,uid,ids,context=None):
        return True
    
    def filter_customers(self,cr,uid,ids,context=None):
        assert len(ids) == 1
        total_customer_list = set(self.get_all_customers(cr))
        final_customer_list = set([])
        wizard = self.browse(cr,uid,ids[0],context)
        for index,i in enumerate(wizard.line_ids): # to check whether it is the first loop so that first loop will always be OR
            if i.field_type == 'last_order_date':
                customer_list = total_customer_list - set(self.get_customer_last_order_date(cr,i.last_order_date))
            elif i.field_type == "not_product_line":
                customer_list = total_customer_list - set(self.get_customer_not_product_line(cr,i.volume_attributes))
            elif i.field_type == "type_account":
                customer_list = set(self.get_customer_type_of_account(cr,i.type_of_account))
            elif i.field_type == "classify_finance":
                customer_list = set(self.get_customer_account_finance(cr,i.classify_finance))
            elif i.field_type == "sales_person":
                customer_list = set(self.get_customer_sales_person(cr,i.user_ids))
            elif i.field_type == "acquisition_source":
                customer_list = set(self.get_customer_acquisition_source(cr,i.acquisition_source))
            elif i.field_type == "acquisition_source_name":
                customer_list = set(self.get_customer_acquisition_source_name(cr,i.acquisition_source_name.id))
                
            if i.operator == 'or' or index == 0:
                final_customer_list = final_customer_list.union(customer_list)
            elif i.operator == 'and':
                final_customer_list = final_customer_list.intersection(customer_list)                
        final_customer_list = list(final_customer_list)
        list_customers = map(lambda x:x[0],final_customer_list) 
        return list_customers
    
    def _constraint_line_account(self,cr,uid,ids,context=None):
        for i in ids:
            cr.execute('''
                        select field_type from customer_filter_wizard_line where wizard_id = %s
                       '''%(i))
            type_list  = cr.fetchall()
            if len(type_list)!=len(set(type_list)):
                return False
            else:True
        return True
            
    _constraints = [
                    (_constraint_line_account,"No two constraint lines can have the same constraints",['line_ids'])
                    ]

    line_ids = fields.One2many('customer.filter.wizard.line','wizard_id','Add Constraints')

ACCOUNT_TYPE  = [('smoke_shop',"Smoke Shop"),('vape_shop','Vape Shop'),('convenient_gas_store','Convenient Store/ Gas Station'),
                 ('website','Online Store'),
                 ]
FINANCE_CLASSIFY  = [
                 ('retailer','Retailer'),
                 ('wholesale','Wholesaler / Distributer'),
                 ('private_label','Private Label'),
                 ('website','Vapejjuice.com'),
                 ]

_SOURCE = [
           ('trade_show','Trade Show'),
           ('sales_trip','Sales Trip'),
           ('magazine_add','Magazine Add'),
           ('referral','Referral'),
           ]
        
class customer_fitler_wizard_line(models.TransientModel):
    _name = "customer.filter.wizard.line"
    _description = "Customer Filter Wizard Line"
    
    wizard_id = fields.Many2one('customer.filter.wizard')
    operator = fields.Selection([
                                 ('and','AND'),('or','OR')
                                 ],string='Operator',default='or',required=True)
    field_type = fields.Selection([
                                   ('last_order_date','Last Order Date'),('type_account','Type of Account'),
                                   ('not_product_line','Does not have Product line'),
                                   ('classify_finance','Account Classification (for Finance)'),
                                   ('sales_person',"Sales Person"),
                                   ('acquisition_source','Acquisition Source'),
                                   ('acquisition_source_name','Acquisition Source Value')
                                   ],string = 'Constraint On',required=True)
    last_order_date = fields.Date('Last Order Date')
    type_of_account = fields.Selection(ACCOUNT_TYPE,'Type of Account')
    classify_finance = fields.Selection(FINANCE_CLASSIFY,"Account Classification (for Finance)")
    user_ids = fields.Many2many('res.users','customer_filter_wizard_filer_res_partner','wizard_id','user_id','Sales Person')
    volume_attributes = fields.Many2many('product.attribute.value','customer_filter_line_attributes','line_id','attribute_id',string='Product Line')                              
    acquisition_source = fields.Selection(_SOURCE,string='Acquisition Source')
    acquisition_source_name = fields.Many2one('account.acquisition','Acquisition Source Value')