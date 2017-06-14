from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class purchase_order(osv.osv):
    _inherit = "purchase.order"
    _description = "JJuice Purchase Order"

    _defaults = {
                 'authorized_by':lambda obj, cr, uid, context: uid,
                 }

    def _get_overheads_order(self,cr,uid,ids,context):
        result = {}
        for line in self.pool.get('purchase.overheads').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
            
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()


    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        account_tax_paid = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'jjuice_purchase', 'create_tax_paid_account')[1]
        overheads = self.pool.get('purchase.overheads')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
               val1 += line.price_subtotal
               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            tax_line_total = 0.00
            for tax_line in order.tax_line:
                tax_line_total += tax_line.amount
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']+tax_line_total
        return res

    
    STATE_SELECTION = [
        ('draft', 'Draft PO'),
        ('sent', 'Draft PO sent'),
        ('bid', 'Bid Received'),
        ('confirmed', 'Waiting Approval'),
        ('approved', 'Purchase Confirmed'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ]
    
    def add_invoice_overheads(self,cr,uid,order_id,invoice_ids,context):
        order = self.browse(cr,uid,order_id,context)
        line_obj = self.pool.get('account.invoice.tax')
        for invoice in invoice_ids:
            for tax_line in order.tax_line:
                line_obj.create(cr,uid,{
                                        'invoice_id':invoice,
                                        'name':tax_line.name,
                                        'account_id':tax_line.account_id.id,
                                        'amount':tax_line.amount
                                        },context)
        return True
    
    def view_invoice(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        context = dict(context or {})
        mod_obj = self.pool.get('ir.model.data')
        wizard_obj = self.pool.get('purchase.order.line_invoice')
        #compute the number of invoices to display
        inv_ids = []
        for po in self.browse(cr, uid, ids, context=context):
            if po.invoice_method == 'manual':
                if not po.invoice_ids:
                    context.update({'active_ids' :  [line.id for line in po.order_line]})
                    wizard_obj.makeInvoices(cr, uid, [], context=context)

        for po in self.browse(cr, uid, ids, context=context):
            inv_ids+= [invoice.id for invoice in po.invoice_ids]
            self.add_invoice_overheads(cr, uid, po.id, inv_ids, context)
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
        res_id = res and res[1] or False

        return {
            'name': _('Supplier Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'in_invoice', 'journal_type': 'purchase'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': inv_ids and inv_ids[0] or False,
        }
    
    def calculate_total_tax_amount(self,tax_rate,amount_untaxed):
        total_tax = float(tax_rate*amount_untaxed)/float(100)
        return total_tax
    
    def calculate_tax_percentage(self,tax_amount,amount_untaxed):
        # THis method returns the tax amount as a percentage of amount_untaxed
        try:
            tax_rate = float(100 * tax_amount)/float(amount_untaxed)
            return tax_rate
        except ZeroDivisionError:
            return 0 
    
    def _compute_tax_account(self, cr, uid, ids, field_name, arg, context=None):
        # This method computes the custom tax added to purchase order
        result = {}
        for order in self.browse(cr,uid,ids,context):
            total_tax = self.calculate_total_tax_amount(order.tax_rate, order.amount_untaxed) 
            result.update({order.id:total_tax})
        return result
    
    
    def onchange_tax_amount_entry(self,cr,uid,ids,tax_amount,amount_untaxed,tax_rate,shipping_total,context=None):
        # When the tax % changes or the amount changes we come to know through the context passed through the xml
        #  This helps tracking the onchange in both fields at one time
        res = {}
        r = []
        if context.get("tax_rate",False) or (context.get('_compute_tax_account',False) and tax_rate > 0):
            total_tax = self.calculate_total_tax_amount(tax_rate, amount_untaxed)
            res.update({'tax_amount_entry':total_tax})
        elif context.get("tax_amount_entry",False) or (context.get('_compute_tax_account',False) and tax_amount > 0):
            tax_percentage = self.calculate_tax_percentage(tax_amount, amount_untaxed)
            res.update({'tax_rate':tax_percentage})
        account_shipping = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'jjuice_purchase', 'create_shipping_account')[1]
        account_tax_paid = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'jjuice_purchase', 'create_tax_paid_account')[1]    
        if account_shipping:
            r.append({
                      'account_id':account_shipping,
                      'name':"Shipping Charges",
                      'amount':shipping_total
                      })
        if account_tax_paid:
            r.append({
                      'account_id':account_tax_paid,
                      'name':"Tax Paid",
                      'amount':res.get('tax_amount_entry',False) or tax_amount or 0 
                      })
        res.update({'tax_line':r})
        return {'value':res}

    
    _columns = {
                'requested_by':fields.many2one('hr.employee',"Requested By"),
                'authorized_by':fields.many2one('res.users',"Authorized By"),
                'card_purchase':fields.many2one('card.purchase',"Card used for purchase"),
                'state': fields.selection(STATE_SELECTION, 'Status', readonly=True,
                          help="The status of the purchase order or the quotation request. "
                               "A request for quotation is a purchase order in a 'Draft' status. "
                               "Then the order has to be confirmed by the user, the status switch "
                               "to 'Confirmed'. Then the supplier must confirm the order to change "
                               "the status to 'Approved'. When the purchase order is paid and "
                               "received, the status becomes 'Done'. If a cancel action occurs in "
                               "the invoice or in the receipt of goods, the status becomes "
                               "in exception.",
                          select=True, copy=False),

                'shipping_total':fields.float('Shipping Total'),
                'shipping_rate':fields.float('Shipping %'),
                'tax_line':fields.one2many('purchase.overheads','order_id','Miscellaneous'),
                'tax_rate':fields.float('Tax Rate %'),
                'tax_amount_entry':fields.float('Tax Amount',help="This is for manual entry for tax amount"),
                'tax_total':fields.function(_compute_tax_account,string="Total Tax",type="float"),
                'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
                    store={
                        'purchase.order.line': (_get_order, None, 10),
                    }, multi="sums", help="The amount without tax", track_visibility='always'),
                'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
                    store={
                        'purchase.order.line': (_get_order, None, 10),
                    }, multi="sums", help="The tax amount"),
                'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                    store={
                        'purchase.overheads':(_get_overheads_order,None,10),
                        'purchase.order.line': (_get_order, None, 10),
                    }, multi="sums", help="The total amount"),
                
                }
    
class purchase_overheads(osv.osv):
    _name = "purchase.overheads"
    _description = "Purchase Overheads"
    
    def onchange_amount(self,cr,uid,ids,amount=0,context=None):
        return {
                'value':{
                         'tax_total':500
                         }
                }    

    _columns = {
                'order_id':fields.many2one('purchase.order',"Purchase Order"),
                'account_id':fields.many2one('account.account','Overhead'),
                'name':fields.char("Description"),
                'amount':fields.float('Amount')
                }

class card_purchase(osv.osv):
    _name = "card.purchase"
    _description = "Card used for purchase"

    def name_get(self, cr, uid, ids, context=None):
        result = []
        for id in self.browse(cr,uid,ids,context):
            if id.number:
                result.append((id.id,id.name+' ('+id.number+')'))
            else:
                result.append((id.id,id.name))
        return result
    
    _columns = {
                'name':fields.char('Name',required=True),
                'number':fields.char("Card Number")
                }    