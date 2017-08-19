from openerp import models, fields, api,_
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import date
from openerp import SUPERUSER_ID

_list_tab_style = [
                   (1,"Flavor Concentration Matrix"),
                   (2,"Products List"),
                   (3,"Marketing"),
                   (4,"Free Samples List"),
                   (5,"Free Samples Matrix"),
                ]

_type_of_product = [
                     ('consu','Consumable Product'),
                     ('product','Stockable Product'),
                     ]

class product_tab(models.Model):
    _name = "product.tab"
    _description = "Product Tab"
    _order = "sequence asc"
    
    def fetch_static_data(self,cr,uid,context=None):
        res = {}
        products = self.pool.get('product.product')
        taxes = self.pool.get('account.tax')
        tabs = self.search_read(cr,SUPERUSER_ID,order="sequence")
        marketing_package = self.pool.get('marketing.package')
        for i in tabs:
            if i.get("tab_style",False) == 3:
                package_ids = i.get('marketing_packages_ids',False)
                if package_ids:
                    i.update({
                              "marketing_packages_ids":marketing_package.get_marketing_package(cr,uid,package_ids)
                              })
                    
            if len(i.get('product_ids',False)) > 0:
                product_info = products.read(cr,uid,i.get('product_ids'),fields=['name','vol_id','conc_id','flavor_id','lst_price','virtual_available','incoming_qty'])
                i["product_ids"] = {}
                i["product_ids"] = {product['id']:product for product in product_info}
        res.update({'tabs':tabs})
        tax_info = taxes.search_read(cr,uid,domain=[['type','=','percent'],['type_tax_use','=','sale'],['price_include','=',False]],fields=['id','name','amount'])
        res.update({
                    'taxes':tax_info
                    })
        nmi_journal = self.pool.get('account.journal').search(cr,uid,[('is_nmi_journal','=',True)],limit=1)
        res.update({
                'nmi_journal_id':nmi_journal and nmi_journal[0] or False,
            })
        return res
    
    @api.model
    def _get_attribute_domain(self):
        # We have access to self.env in this context.
        ids = self.env.ref('jjuice.attribute_vol').id
        return [('attribute_id','=', ids)]
    
    
    @api.model  
    def _create_product(self,pairs):
        #(tab_id,flavor_id,vol_id,conc_id) ---> pair
        product_obj = self.env['product.product']
        product_ids = []
        for pair in pairs:
            vals = {
                    'tab_id':pair[0],
                    'flavor_id': pair[1].id,
                    'vol_id':pair[2].id,
                    'conc_id':pair[3].id,
                    'type':self.consumable_stockable,
                    'name':" | ".join([pair[1].name,pair[2].name,pair[3].name]), 
                    'sale_ok':True,
                    'purchase_ok':True,
                }
            if self.uom_id:
                vals.update({'uom_id':self.uom_id.id,'uom_po_id':self.uom_id.id})
            product_id = product_obj.create(vals)
            product_ids.append(product_id)
        return product_ids
    
    @api.model
    def _delete_product(self,pairs):
        #(tab_id,flavor_id,vol_id,conc_id) ---> pair
        product_obj = self.env['product.product']
        for pair in pairs:
            product_ids = product_obj.search([('tab_id','=',pair[0]),('flavor_id','=',pair[1].id),
                                ('vol_id','=',pair[2].id),('conc_id','=',pair[3].id)])
            if product_ids:
                product_ids.unlink()
        return True
    
    @api.model
    def _create_pair_products(self,existing_pairs = [],new_pairs = []):
        '''
            * First check if existing pair are equal to new pairs. If yes then just do not do anything.
                If they are not equal then do the following.
                1. First find out the intersection (These pair will be kept as it is and not touched
                2. E - N will give us set of all the pairs that have been deleted
                3. N - E will give all set of the pairs that have to be created
            
            * the pairs will be list of tuple and the tuple will have the elements in position as follows (tab_id,flavor_id,vol_id,conc_id)  
        '''
        e_minus_n = set(existing_pairs) - set(new_pairs)
        n_minus_e = set(new_pairs) - set(existing_pairs)
        created_product_ids = []
        if e_minus_n:
            self._delete_product(e_minus_n)
        if n_minus_e:
            created_product_ids.append(self._create_product(n_minus_e))
        return True
        
    @api.model
    def create(self,vals):
        result =  super(product_tab,self).create(vals)
        if (result.tab_style == 1 or result.tab_style == 5) and result.flavor_conc_line :
            new_pairs = result._create_pair()
            result._create_pair_products(new_pairs = new_pairs)
        return result
    
    @api.model
    def _create_pair(self):
        pairs = []
        for line in self.flavor_conc_line:
            tab_id,flavor_id,vol_id = line.tab_id.id,line.flavor_id,line.tab_id.vol_id 
            for conc in line.conc_ids:
                pairs.append((tab_id,flavor_id,vol_id,conc))
        return pairs        
        
    @api.multi
    def write(self,vals):
        # The list will contain tuples with the following position
        # 0:tab_id,1:(flavor_id,flavor name),2:vol_id,3:conc_id
        if vals.get('flavor_conc_line',False):    
            existing_pairs,new_pairs = [],[]
            existing_pairs = self._create_pair()
            result =  super(product_tab,self).write(vals)
            new_pairs = self._create_pair()
            self._create_pair_products(existing_pairs,new_pairs)
        else:
            result =  super(product_tab,self).write(vals)
        
        if vals.get('vol_id',False):
            self.product_ids.write({'vol_id':vals.get('vol_id',False)})
        if vals.get('consumable_stockable',False):
            self.product_ids.write({'type':vals.get('consumable_stockable',False)})
        return result
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)',
            'Name of a tab must be unique!'),
    ]    
    
    def calculate_discount(self,internal=0,external=0):
        internal = float(internal)
        discount_factor = ((100.00-internal) * (100.00-external))/100
        discount = 100 - discount_factor
        return discount
    
    def create_order(self,cr,uid,result,context=None):
        partner_id = result.get('partner_id',[False])
        action = {}
        # ACTIVE PARTNER
        if not result.get('partner_id',False):
            raise Warning(_('Due to technical problems we are not able to fetch the customer ID. Please contact your developer'))

        # DISCOUNT PERCENTAGE
        discount_percentage = result.get("discount_percentage",0)
        
        #TAXES
        taxes = result.get('taxes',False)
        
        #SHIPPING AND HANDLING
        if result.get("s_h",False) and result.get("s_h",0) > 0: 
            cr.execute('''
                select id from product_product where shipping = true and active = true
            ''')
            s_h_id = cr.fetchone()
            if not s_h_id:
                raise Warning(_('No shipping product created.Please start a new tab and first create a shipping product by tickng the shipping option on a product variant'))
            else:
                result['lines'].append([0,0,{
                                      'product_id':s_h_id[0],
                                      'product_uom_qty':1,
                                      'price_unit':result.get("s_h",0),
                                      'discount':0,
                                      }])
                
        # CHECK PAYMENT PLANS
        for plan in  result.get("payment_plan",[]):
            if (not plan[2].get('amount_original')) or plan[2].get('amount_original') == 0:
                raise Warning(_('Payment Plan amount cannot be zero'))
            if (not plan[2].get('method_of_payment')):
                raise Warning(_('Method of payment is required for payment plan'))
            if not plan[2].get('date',False):
                plan[2].update({
                             'date':date.today().strftime('%Y-%m-%d'),
                             })
            plan[2].update({
                         'partner_id':partner_id
                         })
            
        # Sale Order Lines Discount Setting and taxes addition
        for line in result.get("lines",False):
            discount = self.calculate_discount(line[2].get('discount',0),discount_percentage) #line discount and external discount
            line[2].update({
                            "discount":discount,
                            "tax_id":result.get("taxes",[]),
                            })
        order_id = self.pool.get('sale.order').create(cr,uid,{
                                                                'partner_id':partner_id,
                                                                'note':result.get("order_notes",""),
                                                                'order_line':result.get("lines",[]),
                                                                'payment_plan_ids':result.get("payment_plan",[])
                                                                },context)
                        
        if result.get("paid",False) and result.get('paid',False) > 0:
            paid = result.get("paid",False)
            payment_method = result.get('payment_method',False)
            if not payment_method:
                raise Warning(_("Please enter the payment method!!"))
            res = self.pool.get("sale.order").confirm_sales_order(cr,uid,[order_id],paid,payment_method,context)
            return res
        else:
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale','view_order_form')
            action = {
                         'type': 'ir.actions.act_window',
                         'view_type': 'form',
                         'res_id':order_id,
                         'view_mode': 'form',
                         'res_model': 'sale.order',
                         'views': [[view_id, 'form']],
                         'view_id': view_id,
                         'target': 'current',
                         'context':{},
                       };
            return action
    
    name = fields.Char('Tab Name',size=30,required=True)
    visible_all_customers = fields.Boolean("Visible to all Customers")
    specific_customer_ids = fields.Many2many('res.partner','product_tab_res_partners','tab_id','partner_id',string = "Customers",help = "List of Customer to whom this tab will be available to")
    tab_style = fields.Selection(_list_tab_style,string = "Tab Style",required=True,help = "These are options available that will format and determine the functionality of tab")
    product_ids = fields.One2many('product.product','tab_id','Products',help = "List of products belonging to this tab")
    vol_id = fields.Many2one('product.attribute.value',"Volume" ,domain = _get_attribute_domain)
    consumable_stockable = fields.Selection(_type_of_product,"Type of Product",required=True)
    sequence = fields.Integer('Sequence')
    active = fields.Boolean("Active",default=True)
    uom_id = fields.Many2one('product.uom','Unit of Measure')
    marketing_packages_ids = fields.Many2many("marketing.package",'tab_id','package_id',string = "Marketing Packages",help = "Useful if the tab style is Marketing")
    flavor_conc_line = fields.One2many(
                                        'flavor.conc.details','tab_id',"Flavors & Concentration Details"
                                        )
    input_width = fields.Char("Width",required=True,default="50px")
    
class flavor_concentration_details(models.Model):
    _name = "flavor.conc.details"
    _description = "flavor and Concentration detail for tabs"
    
    @api.model
    def create(self,vals):
        return super(flavor_concentration_details,self).create(vals)
    
    @api.model
    def _get_attribute_domain(self):
        # We have access to self.env in this context.
        ids = self.env.ref('jjuice.attribute_conc').id
        return [('attribute_id','=', ids)]    
    
    tab_id = fields.Many2one('product.tab','Tabs',ondelete='cascade', select=True)
    flavor_id = fields.Many2one('product.flavors','Flavor')
    conc_ids = fields.Many2many('product.attribute.value','details_conc','detail_id','conc_id','Concentrations',domain = _get_attribute_domain)
     