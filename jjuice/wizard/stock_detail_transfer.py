from openerp import models, fields, api
from openerp.tools.translate import _

class stock_transfer_details(models.TransientModel):
    _inherit = "stock.transfer_details"
   
    number = fields.Char('Shipment Tracking Number')
    parcel_id = fields.Many2one('name.parcel','Parcel Services')

    @api.multi
    def do_detailed_transfer(self):
        super(stock_transfer_details,self).do_detailed_transfer()
        view = self.env.ref('mail.email_compose_message_wizard_form')
        if self.picking_id.partner_id:
            self.picking_id.shipment_number = self.number
            if self.picking_id and self.number:
                object_id = self.pool.get('mail.compose.message').create(self._cr,self._uid,{
                                                                          'composition_mode':'comment',
                                                                          'model':'stock.picking',
                                                                          'res_id':self.picking_id.id,
                                                                          'is_log':False,
                                                                          'subject':"JJuice Shipment No.",
                                                                          'partner_ids':[(6, 0, [self.picking_id.partner_id.id])],
                                                                          'body':'Dear %s <br/>Your %sShipment Tracking Number for JJuice Shipment is : %s' %(self.picking_id.partner_id.name ,self.parcel_id and self.parcel_id.name+" " or '',self.number)
                                                                          },self._context)
                
                return {
                    'name': _('Shipment Number'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': object_id,
                    'context': self.env.context,                
                }

class name_parcel(models.Model):
    _name = "name.parcel"
    
    name = fields.Char('Parcel Services')