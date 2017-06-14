from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

class fedex_account(models.Model):
    _name = "fedex.account"
    _description = "Fedex Account Information"
    
    _sql_constraints = [
        ('sequence_uniq', 'unique(sequence)',
            'Sequence for all the fedex account must be unique!'),
    ]
    
    
    @api.model
    def create(self,vals):
        sequence = self.env['ir.sequence'].get('FEDEX') or '/'
        vals['sequence_name'] = sequence
        return super(fedex_account,self).create(vals)
    
    @api.model
    def get_fedex_account(self):
        res = {}
        self._cr.execute('''
            SELECT 
            name,
            key,
            password,
            account_number,
            meter_number,
            freight_account_number,
            user_test_server,
            id
            FROM fedex_account where sequence = (SELECT MIN(sequence) FROM fedex_account) LIMIT 1
        ''')
        info = self._cr.fetchone()
        if info:
            res.update({
                        'name':info[0],
                        'key':info[1],
                        'password':info[2],
                        'account_number':info[3],
                        'meter_number':info[4],
                        'freight_account_number':info[5],
                        'use_test_server':info[6],
                        'id':info[7]
                        })
        return res 
    
    @api.multi
    @api.constrains('is_primary')
    def _check_multi_primary_production_account(self):
        self._cr.execute('''
            select count(id) from fedex_account where is_primary = true
        ''')
        count = self._cr.fetchone() #(x,)
        if count[0] > 1:
            raise ValidationError("There can be only one primary production account")
        
    name = fields.Char('Fedex Account Name',required = True)
    sequence = fields.Integer('Sequence',required = True)
    sequence_name = fields.Char('')
    key = fields.Char('Key')
    password = fields.Char('Password')
    account_number = fields.Char('Account Number')
    freight_account_number = fields.Char('Freight Account Number',default = False)
    user_test_server = fields.Boolean('Use Test Sever')
    meter_number = fields.Char('Meter Number')
    is_primary = fields.Boolean('Primary Productionn Account',default=False)
    
