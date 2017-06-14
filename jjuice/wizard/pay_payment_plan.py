from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

class pay_payment_plan_line(models.TransientModel):
    _name = 'pay.payment.line'
    _description = 'Pay Payment Plan'

    def pay_payment(self,cr,uid,ids,context):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'jjuice', 'view_vendor_receipt_dialog_form_jjuice')
        line_id  =self.browse(cr,uid,ids[0],context)
        inv = self.pool.get('account.invoice').browse(cr, uid, line_id.invoice_id.id, context=context)
        
        # The amount should not be greate than the balance of the invoice
        if line_id.amount > line_id.balance:
            raise Warning(_('Error!'), _("The amount paid should not exceed the balance of the invoice"))
         
        return {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                'default_amount': line_id.amount,
                'default_reference': inv.name,
                'close_after_process': True,
                'invoice_type': inv.type,
                'default_journal_id':line_id.wizard_id.method.id,
                'invoice_id': inv.id,
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
            }
        }

    invoice_id = fields.Many2one('account.invoice','Invoice')
    amount = fields.Float('Amount')
    balance = fields.Float(related = 'invoice_id.residual',string = "Balance")
    wizard_id = fields.Many2one('pay.payment.plan',invisible = True)
    state = fields.Selection([('unpaid','Unpaid'),('paid','Paid')],string = "Status",default = "unpaid")
    
class pay_payment_plan(models.TransientModel):
    _name = 'pay.payment.plan'
    _description = 'Pay Payment Plan'

    @api.one
    def pay_payment(self):
        total  = 0.00
        #checking whether the entered amount exceed the amount to be paid
        for i in self.invoice_id:
            if i.state == 'paid':
                total = total + i.amount
        return {'type': 'ir.actions.act_window_close'}
    
    method = fields.Many2one('account.journal',"Method of Payment")
    invoice_id = fields.One2many('pay.payment.line','wizard_id',string = 'Invoices')
    amount = fields.Float('Amount to be adjusted') 
    plan_id  = fields.Many2one('payment.plan')   