from openerp import models, fields, api, _
from openerp.exceptions import except_orm

class account_commissions_archive(models.Model):
    _name = "account.commissions.archive"
    _description = "Commissions Calculator Archive"
    _rec_name = "user"

    @api.one
    @api.depends(
        'user',
        'from_date',
        'to_date',
    )
    
    @api.constrains(
        'user',
        'from_date',
        'to_date',        
    )
    def check_date_archive(self):
        # check that to date always greater than from date
        # check always that for a particular employee the archives to date always less than from date
        if self.to_date <= self.from_date:
            raise except_orm("Error!","Sorry! To date should always be greater than from date")
        ids = self.search([('user','=',self.user.id),('from_date','<=',self.to_date),
                           ('to_date','>=',self.from_date),('id','!=',self.id)])
        if ids:
            raise except_orm("Error!","Sorry! Commissions dates overlapping for this Sales Person")

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
    
    
    
    