from openerp import models, fields, api, _

class res_partner(models.Model):
    _inherit = "res.partner"
    is_residential = fields.Boolean('FedEx Residential Address',help = "Is this address a residential address.Used in Shipping Services like FedEx")
    fedex_account_id = fields.Many2one('fedex.account','FedEx Account')