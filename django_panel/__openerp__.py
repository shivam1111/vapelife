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
    'name' : 'JJuice Django Panel',
    'version' : '0.1',
    'author' : 'J & G Infosystems',
    'category' : 'JJuice',
    'description' : """
    
   """,
    'website': '',
    'images' : [], #'/images/image_name.png'
    'depends' : ['base','web','product','jjuice'],#account_analytic_analysis
    'data': [
             'security/django_panel_security.xml',
             'data.xml',        
             'views/menu.xml',
             'views/website_banner.xml',
             'views/res_config.xml',
             'views/website_policy.xml',
             'views/product_attribute_value.xml',
             'views/product_flavors.xml',
             'views/product.xml',
             'views/hr_employee.xml',
             'views/partner_reviews.xml',
             'views/website_contactus.xml',
             'views/res_country.xml',
             'views/res_partner.xml',
             'security/ir.model.access.csv',
             'report/website_sale_order_report.xml',
             'edi/registration_email_template.xml',
             'edi/registration_wholesale_email.xml',
             'edi/registration_email_notification.xml'

         ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
