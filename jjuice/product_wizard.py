from openerp.osv import osv, fields
from openerp.tools.translate import _

class product_wizard(osv.osv):
    _name="product.wizard"
    _description="first wizard module"
    _defaults={
              'date': fields.datetime.now,
              }
    
    
    _columns={
              'product_ref':fields.char('Reference'),
              'date':fields.datetime('Creation Date'),
              "product":fields.one2many("update.product",'product_id',string='product'),
             
             }
    
    