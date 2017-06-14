# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import time
from openerp import SUPERUSER_ID
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv

# This  prints a new delivery list 
class order_website_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(order_website_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'is_shipping_free':self.is_shipping_free
        })
        self.context = context
    
    def is_shipping_free(self,order):
        print dir(self)
        self.cr.execute('''
            select id from product_product where shipping =true and active = true limit 1
        ''')
        shipping_id = self.cr.fetchone()[0]
        shipping = True
        if shipping_id:
            for i in order.order_line:
                if i.product_id.id == shipping_id and i.price_subtotal > 0:
                    shipping = False
                    break
        return shipping
        
    def set_context(self, objects, data, ids, report_type=None,context=None):
        if data == None:data={}
#         if data.get('model',False) == 'stock.picking':
#             brw_object = self.pool.get('sale.order').browse(self.cr,SUPERUSER_ID,data.get('data',False).get('ids',False),context=None)
#             if brw_object:
#                 return super(order_original_report, self).set_context(brw_object, data.get('data',False), [brw_object.id], report_type=report_type)
        return super(order_website_report, self).set_context(objects, data.get('data',False), ids, report_type=report_type)


class report_website_order_final(osv.AbstractModel):
    _name = 'report.django_panel.report_qweb_order_website_report'
    _inherit = 'report.abstract_report'
    _template = 'django_panel.report_qweb_order_website_report'
    _wrapped_report_class = order_website_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: