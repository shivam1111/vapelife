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
    'name': 'JJUICE Purchase Management',
    'version': '1.1',
    'category': 'JJuice',
    'sequence': 19,
    'summary': 'Purchase Orders, Receipts, Supplier Invoices',
    'description': """
    * Add Fields 
    * Customize the workflow
    * Add tree view of stock moves
    
    - We have to manually assign the parent account to the shipping and purchase tax paid accounts created by the module
    
    """,
    'author': 'JG Infosystems',
    'website': 'https://www.jginfosystems.com',
    'images': [],
    'depends': ['base','purchase','stock','hr','account','stock'],
    'data': [ 'purchase_view.xml',
             'jjuice_data.xml',
             'stock_view.xml',
             'views/jjuice_purchase.xml',
             'views/report_purchaseorder.xml',
             'views/report_purchasequotation.xml'
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: