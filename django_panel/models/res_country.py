from openerp import models, fields, api, _

class res_country(models.Model):
    _inherit = "res.country"
    
    is_shipping_allowed = fields.Boolean('Is Shipping Allowed')