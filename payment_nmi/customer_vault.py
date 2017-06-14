from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from helper import get_vault_detail,delete_vault
import xml.etree.ElementTree as ET
from openerp.exceptions import Warning
import urlparse
from openerp.exceptions import except_orm

class customer_vault(models.Model):
    _name = 'customer.vault'
    _rec_name = "customer_vault_id"
    
    @api.multi
    def delete_vault(self):
        assert len(self) == 1
        params = self.env['ir.config_parameter'].sudo()
        username =  params.get_param('nmi_username',default="username")
        pwd = params.get_param('nmi_password',default="password")        
        data = delete_vault(username,pwd,self.customer_vault_id)
        temp = urlparse.parse_qs(data)
        raise Warning('Code:%s'%(temp.get('response_code')[0]),temp.get('responsetext','')[0])
    
    @api.multi
    def get_vault_details(self):
        assert len(self) == 1
        params = self.env['ir.config_parameter'].sudo()
        username =  params.get_param('nmi_username',default="username")
        pwd = params.get_param('nmi_password',default="password")        
        details = get_vault_detail(username,pwd,self.customer_vault_id)
        root = ET.fromstring(details)
        try:
            customer  = root.find('customer_vault').find('customer')
            vals = {}
            for child in customer:
                vals.update({
                        child.tag:child.text
                })
            vault_wizard = self.env['customer.vault.wizard'].create(vals)
            view  = self.env.ref('payment_nmi.customer_vault_wizard_form_view')
            return {
                'name':_("Vault Details"),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'customer.vault.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': vault_wizard.id,
                'context': self.env.context,                
            }
        except Exception as e:
            raise except_orm('Error',e)

    customer_vault_id = fields.Char('Customer Vault ID',required=True)
    partner_id = fields.Many2one('res.partner','Partner')
