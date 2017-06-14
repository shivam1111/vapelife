from openerp import models, fields, api, _

class stock_picking(models.Model):
    _inherit = "stock.picking"
    
    @api.multi
    def tranfer_fedex(self):
        self = self.with_context(override=True) # THis is to override python constraints while creating shipment. 
        shipment_obj = self.env['create.shipment.fedex']
        res = self.env['fedex.account'].get_fedex_account()
        primary_product_account = self.env['fedex.account'].search([('is_primary','=',True)])
        final_account_id = self.partner_id.fedex_account_id and self.partner_id.fedex_account_id.id or primary_product_account.id or res.get('id',False)
        shipment = shipment_obj.create({
                                        'recipient_id':self.partner_id.id,
                                        'to_person_name':self.partner_id.name,
                                        'to_company_name':self.partner_id.is_company and self.partner_id.name or self.partner_id.parent_id.name,
                                        'to_phone_number':self.partner_id.phone,
                                        'to_street1':self.partner_id.street or "Empty Street",
                                        'account_id':final_account_id,
                                        'picking_id':self.id
                                        })
        shipment.onchange_recipient_id()
        compose_form = self.env.ref('jjuice_fedex.create_shipment_form', False)
        return {
            'name': _('Create Shipment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'res_model': 'create.shipment.fedex',
            'target': 'current',
            'res_id':shipment.id,
            'context':self._context
           }                    
        
    fedex_shipment_id = fields.One2many('create.shipment.fedex','picking_id','FedEx Shipment Doc')
    
        