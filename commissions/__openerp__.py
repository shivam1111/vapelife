# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
{
    'name' : 'JJuice Commissions Calculator',
    'version' : '0.1',
    'author' : 'J & G Infosystems',
    'category' : 'JJuice',
    'description' : """
    
   """,
    'website': '',
    'images' : [], #'/images/image_name.png'
    'depends' : ['base','account','jjuice','hr'],#account_analytic_analysis
    'data': [
             'security/commission_security.xml',
             'security/ir.model.access.csv',
             'wizard/account_commissions_view.xml',
             'account_commissions_archive_view.xml',
             'commissions_report.xml',
             'views/report_account_commissions.xml',
             ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
