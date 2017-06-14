from openerp import models, fields, api, _
from datetime import date
from openerp.exceptions import except_orm, Warning, RedirectWarning

class payment_plan(models.Model):
    _name="payment.plan"
    _description="payment file for jjuice"

    def create(self,cr,uid,vals,context):
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'payment.plan') or '/'
        return super(payment_plan,self).create(cr,uid,vals,context)
        
    def _check_ids_empty(self,cr,uid,ids,context=None):
        for plan in self.read(cr, uid, ids, ['order_id', 'invoice_id'], context=context):
            if plan['order_id'] == plan['invoice_id']:
                return False 
        return True        
    
    def _check_ids(self, cr, uid, ids, context=None):
        for plan in self.read(cr, uid, ids, ['order_id', 'invoice_id'], context=context):
            if (plan.get('order_id',False) and plan.get('invoice_id',False)):
                return False
        return True

    _constraints = [
        (_check_ids, 'Error! Cannot have a Sale Order and Invoice attached to the same payment plan', ['order_id', 'invoice_id']),
        (_check_ids_empty, 'Error! It is required to attach a Sales Order or an Invoice to a payment plan', ['order_id', 'invoice_id'])
    ]
    
    def cal_payment(self, cr, uid, ids, context=None):
        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'jjuice', 'pay_payment_plan_form')[1]
        list_invoice = []
        obj = self.pool.get('pay.payment.line')
        obj_plan = self.browse(cr,uid,ids[0],context)
        if obj_plan.amount <= 0:
            raise Warning(_('Error!'), _('Cannot pay from a payment plan that has amount less than or equal to zero')) 
        for plan in obj_plan:
            if plan.order_id:
                for invoice in plan.order_id.invoice_ids:
                    list_invoice.append(invoice.id)
            elif plan.invoice_id:
                list_invoice.append(plan.invoice_id.id)
        wizard_object = self.pool.get('pay.payment.plan')
        wizard_id = wizard_object.create(cr,uid,{'plan_id':ids[0],'amount':obj_plan.amount,'method':obj_plan.method_of_payment.id},context)
        for i in list_invoice:
            obj.create(cr,uid,{'invoice_id':i,'amount':0,'wizard_id':wizard_id},context)
        return {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'res_id':wizard_id,
            'view_type': 'form',
            'res_model': 'pay.payment.plan',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context':{'payment_plan_ids':ids,'wizard_id':wizard_id}
        }
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        result = []
        if context.get('show_payments',False):
            for line in self.browse(cr, uid, ids, context=context):
                result.append((line.id, line.name + "|" + line.date + "|"+ line.method_of_payment.name + "|Actual "+ str(line.amount_original)+ "|Balance "+str(line.amount) + "|"+ line.state+"\n" ))
            return result            
        else:
            return super(payment_plan,self).name_get(cr,uid,ids,context)
        
    @api.multi
    @api.depends('name',)
    def _get_invoice(self):
        for record in self:
            if record.order_id:
                record.invoice_ids=record.order_id.invoice_ids
                
    
    name=fields.Char("Name",default = "/")
    date=fields.Date("Date",required = True,default = date.today().strftime('%Y-%m-%d'))
    method_of_payment=fields.Many2one("account.journal","Method Of Payment",required =True)
    partner_id=fields.Many2one(comodel_name = 'res.partner',string = "Partner")
    invoice_id = fields.Many2one('account.invoice',"Invoice")
    order_id=fields.Many2one("sale.order","Sale Order")
    amount_original = fields.Float("Original Plan Amount",readonly = True)
    amount=fields.Float("Amount to be adjusted")
    state=fields.Selection([('unpaid','Unpaid'),('paid','Paid')],default = 'unpaid')
    invoice_ids = fields.Many2many('account.invoice','plan_invoice_rel','plan_id','invoice_id',compute="_get_invoice")