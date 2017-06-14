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
    'name': 'FEDEX',
    'version': '1.1',
    'category': 'JJuice',
    'sequence': 19,
    'summary': 'FEDEX Integration',
    'description': """
FEDEX INTEGRATION
=================
    """,
    'author': 'J & G Infosystems',
    'website': 'https://www.jginfosystems.com',
    'images': [],
    'depends': ['base',
                'integrations',
                'knowledge',
                'stock',
                'jjuice',
                'web'
                ],
    'data': [
             'security/fedex_security.xml',
             'fedex_account_view.xml',
             'wizard/track_shipment_view.xml',
             'wizard/rate_request.xml',
             'fedex_account_sequence.xml',
             'create_shipment.xml',
             'wizard/fedex_message.xml',
             'stock_view.xml',
             'views/jjuice_fedex.xml',
             'report/print_label.xml'
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
