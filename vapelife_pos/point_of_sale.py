from openerp import models, fields, api, _

_MIXTURE = [('quarter','Quarter'),('half','Half'),('three_quarters','Three Quarters'),('full','Full')]
_RATIO = [('quarter',0.25),('half',0.50),('three_quarters',0.75),('full',1)]
_RATIO_DICT = dict(_RATIO)
class product_product(models.Model):
    _inherit="product.product"
    _order = "name"
    is_bar = fields.Boolean('Is Bar ?')
    max_volume = fields.Integer('Max Volume')


class pos_order(models.Model):
    _inherit="pos.order"

    def create_picking(self, cr, uid, ids, context=None):
        """Create a picking for each order and validate it."""
        picking_obj = self.pool.get('stock.picking')
        partner_obj = self.pool.get('res.partner')
        move_obj = self.pool.get('stock.move')

        for order in self.browse(cr, uid, ids, context=context):
            if all(t == 'service' for t in order.lines.mapped('product_id.type')):
                continue
            addr = order.partner_id and partner_obj.address_get(cr, uid, [order.partner_id.id], ['delivery']) or {}
            picking_type = order.picking_type_id
            picking_id = False
            if picking_type:
                picking_id = picking_obj.create(cr, uid, {
                    'origin': order.name,
                    'partner_id': addr.get('delivery', False),
                    'date_done': order.date_order,
                    'picking_type_id': picking_type.id,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'invoice_state': 'none',
                }, context=context)
                self.write(cr, uid, [order.id], {'picking_id': picking_id}, context=context)
            location_id = order.location_id.id
            if order.partner_id:
                destination_id = order.partner_id.property_stock_customer.id
            elif picking_type:
                if not picking_type.default_location_dest_id:
                    raise osv.except_osv(_('Error!'), _(
                        'Missing source or destination location for picking type %s. Please configure those fields and try again.' % (
                        picking_type.name,)))
                destination_id = picking_type.default_location_dest_id.id
            else:
                destination_id = partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)[
                    'property_stock_customer']

            move_list = []
            for line in order.lines:
                if line.product_id and line.product_id.type == 'service':
                    continue
                move_list.append(move_obj.create(cr, uid, {
                    'name': line.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_uos': line.product_id.uom_id.id,
                    'picking_id': picking_id,
                    'picking_type_id': picking_type.id,
                    'product_id': line.product_id.id,
                    'product_uos_qty': abs(line.qty),
                    'product_uom_qty': abs(line.qty),
                    'state': 'draft',
                    'location_id': location_id if line.qty >= 0 else destination_id,
                    'location_dest_id': destination_id if line.qty >= 0 else location_id,
                }, context=context))
                if line.product_id.is_bar:
                    if line.product_mix_a_id:
                        qty_a = line.product_id.max_volume * _RATIO_DICT.get(line.mixture)
                        move_list.append(move_obj.create(cr, uid, {
                            'name': line.name,
                            'product_uom': line.product_mix_a_id.uom_id.id,
                            'product_uos': line.product_mix_a_id.uom_id.id,
                            'picking_id': picking_id,
                            'picking_type_id': picking_type.id,
                            'product_id': line.product_mix_a_id.id,
                            'product_uos_qty': abs(qty_a),
                            'product_uom_qty': abs(qty_a),
                            'state': 'draft',
                            'location_id': location_id if line.qty >= 0 else destination_id,
                            'location_dest_id': destination_id if line.qty >= 0 else location_id,
                        }, context=context))
                        if line.mixture != "full" and line.product_mix_a_id:
                            qty_b = line.product_id.max_volume * (1 - _RATIO_DICT.get(line.mixture))

                            move_list.append(move_obj.create(cr, uid, {
                                'name': line.name,
                                'product_uom': line.product_mix_b_id.uom_id.id,
                                'product_uos': line.product_mix_b_id.uom_id.id,
                                'picking_id': picking_id,
                                'picking_type_id': picking_type.id,
                                'product_id': line.product_mix_b_id.id,
                                'product_uos_qty': abs(qty_b),
                                'product_uom_qty': abs(qty_b),
                                'state': 'draft',
                                'location_id': location_id if line.qty >= 0 else destination_id,
                                'location_dest_id': destination_id if line.qty >= 0 else location_id,
                            }, context=context))


            if picking_id:
                picking_obj.action_confirm(cr, uid, [picking_id], context=context)
                picking_obj.force_assign(cr, uid, [picking_id], context=context)
                picking_obj.action_done(cr, uid, [picking_id], context=context)
            elif move_list:
                move_obj.action_confirm(cr, uid, move_list, context=context)
                move_obj.force_assign(cr, uid, move_list, context=context)
                move_obj.action_done(cr, uid, move_list, context=context)
        return True

class pos_order_line(models.Model):
    _inherit = "pos.order.line"
    _description = "Lines of Point of Sale"


    product_mix_a_id =  fields.Many2one('product.product', 'Product A', domain=[('sale_ok', '=', True)])



    product_mix_b_id = fields.Many2one('product.product', 'Product B', domain=[('sale_ok', '=', True)])

    mixture = fields.Selection(_MIXTURE)