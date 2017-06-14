from openerp import models, fields, api, _
from openerp.exceptions import except_orm

_RATING = [
        ('1','Very Bad'),
        ('2','Bad'),
        ('3', 'Normal'),
        ('4', 'Good'),
        ('5','Very Good')
    ] 


class flavor_reviews(models.Model):
    _name = "flavor.reviews"
    _description="Flavor Reviews"
    
    
    name = fields.Char('Name')
    email = fields.Char('Email ID')
    title = fields.Char('Title')
    description = fields.Text('Description')
    flavor_id = fields.Many2one('product.flavors',string = "Flavor")
    partner_id = fields.Many2one('res.partner','Customer')
    rating = fields.Selection(_RATING,string = "Rating")
    