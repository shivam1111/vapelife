from openerp import models, fields, api, _
from openerp.exceptions import except_orm

class account_move_line(models.Model):
    _inherit = "account.move.line"
    _description = "Account Commission Line"

    @api.one
    @api.depends(
        'debit',
        'credit',
        'type_account',
        'partner_id',
    )
    def _calculate_commission(self):
        commission = 0.00
        diff = self.debit - self.credit
        if diff > 0:
            if self.type_account in ['retailer','website']:
                self.commission = 0.2 * diff
            else:
                self.commission = 0.1 * diff
        else:
            self.commission = 0
    
    type_account = fields.Selection(related='partner_id.classify_finance',type="selection",string='Type of A/C')
    commission = fields.Float('Commission',help = "Commission is calculated as x% of difference between\
                                                         total debit - total credit in the columns",compute="_calculate_commission")

class account_commissions(models.TransientModel):
    _name = "account.commissions"
    _description = "Commissions Calculator"

    @api.multi
    def generate_archive(self):
        archive = self.env['account.commissions.archive'].create({
                'user':self.user.id,
                'from_date':self.from_date,
                'to_date':self.to_date,
            })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.commissions.archive',
            'target': 'current',
            'res_id':archive.id,
        }
            
    @api.one
    @api.depends(
        'user',
        'from_date',
        'to_date',
    )
    def _compute_payments(self):
        payment_ids = []
        if self.user and self.from_date and self.to_date:
            self._cr.execute("""
                select
                    l.id
                from
                    account_move_line l
                    left join account_account a on (l.account_id = a.id)
                    left join account_move am on (am.id=l.move_id)
                    left join account_invoice as inv on (inv.move_id = am.id)
                    left join res_partner partner on (l.partner_id = partner.id)
                    left join res_users as us on (us.id = partner.user_id) 
                where l.state != 'draft'
                  and a.type = 'liquidity'
                  and l.date >= '%s'
                  and l.date <='%s'
                  and us.id = %s
            """%(self.from_date,self.to_date,self.user.id))
            res = self._cr.fetchall()
            if len(res) > 0:
                payment_ids = map(lambda x:x[0],res)
        self.payment_ids = payment_ids
    
    user= fields.Many2one('res.users',string = "Sales Person",required=True)
    from_date = fields.Date('From',required=True)
    to_date = fields.Date('To',required=True)
    payment_ids = fields.Many2many('account.move.line', string='Payments',
        compute='_compute_payments') 

