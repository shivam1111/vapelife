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
    'name' : 'JJUICE',
    'version' : '0.1',
    'author' : 'J & G Infosystems',
    'category' : 'JJuice',
    'description' : """
    
   """,
    'website': '',
    'images' : [], #'/images/image_name.png'
    'depends' : ['base','hr','crm','sale','account','stock','payment_nmi',
                 'sale_stock','sale_crm','account_acquisition'],#account_analytic_analysis
    'data': [
             'jjuice_data.xml',
             'sale_order.xml',
             'fields_view.xml',
             'product_wizard_view.xml',
             'customers_view_change.xml',
             'res_partner_view.xml',
             'jjuice.xml',
             'report/report_sale_order.xml',
             'sale_report.xml',
             'account_invoice.xml',
             'account_report.xml',
             'product_view.xml',
             'sale_stock_view.xml',
             'wizard/stock_transfer_details.xml',
             'security/ir.model.access.csv',
             'security/jjuice_security.xml',
             'views/report_invoice.xml',
             'views/report_saleorder.xml',
             'wizard/display_product_availability.xml',
             'wizard/customer_filter_wizard.xml',
             'crm_lead_view.xml',
             'payment_plan_view.xml',
             'wizard/pay_payment_plan.xml',
             'account_voucher.xml',
             'payment_plan_sequence.xml',
             'res_company.xml',
             'report/account_treasury_report_view.xml',
             'wizard/change_sale_person_customers.xml',
             'wizard/change_sale_person_lead.xml',
              'crm_lead_view.xml',
              'marketing_package.xml',
              'wizard/mail_compose_message.xml',
              'product_tab_view.xml',
              'product_flavours_view.xml'
             ],

    'qweb' : [
        "static/src/xml/*.xml",
    ],
             
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
