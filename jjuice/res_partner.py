from openerp.osv import fields, osv 
from openerp.tools.translate import _

class volume_price(osv.osv):
    _name = "volume.prices.line"
    _columns = {
                'customer_id':fields.many2one('res.partner','Customer',invisible=True),
                'product_attribute':fields.many2one('product.attribute.value',"Volume",required=True),
                'price':fields.float("Price"),
                }
    
class res_partner_order(osv.osv):
    _inherit="res.partner"
    _description="jjuice"
    
    
    def _default_set_lead(self,cr,uid,context):
        if context.get('search_default_leads',False):
            return True
        return False
    
    def _default_set_customer(self,cr,uid,context):
        if not context.get('search_default_leads',False):
            return True
        return False
    
    _defaults = {
                 'user_id':lambda self,cr,uid,context: uid,
                 'leads':_default_set_lead,
                 'customer':_default_set_customer
                 }
    
    def _check_customer_type(self, cr, uid, ids, context=None):
        for partner in self.browse(cr,uid,ids,context):
            if partner.customer and partner.leads:
                return False
        return True
                
    _constraints = [
        (_check_customer_type, 'Error: A Partner cannot be lead and a customer at the same time', ['customer','leads']),
        ]   

    def set_price(self,cr,uid,id,context=None):
        result = {}
        customer = self.pool.get('res.partner').browse(cr,uid,id,context)
        for i in customer.volume_prices:
            result.update({i.product_attribute.id:i.price})
        return result
    
    def call_view_jjuice(self,cr,uid,ids,context):
        return {
                'type':'ir.actions.client',
                'tag':'graph.action',
                'context':context,
                }
    
    def _draft_order_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,0), ids))
        # The current user may not have access rights for sale orders
        try:
            for partner in self.browse(cr, uid, ids, context):
                count = 0
                # First make total list of sale orders to look for quotations
                list_order = partner.sale_order_ids + partner.mapped('child_ids.sale_order_ids')
                for i in list_order:
                    if i.state == "draft":
                        count = count + 1
                res[partner.id] = count
        except:
            pass
        return res
    
    _columns={
              "leads":fields.boolean("Lead"),
              "website_customer":fields.boolean("Website Guest Customer"),
              "order":fields.one2many("res.partner.order","partners"),
              'volume_prices':fields.one2many('volume.prices.line','customer_id',"Prices"),             
              'email_multi_to':fields.one2many('multi.email','partner_id',"Addition Email IDs"),
              'multi_address':fields.one2many('res.partner', 'parent_id', 'Contacts', domain=[('active','=',True),('type','in',['invoice','delivery'])]),
              'draft_order_count': fields.function(_draft_order_count, string='# of Sales Order', type='integer'),
              }

class multi_email(osv.osv):
    _name = "multi.email"
    _columns = {
                'email':fields.char('Email'),
                'partner_id':fields.many2one('res.partner','Partner')
                }
    
class res_partner_orders(osv.osv):
        _name="res.partner.order"
        _description="partner module"
        _columns={
                    "partners":fields.many2one("res.partner","partner"),
                    "name":fields.char("Name"),
                    "order_date":fields.date("Order Date"),
                    "ref":fields.char("Ref"),
                    "res_partner":fields.many2one("res.partner","Customer"),
                    
                    #"product":fields.many2one("product.product","Product"),
                    "10_ml":fields.one2many("res.partner.ml","product_id","10 Ml"),
                    "350_ml":fields.one2many("res.partner.ml","product_id","350 Ml"),
                  }
        
class res_partner_ml(osv.osv):
    _name="res.partner.ml"
    _description="jjuice"
    _columns={
              "product_id":fields.many2one("product.product","Product"),
              "quantity":fields.float("Quantity"),
              "unit_price":fields.float("Unit Price"),
              "sub_total":fields.float("Sub Total"),
              }     
    
