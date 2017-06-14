from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class stock_move(osv.osv):
    _inherit = "stock.move"
    _description = "Add Supplier Field"
    
    def _compute_supplier(self,cr,uid,ids,field_name,arg,context):
        result = {}
        for move in self.browse(cr,uid,ids,context):
            if move.purchase_line_id:
                result.update({move.id:move.purchase_line_id.order_id.partner_id.id})
        return result
    
    _columns = {
#                 'supplier_id':fields.function(_compute_supplier,type="many2one",relation="res.partner",string = "Supplier")
                  'supplier_id':fields.related("purchase_line_id","order_id",'partner_id',type="many2one",relation="res.partner",string="Supplier",store=True),  
                }
    
