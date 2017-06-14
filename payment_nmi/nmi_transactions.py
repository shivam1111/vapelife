from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from helper import get_vault_detail
from datetime import datetime

class nmi_transactions(models.Model):
    _name = 'nmi.transactions'
    _order = "created_time desc"
#     @api.multi
#     def get_billing_ids(self):
#         assert len(self) == 1
#         params = self.env['ir.config_parameter']
#         username =  params.get_param('nmi_username',default="username")
#         pwd = params.get_param('nmi_password',default="password")
#         get_billing_ids(username,pwd,self.partner_id.nmi_vault_id or 'no_vault_id')
        
    @api.model
    def create(self,vals):
        sequence = self.env['ir.sequence'].get('NMI') or '/'
        vals['name'] = sequence
        return super(nmi_transactions,self).create(vals)    
    
    name = fields.Char("Serial Number")
    created_time =fields.Datetime('Create on',default = datetime.now())
    partner_id = fields.Many2one('res.partner',string = "Partner",required = True)
    amount = fields.Float('Amount')
    remarks = fields.Text("Response")
    invoice_id = fields.Many2one('account.invoice',string = "Invoice")
    vault_id = fields.Many2one('customer.vault','Vault')
    response_code = fields.Char("Response Code")
    transaction_id = fields.Char('Transaction ID')