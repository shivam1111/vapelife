from openerp import models, fields, api
from openerp.tools.translate import _

class stock_transfer_details(models.TransientModel):
    _inherit = "stock.transfer_details"
    
    @api.multi
    @api.model
    def do_detailed_transfer(self):
        res = super(stock_transfer_details,self).do_detailed_transfer()
        if res and res.get('res_id',False):
            mail_object = self.env['mail.compose.message']
            mail = mail_object.search([('id','=',res.get('res_id',False))])
            msg = 'Dear %s <br/>Your %sShipment Tracking Number for JJuice Shipment is : %s' %(self.picking_id.partner_id.name ,self.parcel_id and self.parcel_id.name+" " or '',self.number)
            msg = msg + "<br/>You can track your package by clicking on the <a href='http://www.fedex.com/Tracking?action=track&tracknumbers=%s'>Link</a>"%(self.number)
            mail.body = msg
            return res