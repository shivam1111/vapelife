from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    
    def action_invoice_sent(self,cr,uid,ids,context=None):
        context={}
        return super(account_invoice,self).action_invoice_sent(cr,uid,ids,context)

    def open_invoice(self,cr,uid,id,context):
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')
        return {
            'view_mode': 'form',
            'view_id': view_id,
            'res_id':id[0],
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
        }    
        
    def adjust_balance(self,cr,uid,ids,context):
        assert len(ids) == 1;
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')
        inv = self.browse(cr, uid, ids[0], context=context)
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
                'refresh_tree_view':True,
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                'default_reference': inv.name,
                'close_after_process': True,
                'invoice_type': inv.type,
                'invoice_id': inv.id,
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
            }
        }
        
    
    @api.depends('amount_total','residual')
    def _compute_payments_paid(self):
        for record in self:
              if record.id and record.state in ['open','paid']:
                record.paid_balance = record.amount_total - record.residual

    @api.one
    @api.depends('invoice_line','invoice_line.product_id')    
    def _check_shipping_free(self):
        res = {}
        self._cr.execute('''
                select id from product_product where shipping = true limit 1
            ''')
        product = self._cr.fetchone()
        product_id = product and product[0] or False
        for line in self.invoice_line:
            if line.product_id.id == product_id:
                if line.quantity >= 0:
                    self.free_shipping_check=True
                    break

    
    @api.one
    @api.depends('name',)
    def _compute_payments_jjuice(self):
        for record in self:
              list_plan = []
              if record.id:
                  self._cr.execute('''
                  select order_id from sale_order_invoice_rel where invoice_id = %s 
                  ''' %(record.id))
                  order_id = self._cr.fetchall()
                  for i in order_id:
                      sale_order = self.env['sale.order'].search([('id','=',i[0])])
                      list_plan = list_plan + map(lambda x:x.id , sale_order.payment_plan_ids)
                  list_invoice_plan = self.env['payment.plan'].search([('invoice_id','=',record.id)])
                  list_plan = list_plan + map(lambda x:x.id , list_invoice_plan)
                  record.payment_plan_ids = list_plan 
    @api.one
    @api.depends('partner_id')
    def _get_shipping_partner(self):
        if self.partner_id:
            addr = self.partner_id.address_get(['delivery'])
            delivery_partner = self.env['res.partner'].browse(addr.get('delivery'))
            self.shipping_partner_id = delivery_partner
        
    
    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        self.amount_before_discount_tax = sum(line.total_subtotal_before_discount for line in self.invoice_line) #without tax and discount
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
        self.amount_tax = sum(line.amount for line in self.tax_line)
        self.amount_total = self.amount_untaxed + self.amount_tax
        self.discount_jjuice = self.amount_before_discount_tax -  self.amount_untaxed
        
    discount_jjuice = fields.Float(string='Discount', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    
    amount_before_discount_tax = fields.Float(string='Amount Before Discount and Tax', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')

    account_state = fields.Selection([('uncollected','Uncollected A/C Receivables'),('toxic','Toxic Accounts')],
                                     default="uncollected"
                                     )    
    payment_plan_ids=fields.Many2many("payment.plan","payment_id","paymen_invoice_relation","invoice_id","Payment Plan Id",compute='_compute_payments_jjuice')
    paid_balance = fields.Float("Paid",compute='_compute_payments_paid',store=True)
    free_shipping_check=fields.Boolean("Free Shipping",compute = '_check_shipping_free')
    shipping_partner_id = fields.Many2one('res.partner', string='Shipping Entity',compute ='_get_shipping_partner',
        help="The commercial entity that will be used on Journal Entries for this invoice")
class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    _order = "invoice_id,sequence,id"

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id')
    def _compute_price(self):
        precision = self.pool.get('decimal.precision').precision_get(self._cr,self._uid,'Account')
        self.total_subtotal_before_discount = round(self.price_unit * self.quantity, precision)
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(price, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = taxes['total']
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)

            
    total_subtotal_before_discount = fields.Float(string='Amount Before Discount', digits= dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_price')

