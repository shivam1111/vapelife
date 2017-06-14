from openerp import models, fields, api,_
import openerp.addons.decimal_precision as dp

class product_flavours(models.Model):
    _name = "product.flavors"
    _description = "Product Flavours"
    
    name = fields.Char('Name')