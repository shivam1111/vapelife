from openerp import models, fields, api, _

class website_contactus(models.Model):
    _name = "website.contactus"
    _description = "Contact Us Form "
    _inherit = ['mail.thread','ir.needaction_mixin']
    

    name = fields.Char('Name')
    email = fields.Char("Email")
    website = fields.Char("Website")
    message = fields.Text("Comment")