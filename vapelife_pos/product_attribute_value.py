from openerp import models, fields, api, _


class product_attribute_value(models.Model):
    _inherit="product.attribute.value"
    _description = "Product Attribute Value"

    actual_value = fields.Float("Actual Value")