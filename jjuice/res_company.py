from openerp.osv import fields, osv
from openerp.tools.translate import _

class res_company(osv.osv):
    _inherit = "res.company"

    _columns = {
                'paid_image':fields.binary("Paid Stamp"),
                'ship_image':fields.binary("Free Shipping Stamp"),
                }