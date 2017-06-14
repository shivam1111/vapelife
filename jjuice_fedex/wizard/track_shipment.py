from openerp import models, fields, api, _
from ..config import fedex_config
from openerp.exceptions import except_orm,Warning
import logging
from ..fedex.services.track_service import FedexTrackRequest

class track_fedex_shipment(models.TransientModel):
    _name = "track.fedex.shipment"
    _rec_name = 'number'
    
    @api.multi
    def update_reponse(self):
        res = self.track_shipment_number()
        msg = ''
        if res.get('type',False) == 'error':
            msg = "Error Code %s. \n"%(res.get('code',''))
            msg = msg + res.get('msg','')
        elif res.get('type',False) == 'response':
            for j in res.get('msg',[]):
                msg = "Tracking Number: %s"%(j[0]) + "  Status: %s\n"%(j[1])
        self.status = msg
        compose_form = self.env.ref('jjuice_fedex.track_shipment_form', False)
        return {
            'name': _('Track Shipment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'res_model': 'track.fedex.shipment',
            'target': 'new',
            'res_id':self.id,
            'nodestroy': True,
            'context':self._context                
                }

    @api.multi
    def track_shipment_number(self):
        res = self.env['fedex.account'].get_fedex_account()
        if res:
            config_object = fedex_config(
                             key=res.get('key',False),
                             password=res.get('password',False),
                             account_number=res.get('account_number',False),
                             meter_number=res.get('meter_number',False),
                             freight_account_number=res.get('freight_account_number',False),
                             use_test_server=res.get('use_test_server',False)
                             )
            
            # Set this to the INFO level to see the response from Fedex printed in stdout.
            logging.basicConfig(level=logging.INFO)
            # NOTE: TRACKING IS VERY ERRATIC ON THE TEST SERVERS. YOU MAY NEED TO USE
            # PRODUCTION KEYS/PASSWORDS/ACCOUNT #.
            # We're using the FedexConfig object from example_config.py in this dir.
            track = FedexTrackRequest(config_object.CONFIG_OBJ)
            track.TrackPackageIdentifier.Type = 'TRACKING_NUMBER_OR_DOORTAG'
            track.TrackPackageIdentifier.Value = self.number
            # Fires off the request, sets the 'response' attribute on the object.
            try:
                track.send_request()
            except:
                code = track.response['Notifications'][0]['Code']
                msg = track.response['Notifications'][0]['Message']
                return {
                       'type':'error',
                       'code':code,
                       'msg':msg
                       
                       }
            # See the response printed out.
            # Look through the matches (there should only be one for a tracking number
            # query), and show a few details about each shipment.
            # In case of create shipment we do not want to display msg. We want to update the status
            res = {'type':'response','msg':[]}
            for match in track.response.TrackDetails:
                res['msg'].append((match.TrackingNumber,match.StatusDescription))
                return res
        else:
            raise except_orm(_('Account Configuration!'),
                _("No Fedex Account has been configured")
                ) 
        
    number = fields.Char('Shipment Number')
    status = fields.Char('Status')