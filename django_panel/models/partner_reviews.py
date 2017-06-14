from openerp import models, fields, api, _

class partner_reviews(models.Model):
    _name = "partner.reviews"
    _description = "Partner Reviews"
    
    partner_id = fields.Many2one('res.partner','Partner')
    review = fields.Text('Review')
    sequence = fields.Integer('Sequence')
    
    