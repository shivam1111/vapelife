from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

_SOURCE = [
           ('trade_show','Trade Show'),
           ('sales_trip','Sales Trip'),
           ('magazine_add','Magazine Add'),
           ('referral','Referral'),
           ('website','Website')
       ]

class account_acquisition(models.Model):
    _name = "account.acquisition"
    _description = "How JJuice acquired the account"
    
    @api.one
    def _compute_partner_ids(self):
        partner_ids = self.env['res.partner'].search([('acquisition_id','=',self.id)])
        self.partner_ids = partner_ids
    
    name = fields.Char('Source Name' ,required=True)
    source = fields.Selection(_SOURCE,'Source',required=True)
    partner_ids = fields.Many2many('res.partner',string="Partners Acquired",compute='_compute_partner_ids')