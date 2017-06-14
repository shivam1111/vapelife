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
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class stock_picking(osv.osv):
    _inherit="stock.picking"
    _order="date desc"

    

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _columns = {
                'shipment_number':fields.char('Shipment Tracking Number', ),
                }
    
    def print_delivery_report_custom(self,cr,uid,ids,context=None):
        assert len(ids) == 1
        if type(ids) is int: ids = [ids]
        sale_id = self.read(cr,uid,ids[0],{'sale_id'},context)
        if sale_id.get('sale_id',False):
            context.update({'stock_picking':True})
            return self.pool.get('sale.order').print_attachment_report(cr,uid,[sale_id.get('sale_id',[0])[0]],context)
        else: return True