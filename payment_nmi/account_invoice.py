from openerp import models, fields, api, _

class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    @api.multi
    def pay_by_nmi(self):
        assert len(self) == 1
        view_id  = self.env.ref('payment_nmi.nmi_payment_wizard_form')
        return {
            'name':_("Pay by NMI"),
            'view_mode': 'form',
            'view_id': view_id.id,
            'view_type': 'form',
            'res_model': 'nmi.payment.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_invoice_id': self.id,
            }
        }                    
    
    nmi_transaction_ids = fields.One2many('nmi.transactions','invoice_id')