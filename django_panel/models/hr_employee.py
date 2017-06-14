from openerp import models, fields, api, _

class hr_employee(models.Model):
    _inherit = "hr.employee"
    
    publish = fields.Boolean(string="Publish")
    sequence = fields.Integer("Sequence")