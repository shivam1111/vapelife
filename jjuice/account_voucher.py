from openerp.osv import fields, osv
from openerp.tools.translate import _

class account_voucher(osv.osv):
    _inherit = "account.voucher"
    _description  = "Account Voucher JJuice"
    _defaults = {
                 'verified':'no',
                 }
    _columns = {
                'verified':fields.selection([('no',"Unverified"),
                                             ('yes',"Verified")],string = "Verification status")
                }
    
    def button_proforma_voucher(self,cr,uid,ids,context=None):
        if context is None:
            context={}
        invoice_obj=self.pool.get('account.invoice')
        ids_invoice=context.get('active_ids',[])
        super(account_voucher,self).button_proforma_voucher(cr,uid,ids,context)
        return invoice_obj.action_invoice_sent(cr,uid,ids_invoice,context)    
    
    def change_verification_status_no(self,cr,uid,ids,context):
        for i in ids:
            self.write(cr,uid,i,{'verified':"no"},context)
        return True

    def change_verification_status_yes(self,cr,uid,ids,context):
        for i in ids:
            self.write(cr,uid,i,{'verified':"yes"},context)
        return True
        
    
    def button_proforma_voucher_jjuice(self, cr, uid, ids, context=None):
        amount = 0.00
        if context.get('refresh_tree_view',False):
            self.signal_workflow(cr, uid, ids, 'proforma_voucher')
            return {'type': 'ir.actions.act_window_close'}
        
        if context.get('invoice_open',False):
            view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')[1]
            plan = self.pool.get('payment.plan').write(cr,uid,context.get('plan_id',False),{'amount':0,'state':'paid'},context)
            self.signal_workflow(cr, uid, ids, 'proforma_voucher')
            return {
            'view_mode': 'form',
            'res_id':context.get('invoice_id',False),
            'view_type': 'form',
            'view_id':view_id,
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
                    }
        plan = self.pool.get('payment.plan')
        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'jjuice', 'pay_payment_plan_form')[1]
        self.signal_workflow(cr, uid, ids, 'proforma_voucher')
        obj_line = self.pool.get('pay.payment.line')
        line_obj = obj_line.browse(cr,uid,context.get('active_id',False),context)
        wizard_id =line_obj.wizard_id.id
        wizard_amount = line_obj.wizard_id.amount
        obj_line.write(cr,uid,context.get('active_id',False),{'state':'paid'},context)
        if ((wizard_amount - line_obj.amount) <= 0 ):
            plan.write(cr,uid,line_obj.wizard_id.plan_id.id,{'amount':wizard_amount - line_obj.amount,'state':'paid'},context)
        else:
            plan.write(cr,uid,line_obj.wizard_id.plan_id.id,{'amount':wizard_amount - line_obj.amount},context)
        wizard_obj = self.pool.get('pay.payment.plan').write(cr,uid,wizard_id,{'amount':wizard_amount - line_obj.amount},context)
        
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
            'context':{'wizard_id':wizard_id}
        }    