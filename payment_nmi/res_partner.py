from openerp import models, fields, api, _

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    nmi_vault_id = fields.Char('NMI Vault ID')
    customer_vault_ids = fields.One2many('customer.vault','partner_id','Customer Vaults')