from openerp import models, fields, api, _
from urlparse import urlsplit
from openerp.exceptions import except_orm

class res_partner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def convert_lead_partner(self):
        user = self.env['res.users'].sudo()
        for i in self:
            i.leads = False
            i.customer = True
            i.child_ids.leads = False
            i.child_ids.customer = True
            user = self.env['res.users'].sudo()
            user_id = user.search([('partner_id','=',i.id),('active','=',False)])
            if user_id:
                user_id.active=True
                user_id.action_reset_password()
                template = self.env.ref('django_panel.email_template_registration_website_wholesale', False)
                self.env['email.template'].sudo().browse(template.id).send_mail(i.id, force_send=True)

    @api.multi
    def delete_wholesale_account_lead(self):
        from xmlrpclib import ServerProxy
        username = self.env['ir.config_parameter'].get_param('website_username')
        password = self.env['ir.config_parameter'].get_param('website_pwd')
        website_url = self.env['ir.config_parameter'].get_param('website_url')
        urlspl = urlsplit(website_url)
        s = ServerProxy(urlspl.scheme+"://"+username+":"+password+"@"+urlspl.netloc)
        user = self.env['res.users'].sudo()
        for i in self:
            user_id = user.search([('partner_id', '=', i.id), ('active', '=', False)])
            if user_id:
                resp = s.odoo.delete_user(user_id.id)
                if not resp:
                    raise except_orm('Error', "Due to some reason we were unable to delete the user from Django Panel. Please contact your techincal advisor")
                user_id.unlink()

    django_id = fields.Integer("Django ID")

