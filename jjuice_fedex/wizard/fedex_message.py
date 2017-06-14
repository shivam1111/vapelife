from openerp import models, fields, api, _

class fedex_message(models.TransientModel):
    _name = "fedex.message"
    _description = "Fedex Message Display"
    
    name = fields.Text('Message')