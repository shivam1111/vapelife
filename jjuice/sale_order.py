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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID, api
from operator import itemgetter
import operator
from openerp.exceptions import except_orm
from collections import OrderedDict
from _symtable import FREE
from openerp.exceptions import Warning

class sale_order(models.Model):
    _inherit  = "sale.order"
    _description = "Sale Order JJuice"
    
    def set_customer_lead(self,cr,uid,ids,context=None):
        '''
            This function converts the lead into customer for sale order ids
        '''
        partner = self.pool.get('res.partner')
        for order in self.pool.get("sale.order").browse(cr,uid,ids,context):
            partner.write(cr,uid,order.partner_id.id,{'customer':True,'leads':False},context)
        return True
     
        
    def action_wait(self, cr, uid, ids, context=None):
        '''
            IF the related partner is a lead then convert it into  customer
        '''
        self.set_customer_lead(cr,uid,ids,context=None)
        super(sale_order,self).action_wait(cr,uid,ids,context)
        return True
    
    
    def confirm_sales_order(self,cr,uid,sale_id,paid,method,context=None):
        if context == None:context = {}
        account_invoice = self.pool.get('account.invoice')
        self.action_button_confirm(cr,uid,sale_id,context)
        invoice_wizard = self.pool.get('sale.advance.payment.inv')
        wizard_id = invoice_wizard.create(cr,uid,{'advance_payment_method':'all'},context)
        context.update({'active_ids':sale_id,'open_invoices':True})
        res = invoice_wizard.create_invoices(cr,uid,[wizard_id],context)
        account_invoice.signal_workflow(cr, uid, [res.get('res_id',False)], 'invoice_open')
        inv = account_invoice.browse(cr,uid,res.get('res_id',False),context)
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'jjuice', 'view_vendor_receipt_dialog_form_jjuice')
        dummy, invoice_view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')
        res.update({'invoice_view_id':invoice_view_id})
        invoice_info = {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'invoice_open':True,
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                'default_amount': paid,
                'default_reference': inv.name,
                'close_after_process': True,
                'invoice_type': inv.type,
                'default_journal_id':method,
                'invoice_id': inv.id,
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
            }
        }
        return {'res':res,'invoice_info':invoice_info}
        
    def _get_product_conc_vol(self,cr,uid,attribute,product_id,context):
        ''' 
        Takes in attributes ids of volume and concentration in the order respectively and products id
        and return the name and id of the attribute values that are present from that attribute in this product
        '''   
        
        cr.execute('''
        select DISTINCT ON (att_id) att_id,child.name,prodattr.id,child.default_free_samples from  product_attribute_value_product_product_rel as base
            left join product_attribute_value as child on base.att_id = child.id  
                left join product_attribute as prodattr on child.attribute_id = prodattr.id
                    where base.prod_id = %s and (child.attribute_id = %s or child.attribute_id = %s) 

        ''' %(product_id,attribute[0],attribute[1]))
        
        res = cr.fetchall();
        return res
        
    @api.multi
    @api.depends('name',)
    def _compute_payments(self):
        for record in self:
            obj=self.env['payment.plan']
            search_id=obj.search([('order_id', '=' ,record.id)])
            record.payment_plan_ids=search_id
    
    
    def print_attachment_report(self,cr,uid,id,context=None):
        uid = SUPERUSER_ID
        assert len(id) == 1

        paid_stamp,shipping_stamp = True,True
        
        if type(id) is int: id = [id]
        
        invoice_lines = {'total':0.00,'paid':0.00,'residual':0.00,'invoice':{}}
        
        cr.execute('''
            select id from product_product where shipping =true and active = true limit 1
        ''')
        shipping_id = cr.fetchone()[0]
        brw = self.browse(cr,uid,id[0],context)
        
        comment = brw.note
        
        available_conc = {}
        available_flavor = {}
        product_list = {}
        matrix_data = {}
        list_data = {}
        marketing_data = {}
        extra_data = {}
        totals = {}
        tabs_data = set([])
        grand_total = 0
        #Collecting related invoice information
        for invoice  in brw.invoice_ids:
            #Checking for the paid_stamp
            if invoice.state != 'cancel':
                if invoice.state != 'paid':
                    paid_stamp = False
                invoice_lines['invoice'].update({
                                        invoice.number or invoice.state:{'total':invoice.amount_total,'residual':invoice.residual,'paid':invoice.amount_total - invoice.residual}
                                     })
                invoice_lines['total'] =  invoice_lines['total'] +  invoice.amount_total
                invoice_lines['residual'] = invoice_lines['residual'] +  invoice.residual
                invoice_lines['paid'] = invoice_lines['paid'] + (invoice.amount_total - invoice.residual)

        
        for line in brw.order_line:
            product_id = line.product_id
            tab_id = product_id.tab_id
            
            #Checking for the shipping stamp
            if product_id.id == shipping_id:
                if line.product_uom_qty > 0:
                    shipping_stamp = False
                continue
            grand_total = grand_total + line.product_uom_qty
            
            if tab_id:
                tabs_data.add((tab_id.id,tab_id.tab_style,tab_id.name))
                if tab_id.tab_style == 1 or tab_id.tab_style == 5:
                    # this means it is a matrix configuration
                    flavor_id = product_id.flavor_id
                    conc_id = product_id.conc_id
                    
                    if flavor_id and conc_id:
                        # available concentration and available flavors
                        if tab_id.id in available_conc.keys():
                            available_conc[tab_id.id].add((conc_id.id,conc_id.name))
                        else:
                            available_conc.update({
                                                   tab_id.id:set([(conc_id.id,conc_id.name)])
                                                   })
                        if tab_id.id in available_flavor.keys():
                            available_flavor[tab_id.id].add((flavor_id.id,flavor_id.name))
                        else:
                            available_flavor.update({
                                                   tab_id.id:set([(flavor_id.id,flavor_id.name)])
                                                   })                    
                    
                        # Adding qty data to be printed on report
                        if tab_id.id in matrix_data.keys():
                            tab_data = matrix_data[tab_id.id]
                            if flavor_id.id in tab_data.keys():
                                flavor_data = tab_data[flavor_id.id]
                                if conc_id.id in flavor_data.keys():
                                    conc_data = flavor_data[conc_id.id] or 0
                                    flavor_data[conc_id.id] = conc_data + line.product_uom_qty
                                else:
                                    flavor_data[conc_id.id] = line.product_uom_qty
                            else:
                                tab_data.update({
                                                 flavor_id.id:{
                                                               conc_id.id:line.product_uom_qty
                                                               }
                                                 })
                        else:
                            matrix_data.update({
                                                tab_id.id:{
                                                           flavor_id.id:{
                                                                         conc_id.id:line.product_uom_qty
                                                                         }
                                                           }
                                                })
                        # Totals
                        if tab_id.id in totals.keys():
                            tab_data = totals[tab_id.id]
                            if conc_id.id in tab_data:
                                before_qty = tab_data[conc_id.id]
                                tab_data[conc_id.id] = before_qty + line.product_uom_qty
                            else:
                                tab_data[conc_id.id] = line.product_uom_qty
                                
                        else:
                            totals.update({
                                           tab_id.id:{
                                                      conc_id.id:line.product_uom_qty
                                                      }
                                           })
                            
                    else:
                        raise Warning(_("Please configure product with ID %s properly"%(product_id.id)))
                    
                    
                elif tab_id.tab_style == 2 or tab_id.tab_style == 4:
                    product_list.update({
                                         product_id.id:product_id.name
                                         })
                    if tab_id.id in list_data.keys():
                        tab_data = list_data[tab_id.id]
                        if product_id.id in tab_data.keys():
                            before_qty = tab_data[product_id.id] or 0
                            tab_data[product_id.id] = before_qty + line.product_uom_qty
                        else:
                            tab_data.update({
                                             product_id.id:line.product_uom_qty,
                                             })
                            
                    else:
                        list_data.update({
                                          tab_id.id:{
                                                     product_id.id:line.product_uom_qty,
                                                     }
                                          })
                    #Totals
                    if tab_id.id in totals.keys():
                        before_total = totals[tab_id.id]
                        totals[tab_id.id] = before_total + line.product_uom_qty
                    else:
                        totals[tab_id.id] = line.product_uom_qty
                        
                         
                elif tab_id.tab_style == 3:
                    product_list.update({
                                     product_id.id:product_id.name
                             })
                    if tab_id.id in marketing_data.keys():
                        tab_data = marketing_data[tab_id.id]
                        if product_id.id in tab_data.keys():
                            before_qty = tab_data[product_id.id]
                            tab_data[product_id.id] = before_qty + line.product_uom_qty
                        else:
                            tab_data.update({
                                             product_id.id:line.product_uom_qty,
                                             })
                    else:
                        marketing_data.update({
                                               tab_id.id:{
                                                          product_id.id:line.product_uom_qty,
                                                          }
                                               })
                    #Totals
                    if tab_id.id in totals.keys():
                        before_total = totals[tab_id.id]
                        totals[tab_id.id] = before_total + line.product_uom_qty
                    else:
                        totals[tab_id.id] = line.product_uom_qty

                            
            else:
                product_list.update({
                     product_id.id:product_id.name
                 })
                # EXTRA product with out tabs
                if product_id.id in extra_data:
                    before_qty = extra_data[product_id.id]
                    extra_data[product_id.id] = before_qty + line.product_uom_qty
                else:
                    extra_data[product_id.id] = line.product_uom_qty
                
                if "extra" in totals.keys():
                    before_total = totals["extra"]
                    totals['extra'] = before_total + line.product_uom_qty
                else:
                    totals['extra'] = line.product_uom_qty
            
        for tab in available_conc:
            available_conc[tab] = list(sorted(available_conc[tab],key=itemgetter(1)))
        
        for tab in available_flavor:
            available_flavor[tab] = list(sorted(available_flavor[tab],key=itemgetter(1)))
    
        data= {
               'paid_stamp':paid_stamp,
               'shipping_stamp':shipping_stamp,
               'grand_total':grand_total,
               'invoice_line':invoice_lines,
               'comment':comment,
               'ids':id,
               'tabs_data':list(tabs_data),
               'available_conc':available_conc,
               'available_flavor':available_flavor,
               'extra_data':extra_data,
               'list_data':list_data,
               'matrix_data':matrix_data,
               'marketing_data':marketing_data,
               'totals':totals,     
               'product_list':product_list             
             }

        if context.get('stock_picking',False):
            data.update({'model':'stock.picking'})
            return {
                        'type': 'ir.actions.report.xml',
                        'report_name': 'jjuice.report_qweb_order_attachment',
                        'context':context,
                        'datas': {'model':'stock.picking','data':data}
                        }
        else:            
            return {
                        'type': 'ir.actions.report.xml',
                        'report_name': 'jjuice.report_qweb_order_attachment',
                        'context':context,
                        'datas':{'model':'sale.order','data':data}
                    }
    
    payment_plan_ids=fields.Many2many("payment.plan","payment_plan_sale_relation","order_id","payment_id","Payment Plans",)
    shipment = fields.Char('Shipment',char=240)
    internal_sale = fields.Boolean('Internal Sale')
    state = fields.Selection([
            ('draft', 'Consignment'),
            ('sent', 'Consignment Mailed'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sale Order'),
            ('manual', 'Approved'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done')])
