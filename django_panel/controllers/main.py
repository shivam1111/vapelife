import logging
import werkzeug

import openerp,datetime,requests,json
from openerp.addons.auth_signup.res_users import SignupError
from openerp.addons.web.controllers.main import ensure_db
from openerp import http
from openerp.http import request
from openerp.tools.translate import _
from requests.auth import HTTPBasicAuth

_logger = logging.getLogger(__name__)

class AuthSignupHome(openerp.addons.web.controllers.main.Home):

    @http.route('/web/signup', type='http', auth='public', website=True)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            # {'confirm_password': u'shivam', 'redirect': u'', 'token': u'XoWD6GPbdw6oelpRxQwK',
            #  'reset_password_enabled': False, 'name': u'SanDeep', 'login': u'shivam1111@gmail.com',
            #  'password': u'shivam', 'db': u'jjuice', 'signup_enabled': True}
            try:
                self.do_signup(qcontext)
                start = datetime.datetime.now()
                url = request.registry['ir.config_parameter'].get_param(request.cr, openerp.SUPERUSER_ID,
                                                                        'website_url') + "/accounts/odoo_signup/"
                login = request.registry['ir.config_parameter'].get_param(request.cr, openerp.SUPERUSER_ID,
                                                                          'website_username')
                pwd = request.registry['ir.config_parameter'].get_param(request.cr, openerp.SUPERUSER_ID, 'website_pwd')
                qcontext.update({
                    'website_username':login,
                    'website_password':pwd,
                })
                try:
                    response = requests.post(url, data=qcontext, headers={},
                                             auth=HTTPBasicAuth(login, pwd))
                    response_data = response.json()
                    if response_data.get('error',False):
                        qcontext['error'] = _("Sorry we faced some problem completing the registration. Please try again!")
                        return request.render('auth_signup.signup', qcontext)
                    return request.redirect(request.registry['ir.config_parameter'].get_param(request.cr, openerp.SUPERUSER_ID,
                                                                        'website_url'))
                except Exception as e:
                    # This means there was a connection problem
                    _logger.error(e.message)
                    qcontext['error'] = _(e.message)
                    return request.render('auth_signup.signup', qcontext)
            except (SignupError, AssertionError), e:
                qcontext['error'] = _(e.message)
        return request.render('auth_signup.signup', qcontext)
