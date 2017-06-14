from openerp import models, fields, api, _
from pyPdf import PdfFileWriter, PdfFileReader
from datetime import date

class sale_order(models.Model):
    _inherit = "sale.order"
    
    @api.one
    def get_invoice_report(self):
        output = PdfFileWriter()  
        report_obj = self.env['report']
        pdf = report_obj.get_pdf(self, 'django_panel.report_qweb_order_website_report', data={})
        output_base64 = pdf.encode("base64"),
        return output_base64  
    
    
    @api.model
    def create_sale_order_from_cart(self,vals):
#         {'origin': '3057132f9b644f23892a0e84f7e1e0f8', 
#             'note': 'Order Notes', 
#             'order_line': [[0, 0, {'price_unit': 30.0, 'product_uom_qty': 1, 'product_id': 1503}]], 
#                 'partner_id': 3, 
#             'shipping_cost': 10.36
#         }
        order_line = vals.get('order_line',[])
        order = False
        if len(order_line) > 0:
            medium_id = self.env.ref('django_panel.django_website_sale_order_source')
            if vals.get('shipping_cost',0.00) > 0:
                shipping_product = self.env['product.product'].search([('shipping','=',True)],limit=1)
                if len(shipping_product) > 0:
                    order_line.append([0,0,{
                        'product_id':shipping_product.id,
                        'product_uom_qty':1,
                        'price_unit':vals.get('shipping_cost',0.00),
                    }])
            self.env['res.partner'].search([('id','=',vals.get('partner_id',False))])[0].notify_email = 'none'
            order = self.create({
                'partner_id':vals.get('partner_id',False),
                'origin':vals.get('origin',''),
                'note':vals.get('note',''),
                'order_line':vals.get('order_line',[]),
                'source_id':medium_id.id,
            })
            order.action_button_confirm();
            invoice_wizard = self.env['sale.advance.payment.inv'].with_context(active_ids=[order.id],open_invoices=True)
            wizard_id = invoice_wizard.create({'advance_payment_method':'all'})
            res = wizard_id.create_invoices()
            account_invoice = self.env['account.invoice'].search([('id','=',res.get('res_id',False))])
            account_invoice.signal_workflow('invoice_open')  
            journal_id = self.env['account.journal'].search([('is_nmi_journal','=',True)])
            account_voucher = self.env['account.voucher'].with_context(**{
                'invoice_open':True,
                'default_amount':account_invoice.amount_total,
                'payment_expected_currency': account_invoice.currency_id.id,
                'close_after_process': True,
                'invoice_type': account_invoice.type,
                'invoice_id': account_invoice.id,
                'type': account_invoice.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'active_ids':[account_invoice.id],
                'active_id':account_invoice.id,
                'journal_type': 'sale',
            })
            onchange_vals = account_voucher.onchange_journal(journal_id.id, [(6,0,[])], False,
                      self.env['res.partner']._find_accounting_partner(account_invoice.partner_id).id, 
                      date.today().strftime('%Y-%m-%d'), account_invoice.amount_total, 'receipt', account_invoice.company_id.id)
            vals = {
                'partner_id':self.env['res.partner']._find_accounting_partner(account_invoice.partner_id).id,
                'amount':account_invoice.amount_total,
                'reference':"%s | %s"%(vals.get('origin',''),account_invoice.name),
                'name':"%s | %s"%(vals.get('origin',''),account_invoice.name),
                'journal_id':journal_id.id,
                'type':account_invoice.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
            }
            onchange_vals = onchange_vals.get('value',{})
            onchange_vals.update(vals)
            def _wrap_tuple(list_dict):
                new_list = []
                for line in list_dict:
                    new_list.append((0,0,line))
                return new_list
                                
            if onchange_vals.get('line_cr_ids',False):
                onchange_vals['line_cr_ids'] = _wrap_tuple(onchange_vals.get('line_cr_ids',[]))
            if onchange_vals.get('line_dr_ids',False):
                onchange_vals['line_dr_ids'] = _wrap_tuple(onchange_vals.get('line_dr_ids',[]))
            av = account_voucher.create(onchange_vals)
            av.button_proforma_voucher()
            output = PdfFileWriter()  
            report_obj = self.env['report']
            pdf = report_obj.get_pdf(order, 'django_panel.report_qweb_order_website_report', data={})
            output_base64 = pdf.encode("base64")
            template = self.env.ref('account.email_template_edi_invoice', False)
            self.env['email.template'].browse(template.id).send_mail(account_invoice.id,force_send=False)
        return {
            'name':account_invoice and account_invoice.number or 'No Name',
            'order_id':order and order.id or False,
            'invoice_id':account_invoice and account_invoice.id or False,
            'pdf':output_base64,
        }