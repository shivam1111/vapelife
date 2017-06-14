from openerp.osv import fields, osv 
from openerp.tools.translate import _
from openerp.addons.crm import crm
from openerp.addons.base.res.res_partner import format_address
from openerp import SUPERUSER_ID

crm.AVAILABLE_PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3','High'),
    ('4', 'Very High'),
    ('5','Very Very High')
]

FINANCE_CLASSIFY  = [
                 ('retailer','Retailer'),
                 ('wholesale','Wholesaler / Distributer'),
                 ('private_label','Private Label'),
                 ('website','Vapejjuice.com'),
                 ]

ACCOUNT_TYPE  = [('smoke_shop',"Smoke Shop"),('vape_shop','Vape Shop'),('convenient_gas_store','Convenient Store/ Gas Station'),
                 ('website','Online Store'),
                 ]


class crm_lead(format_address, osv.osv):
    _inherit = 'crm.lead'
    
    def trasnfer_leads_partners(self,cr,uid,ids,context):
        partner = self.pool.get('res.partner')
        leads = self.pool.get('crm.lead')
        lead_ids = leads.search(cr,uid,['|', ('type','=','lead'), ('type','=',False)],context=context)
        for i in  leads.browse(cr,uid,lead_ids,context):
            use_parent_address = False
            company_vals = {}
            contact_vals = {}
            comment = ""
            company_id = False
            comment = comment+ "Subject: %s\n"%(i.name)
            if i.referred:
                comment = comment + "Referred By: %s\n"%(i.referred)
            #Check if there is a company
            if i.partner_name:
                use_parent_address = True
                company_vals.update({
                                    'name':i.partner_name,
                                    'is_company':True,
                                    'user_id': i.user_id and i.user_id.id or False,
                                    'leads':True,
                                    'phone':i.phone,
                                    'mobile':i.mobile,
                                    'fax':i.fax,
                                    'email':i.email_from,
                                    'street':i.street,
                                    'street2':i.street2,
                                    'city':i.city,
                                    'state_id':i.state_id and i.state_id.id or False,
                                    'zip':i.zip,
                                    'country_id':i.country_id and i.country_id.id or False,
                                    'date_field':i.date_field,
                                    'lead_type':i.lead_type,
                                    'how_met':i.how_met,
                                    'function':i.function,
                                    'priority':i.priority,
                                    'comment':comment,
                                    'type':'contact',
                                    'customer':False,
                                    
                                })
                company_id = partner.create(cr,uid,company_vals,context)
            if i.contact_name:
                contact_vals.update({
                                     'name':i.contact_name,
                                     'type':'contact',
                                     'customer':False,
                                     'comment':comment,
                                     'is_company':False,
                                     'user_id': i.user_id and i.user_id.id or False,
                                     'use_parent_address':use_parent_address,
                                     'leads':True,
                                     'phone':i.phone,
                                     'mobile':i.mobile,
                                     'fax':i.fax,
                                     'email':i.email_from,
                                     'date_field':i.date_field,
                                     'lead_type':i.lead_type,
                                     'how_met':i.how_met,
                                     'function':i.function,
                                     'priority':i.priority,
                                     'parent_id':company_id,
                                     })
                partner.create(cr,uid,contact_vals,context)
        return True
    
    
    _columns = {
                'priority': fields.selection(crm.AVAILABLE_PRIORITIES, 'Priority', select=True),
                }
    
 # this class are used for adding field in employee 
class hr_employee(osv.osv):
    _inherit='hr.employee'
    _description='jjuice module'
    _columns={
            'photo_dl':fields.binary('Photo of Driver License'),
            'skype_id': fields.char('Skype Id', size=240),
 }
    
class res_partner(osv.osv):
    _inherit='res.partner'
    _description='JJUICE'
    
    def create(self,cr,uid,vals,context):
        return super(res_partner,self).create(cr,uid,vals,context)
    
    _columns={
        'skype_id': fields.char('Skype Id', size=240),
        'resale_no': fields.char('State Issued Resale Number', size=240),
        'acccount_type':fields.selection (ACCOUNT_TYPE,string = "Type Of Account"),
        'classify_finance':fields.selection(FINANCE_CLASSIFY,string="Account Classification(For Finance)"),
        'm2m':fields.one2many("partner.lead",'partner2'),
        'date_field':fields.date('Date we first met'),
        'lead_type':fields.selection([('Hot Lead','Hot Lead'),('Warm Lead','Warm Lead'),('Still No Contact','Still No Contact'),('60-90 Days','60-90 Days'),('Not Interested','Not Interested')],string="Type of Lead"),
        'how_met':fields.text('How we met'),
        'priority':fields.selection(crm.AVAILABLE_PRIORITIES,'Priority')
        }
    
class res_partner_lead(osv.osv):
    _name='partner.lead'
    _columns={'notes':fields.text("Notes"),
              'display_partner':fields.many2one("res.partner","Account"),
              'display_lead':fields.many2one("crm.lead","Leads"),
              'partner2':fields.many2one("res.partner"),
              'lead2':fields.many2one("crm.lead"),
              
              }
class crm_lead(osv.osv):
    _inherit='crm.lead'
    _description='jjuice module'
    
    _columns={
              'account_type':fields.selection(ACCOUNT_TYPE,string="Type Of Account"),
              'primary_name':fields.char('Primary Contact Name & Title'),
              'primary_phone':fields.char('Primary Contact phone#'),
              'primary_email':fields.char('Primary Contact email'),
              '2nd_name':fields.char('(if) 2nd Point of Contact & Title'),
              '2nd_phone':fields.char('(if) 2nd Point of Contact Phone #'),
              '2nd_email':fields.char('(if) 2nd Point of Contact email'),
              'date_field':fields.date("Date We First Met"),
              'how_met':fields.text('How We Met'),
              'lead_type':fields.selection([('Hot Lead','Hot Lead'),('Warm Lead','Warm Lead'),('Still No Contact','Still No Contact'),('60-90 Days','60-90 Days'),('Not Interested','Not Interested')],string="Type of Lead"),
              'logs':fields.one2many("partner.lead",'lead2'),
              }
class update_product(osv.osv):
    _name='update.product'
    _description='product module'
    _columns={
              'product_name':fields.many2one('product.product','Product'),
              'product_id':fields.many2one('product.wizard','product_id'),
             # 'cost_price':fields.float('Cost Price'),
               'cost_price':fields.float(string="Cost Price"),
              }
    
    def update_product(self,cr,uid,ids,product_name,context=None):
        obj=self.pool.get('product.product').browse(cr,uid,product_name).standard_price
        res={}
        res['cost_price']=obj
        return {'value':res}
    
    def create(self,cr,uid,vals,context=None):
        obj=self.pool.get('product.product') 
        id=vals.get('product_name')
        price=vals.get('cost_price')
        obj.write(cr, uid, id, {'standard_price':price}, context)
        ids=super(update_product,self).create(cr,uid,vals,context)
        return ids     
