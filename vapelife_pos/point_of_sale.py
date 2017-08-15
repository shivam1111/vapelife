from openerp import models, fields, api, _


class product_product(models.Model):
    _inherit="product.product"
    _order = "name"
    is_bar = fields.Boolean('Is Bar ?')
    max_volume = fields.Integer('Max Volume')


class pos_order(models.Model):
    _inherit="pos.order"

    @api.model
    def get_details(self):
        res = {'conc_ids':[]}
        conc_xml_ids = ["jjuice.attribute_12","jjuice.attribute_0"]
        try:
            res['conc_ids'] = [self.env.ref(i).read([])[0] for i in conc_xml_ids]
            res['vol_350_id'] = self.env.ref('jjuice.attribute_350ml').read([])[0]
        except Exception as e:
            pass
        return res


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
                # Changes made by Shivam Goyal
                if line.product_id.is_bar:
                    for j in line.mixture_line_id:
                        qty = line.product_id.max_volume * j.mix * line.qty
                        move_list.append(move_obj.create(cr, uid, {
                            'name': line.name,
                            'product_uom': j.product_id.uom_id.id,
                            'product_uos': j.product_id.uom_id.id,
                            'picking_id': picking_id,
                            'picking_type_id': picking_type.id,
                            'product_id': j.product_id.id,
                            'product_uos_qty': abs(qty),
                            'product_uom_qty': abs(qty),
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


    def _create_account_move_line(self, cr, uid, ids, session=None, move_id=None, context=None):
        #Overridden so that we can work with multi currency while creating account.move.line lines

        # Tricky, via the workflow, we only have one id in the ids variable
        """Create a account move line of order grouped by products or not."""
        account_move_obj = self.pool.get('account.move')
        account_period_obj = self.pool.get('account.period')
        account_tax_obj = self.pool.get('account.tax')
        property_obj = self.pool.get('ir.property')
        cur_obj = self.pool.get('res.currency')

        # session_ids = set(order.session_id for order in self.browse(cr, uid, ids, context=context))

        if session and not all(session.id == order.session_id.id for order in self.browse(cr, uid, ids, context=context)):
            raise osv.except_osv(_('Error!'), _('Selected orders do not have the same session!'))

        grouped_data = {}
        have_to_group_by = session and session.config_id.group_by or False

        def compute_tax(amount, tax, line):
            if amount > 0:
                tax_code_id = tax['base_code_id']
                tax_amount = line.price_subtotal * tax['base_sign']
            else:
                tax_code_id = tax['ref_base_code_id']
                tax_amount = -line.price_subtotal * tax['ref_base_sign']

            return (tax_code_id, tax_amount,)
        order_amount_total = 0.00
        order_currency_amount_total = 0.00
        for order in self.browse(cr, uid, ids, context=context):
            if order.account_move:
                continue
            if order.state != 'paid':
                continue

            current_company = order.sale_journal.company_id

            group_tax = {}
            account_def = property_obj.get(cr, uid, 'property_account_receivable', 'res.partner', context=context)

            order_account = order.partner_id and \
                            order.partner_id.property_account_receivable and \
                            order.partner_id.property_account_receivable.id or \
                            account_def and account_def.id

            if move_id is None:
                # Create an entry for the sale
                move_id = self._create_account_move(cr, uid, order.session_id.start_at, order.name, order.sale_journal.id,
                                                    order.company_id.id, context=context)

            move = account_move_obj.browse(cr, uid, move_id, context=context)

            def insert_data(data_type, values):
                # if have_to_group_by:

                sale_journal_id = order.sale_journal.id

                # 'quantity': line.qty,
                # 'product_id': line.product_id.id,
                values.update({
                    'date': order.date_order[:10],
                    'ref': order.name,
                    'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(
                        order.partner_id).id or False,
                    'journal_id': sale_journal_id,
                    'period_id': move.period_id.id,
                    'move_id': move_id,
                    'company_id': current_company.id,
                })

                if data_type == 'product':
                    key = ('product', values['partner_id'], values['product_id'], values['analytic_account_id'],
                           values['debit'] > 0)
                elif data_type == 'tax':
                    key = ('tax', values['partner_id'], values['tax_code_id'], values['debit'] > 0)
                elif data_type == 'counter_part':
                    key = ('counter_part', values['partner_id'], values['account_id'], values['debit'] > 0)
                else:
                    return

                grouped_data.setdefault(key, [])

                # if not have_to_group_by or (not grouped_data[key]):
                #     grouped_data[key].append(values)
                # else:
                #     pass

                if have_to_group_by:
                    if not grouped_data[key]:
                        grouped_data[key].append(values)
                    else:
                        for line in grouped_data[key]:
                            if line.get('tax_code_id') == values.get('tax_code_id'):
                                current_value = line
                                current_value['quantity'] = current_value.get('quantity', 0.0) + values.get('quantity', 0.0)
                                current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
                                current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
                                current_value['tax_amount'] = current_value.get('tax_amount', 0.0) + values.get(
                                    'tax_amount', 0.0)
                                break
                        else:
                            grouped_data[key].append(values)
                else:
                    grouped_data[key].append(values)

            # because of the weird way the pos order is written, we need to make sure there is at least one line,
            # because just after the 'for' loop there are references to 'line' and 'income_account' variables (that
            # are set inside the for loop)
            # TOFIX: a deep refactoring of this method (and class!) is needed in order to get rid of this stupid hack
            assert order.lines, _('The POS order must have lines when calling this method')
            # Create an move for each order line

            cur = order.pricelist_id.currency_id
            round_per_line = True
            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                round_per_line = False
            for line in order.lines:
                to_currency = order.company_id.currency_id
                from_currency = order.sale_journal.currency or order.company_id.currency_id
                conversion = self.pool.get('res.currency')._get_conversion_rate(cr,uid,from_currency,to_currency,context)
                tax_amount = 0
                taxes = []
                for t in line.product_id.taxes_id:
                    if t.company_id.id == current_company.id:
                        taxes.append(t)
                computed_taxes = \
                account_tax_obj.compute_all(cr, uid, taxes, line.price_unit * (100.0 - line.discount) / 100.0, line.qty)[
                    'taxes']

                for tax in computed_taxes:
                    tax_amount += cur_obj.round(cr, uid, cur, tax['amount']) if round_per_line else tax['amount']
                    if tax_amount < 0:
                        group_key = (tax['ref_tax_code_id'], tax['base_code_id'], tax['account_collected_id'], tax['id'])
                    else:
                        group_key = (tax['tax_code_id'], tax['base_code_id'], tax['account_collected_id'], tax['id'])

                    group_tax.setdefault(group_key, 0)
                    group_tax[group_key] += cur_obj.round(cr, uid, cur, tax['amount']) if round_per_line else tax['amount']

                amount = line.price_subtotal
                amount = amount * conversion
                # Search for the income account
                if line.product_id.property_account_income.id:
                    income_account = line.product_id.property_account_income.id
                elif line.product_id.categ_id.property_account_income_categ.id:
                    income_account = line.product_id.categ_id.property_account_income_categ.id
                else:
                    raise osv.except_osv(_('Error!'), _('Please define income ' \
                                                        'account for this product: "%s" (id:%d).') \
                                         % (line.product_id.name, line.product_id.id,))

                # Empty the tax list as long as there is no tax code:
                tax_code_id = False
                tax_amount = 0
                while computed_taxes:
                    tax = computed_taxes.pop(0)
                    tax_code_id, tax_amount = compute_tax(amount, tax, line)

                    # If there is one we stop
                    if tax_code_id:
                        break
                vals = {
                    'name': line.product_id.name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': income_account,
                    'analytic_account_id': self._prepare_analytic_account(cr, uid, line, context=context),
                    'credit': ((amount > 0) and amount) or 0.0,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'tax_code_id': tax_code_id,
                    'tax_amount': tax_amount,
                    'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(
                        order.partner_id).id or False
                }
                if from_currency != to_currency:
                    vals.update({
                        'amount_currency':-line.price_subtotal,
                        'currency_id': from_currency.id
                    })
                # Create a move for the line
                insert_data('product', vals)

                # For each remaining tax with a code, whe create a move line
                for tax in computed_taxes:
                    tax_code_id, tax_amount = compute_tax(amount, tax, line)
                    if not tax_code_id:
                        continue

                    insert_data('tax', {
                        'name': _('Tax'),
                        'product_id': line.product_id.id,
                        'quantity': line.qty,
                        'account_id': income_account,
                        'credit': 0.0,
                        'debit': 0.0,
                        'tax_code_id': tax_code_id,
                        'tax_amount': tax_amount,
                        'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(
                            order.partner_id).id or False
                    })

            # Create a move for each tax group
            (tax_code_pos, base_code_pos, account_pos, tax_id) = (0, 1, 2, 3)

            for key, tax_amount in group_tax.items():
                tax = self.pool.get('account.tax').browse(cr, uid, key[tax_id], context=context)
                insert_data('tax', {
                    'name': _('Tax') + ' ' + tax.name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': key[account_pos] or income_account,
                    'credit': ((tax_amount > 0) and tax_amount) or 0.0,
                    'debit': ((tax_amount < 0) and -tax_amount) or 0.0,
                    'tax_code_id': key[tax_code_pos],
                    'tax_amount': abs(tax_amount),
                    'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(
                        order.partner_id).id or False
                })
            vals = {
                'name': _("Trade Receivables"),  # order.name,
                'account_id': order_account,
                'credit': ((order.amount_total < 0) and -order.amount_total) or 0.0,
                'debit': ((order.amount_total > 0) and order.amount_total) or 0.0,
                'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(
                    order.partner_id).id or False
            }
            if from_currency != to_currency:
                counterpart_amount_credit = conversion * (((order.amount_total < 0) and -order.amount_total) or 0.0)
                counterpart_amount_debit = conversion * (((order.amount_total > 0) and order.amount_total) or 0.0)
                vals.update({
                    'credit': counterpart_amount_credit,
                    'debit': counterpart_amount_debit,
                    'amount_currency':counterpart_amount_debit/conversion,
                    'currency_id':from_currency.id,
                })
            # counterpart
            insert_data('counter_part', vals)
            order.write({'state': 'done', 'account_move': move_id})

        all_lines = []
        for group_key, group_data in grouped_data.iteritems():
            for value in group_data:
                all_lines.append((0, 0, value), )
        if move_id:  # In case no order was changed
            self.pool.get("account.move").write(cr, uid, [move_id], {'line_id': all_lines}, context=context)

        return True


class pos_order_line(models.Model):
    _inherit = "pos.order.line"
    _description = "Lines of Point of Sale"


    mixture_line_id = fields.One2many('pos.mixture.line','line_id',string = 'Mixture')

class pos_mixture_line(models.Model):
    _name = "pos.mixture.line"
    _description = "POS Mixture Line"

    line_id = fields.Many2one('pos.order.line',"POS Order Line")
    product_id = fields.Many2one('product.product',"Product",required=True)
    mix = fields.Float("Mix")
