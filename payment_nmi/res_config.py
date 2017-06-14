# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv

class integration_config_settings(osv.osv_memory):
    _inherit = 'integrations.config.settings'

    def set_default_nmi_username(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'nmi_username', (myself.nmi_username or '').strip(), groups=['base.group_system'], context=None)

    def get_default_nmi_username(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        nmi_username = params.get_param(cr, uid, 'nmi_username',default='',context=context)        
        return dict(nmi_username=nmi_username)
    
    def set_default_nmi_password(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'nmi_password', (myself.nmi_password or '').strip(), groups=['base.group_system'], context=None)

    def get_default_nmi_password(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        nmi_password = params.get_param(cr, uid, 'nmi_password',default='',context=context)        
        return dict(nmi_password=nmi_password)        

    def set_default_nmi_key(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'nmi_key', (myself.nmi_key or '').strip(), groups=['base.group_system'], context=None)

    def get_default_nmi_key(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        nmi_key = params.get_param(cr, uid, 'nmi_key',default='',context=context)        
        return dict(nmi_key=nmi_key)            

    _columns = {
                'nmi_username':fields.char('Username'),
                'nmi_password':fields.char('Password'),
                'nmi_key':fields.char('NMI API Key'),
            }