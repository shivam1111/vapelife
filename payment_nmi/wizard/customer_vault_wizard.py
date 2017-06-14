from openerp import models, fields, api, _
from ..helper import create_vault
import urlparse
from openerp.exceptions import except_orm

class customer_vault_wizard(models.TransientModel):
    _name = 'customer.vault.wizard'

    @api.multi
    def create_vault(self):
        assert len(self) == 1
        params = self.env['ir.config_parameter'].sudo()
        username =  params.get_param('nmi_username',default="username")
        pwd = params.get_param('nmi_password',default="password")
        vals = {}
        vals.update({
                'ccnumber':self.cc_number or False,
                'ccexp':self.cc_exp or False,
                'first_name':self.first_name or False,
                'last_name':self.last_name or False,
                'address1':self.address_1 or False,
                'address2':self.address_2 or False,
                'shipping_address1':self.shipping_address_1 or False,
                'shipping_address2':self.shipping_address_2 or False,
                'company':self.company or False,
                'shipping_company':self.shipping_company or False,
                'city':self.city or False,
                'shipping_city':self.shipping_city or False,
                'state':self.state or False,
                'shipping_state':self.shipping_state or False,
                'country':self.country or False,
                'shipping_country':self.shipping_country or False,
                'email':self.email or False,
                'fax':self.fax or False,
                'phone':self.cell_phone or False,
                'zip':self.postal_code or False,
                'shipping_zip':self.shipping_postal_code or False
            })  
        data = create_vault(username,pwd,vals)
        temp = urlparse.parse_qs(data)
        if temp.get('response_code')[0] == '100':
            vault = self.env['customer.vault'].create({'customer_vault_id':temp.get('customer_vault_id')[0],'partner_id':self.partner_id.id or False})
            return {
                'name':_("Vault"),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'customer.vault',
                'target': 'current',
                'res_id': vault.id,
                'context': self.env.context,                
            }            
        else:
            raise except_orm('Error Code %s'%(temp.get('response_code')),temp.get('responsetext',''))
            
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.first_name = self.partner_id.name
            self.shipping_first_name = self.partner_id.name
            self.address_1 = self.partner_id.street
            self.address_2 = self.partner_id.street2
            self.shipping_address_1 = self.partner_id.street
            self.shipping_address_2 =  self.partner_id.street2
            self.company = self.partner_id.parent_id.name or ''
            self.shipping_company = self.partner_id.parent_id.name or ''
            self.city = self.partner_id.city
            self.shipping_city = self.partner_id.city
            self.state = self.partner_id.state_id.code
            self.shipping_state = self.partner_id.state_id.code
            self.country = self.partner_id.country_id.code
            self.shipping_country = self.partner_id.country_id.code
            self.email = self.partner_id.email
            self.fax = self.partner_id.fax
            self.cell_phone = self.partner_id.mobile
            self.phone = self.partner_id.phone
            self.postal_code = self.partner_id.zip
            self.shipping_postal_code = self.partner_id.zip
            self.website = self.partner_id.website
            
            
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    address_1 = fields.Char('Address')
    address_2 = fields.Char('Address2')
    company = fields.Char('Company Name')
    city = fields.Char('City')
    state = fields.Char('State')
    postal_code = fields.Char('Postal Code')
    country = fields.Char('Country')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    fax = fields.Char('Fax')
    cell_phone = fields.Char('Cell Phone')
    website = fields.Char("Website")
    shipping_first_name = fields.Char("First Name")
    shipping_last_name = fields.Char('Last Name')
    shipping_address_1 = fields.Char('Address')
    shipping_address_2 = fields.Char('Address2')
    shipping_company = fields.Char('Company Name')
    shipping_city = fields.Char('City')
    shipping_state = fields.Char('State')
    shipping_postal_code = fields.Char('Postal Code')
    shipping_country = fields.Char('Country')
    shipping_email = fields.Char('Email')
    shipping_carrier = fields.Char('Carrier')
    tracking_number = fields.Char("Tracking Number")
    shipping_date = fields.Char('Date')
    shipping = fields.Char('Shipping')
    cc_number = fields.Char("CC Number")
    cc_exp = fields.Char('Expiry Date')
    cc_start_date = fields.Char("CC Start Date")
    partner_id = fields.Many2one('res.partner','Partner')
    
    
    