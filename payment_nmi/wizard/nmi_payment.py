from openerp import models, fields, api, _
from ..helper import get_vault_detail,make_payment
import urlparse
import xml.etree.ElementTree as ET
from openerp.exceptions import except_orm

class nmi_payment_wizard(models.TransientModel):
    _name = 'nmi.payment.wizard'
    
    @api.multi
    def make_payment(self):
        assert len(self) == 1
        if self.invoice_id and self.diff_balance < 0:
            # This means you are charging more than the invoice balance
            raise except_orm('Error!',"Sorry the payment amount is greater than the invoice balance!")
        
        if self.invoice_id and (self.invoice_id.partner_id != self.partner_id):
            raise except_orm('Error!',"The selected partner and invoice partner mismatch!") 
        
        params = self.env['ir.config_parameter'].sudo()
        username =  params.get_param('nmi_username',default="username")
        pwd = params.get_param('nmi_password',default="password")
        nmi_transaction = self.env['nmi.transactions']
        payment_made = 0.00
        payment_ref = ""
        transaction_ids = []
        remarks = [] 
        for j in self.line_ids:
            if j.active and j.amount > 0:
                data = make_payment(username,pwd,j.vault_id.customer_vault_id,j.amount,self.invoice_id.name or False)
                temp = urlparse.parse_qs(data)
                nmi_transaction.create({
                    'partner_id':self.partner_id.id,
                    'remarks':temp.get('responsetext') and temp.get('responsetext')[0] or '',
                    'vault_id':j.vault_id.id,
                    'invoice_id':self.invoice_id.id,
                    'response_code':temp.get('response_code') and temp.get('response_code')[0] or '',
                    'transaction_id':temp.get('transactionid') and temp.get('transactionid')[0] or '',
                    'amount':j.amount
                })
                remarks.append(temp.get('responsetext') and temp.get('responsetext')[0] or '-')
                if temp.get('response_code')[0] == '100' and temp.get('transactionid'):
                    # This means transaction was successsfull
                    payment_made = payment_made + j.amount
                    transaction_ids.append(temp.get('transactionid')[0])
                    if j.cc_number:
                        payment_ref = payment_ref + j.cc_number+" - ($%s),"%(j.amount)
                    else:
                        details = get_vault_detail(username,pwd,j.vault_id.customer_vault_id)
                        root = ET.fromstring(details)
#                         try:
                        ccnumber  = root.find('customer_vault').find('customer').find('cc_number').text
                        j.cc_number = ccnumber
                        payment_ref = payment_ref + j.cc_number+" - ($%s),"%(j.amount)
#                         except Exception as e:
#                             pass
        if self.invoice_id and self.register_payment and (self.invoice_id.partner_id == self.partner_id):
            view_id = self.env.ref('account_voucher.view_vendor_receipt_dialog_form')
            inv = self.invoice_id
            set_context = {
                    'active_ids':[inv.id],
                    'payment_expected_currency': inv.currency_id.id,
                    'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                    'default_amount': inv.type in ('out_refund', 'in_refund') and -payment_made or payment_made,
                    'default_reference': payment_ref,
                    'close_after_process': True,
                    'invoice_type': inv.type,
                    'invoice_id': inv.id,
                    'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                    'default_name':",".join(transaction_ids),
            }
            journal = self.env['account.journal'].search([('is_nmi_journal','=',True)],limit=1)

            if len(journal) > 0:
                set_context.update({'default_journal_id':journal[0].id})
            
            return {
                'name':remarks and _(" | ".join(["Pay Invoice | Transaction Status -: "]+remarks)) or _("Pay Invoice"),
                'view_mode': 'form',
                'view_id': view_id.id,
                'view_type': 'form',
                'res_model': 'account.voucher',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context':set_context,
            }            
                    
    
    @api.multi
    def get_vault_details(self):
        assert len(self) == 1
        params = self.env['ir.config_parameter'].sudo()
        username =  params.get_param('nmi_username',default="username")
        pwd = params.get_param('nmi_password',default="password")   
        for j in self.line_ids:
            details = get_vault_detail(username,pwd,j.vault_id.customer_vault_id)
            root = ET.fromstring(details)
            try:
                ccnumber  = root.find('customer_vault').find('customer').find('cc_number').text
                ccexp = root.find('customer_vault').find('customer').find('cc_exp').text
                j.cc_number = ccnumber
                j.cc_exp = ccexp
            except Exception as e:
                pass
        view  = self.env.ref('payment_nmi.nmi_payment_wizard_form')
        return {
            'name':_("Make Payment"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'nmi.payment.wizard',
            'target': 'new',
            'res_id': self.id,
            'views': [(view.id, 'form')],
            'view_id': view.id,            
            'context': self.env.context,                
        }                        
            
    @api.depends('invoice_id')
    def _compute_balance(self):
        self.invoice_balance = self.invoice_id.residual
    
    @api.depends('invoice_id','line_ids','line_ids.active')
    def _compute_diff_balance(self):
        total = 0.00
        for j in self.line_ids:
            if j.active:
                total = total + j.amount
        self.diff_balance = self.invoice_id.residual - total
        
    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        self.partner_id = self.invoice_id.partner_id
        self.register_payment = True
    
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.line_ids = map(lambda x:(0,0,{'vault_id':x.id,'active':True}),self.partner_id.customer_vault_ids)
        
    partner_id = fields.Many2one('res.partner',string = "Partner",required=True)
    invoice_id = fields.Many2one('account.invoice',string = "Invoice")
    register_payment = fields.Boolean("Register Payment in Invoice")
    line_ids = fields.One2many('nmi.payment.wizard.line','wizard_id')
    invoice_balance = fields.Float(compute='_compute_balance',string = "Invoice Balance Amount")
    diff_balance = fields.Float(compute = "_compute_diff_balance",string = "Balance")

class nmi_payment_wizard_line(models.TransientModel):
    _name = 'nmi.payment.wizard.line'    

    wizard_id = fields.Many2one('nmi.payment.wizard')
    vault_id = fields.Many2one('customer.vault',string = "Vault")
    cc_number = fields.Char('CC No')
    cc_exp = fields.Char('CC Exp.')
    amount = fields.Float('Amount')
    active = fields.Boolean('Active')