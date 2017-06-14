from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

class res_partner(models.Model):
    _inherit = "res.partner"
    
    acquisition_id = fields.Many2one('account.acquisition','How JJuice Acquired the Account')