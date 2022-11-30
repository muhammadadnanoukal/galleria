# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict

from odoo import api, fields, models
from odoo.tools import float_compare, clean_context, OrderedSet


class StockMove(models.Model):
    _inherit = 'stock.move'

    source_production = fields.Char(string="Source MO", default="none")
    move_price_unit = fields.Float(string='Unit Price', copy=False)
    price_subtotal = fields.Float('Subtotal', compute='_compute_price_subtotal', default=0.0)
    product_tmpl_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
    color = fields.Many2one('product.attribute.value', string="Component Color",
                            domain="[('attribute_id.name', 'like', 'لون'), ('attribute_id.product_tmpl_ids', 'in', product_tmpl_id)]")
    can_change_color = fields.Boolean(default=False)
    sale_order_source = fields.Char("Source SO", default='none')
    sale_order_line_id = fields.Many2one('sale.order.line')

    def _compute_can_change_color(self):
        if self.product_tmpl_id:
            recs = self.env['product.attribute.value'].search([('attribute_id.name', 'like', 'لون'),
                                                               ('attribute_id.product_tmpl_ids', 'in',
                                                                self.product_tmpl_id.ids)])
            for rec in recs:
                if rec.name.lower() == 'standard':
                    self.can_change_color = True

    @api.onchange('color')
    def _onchange_color(self):
        _self = self.copy_data()[0]
        color_attribute_id = self.color.attribute_id.id
        color_id = self.color.id
        for value_id in self.product_id.product_template_variant_value_ids:
            if value_id.attribute_id.id == self.color.attribute_id.id:
                new_color_id = self.env['product.template.attribute.value'].search(
                    [('product_attribute_value_id', '=', self.color.id),
                     ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)])
                self.product_id.product_template_variant_value_ids = [(3, value_id.id)]
                self.product_id.product_template_variant_value_ids = [(4, new_color_id.id)]
                if self.product_id.variant_bom_ids:
                    bom = self.product_id.variant_bom_ids[0]
                    if bom:
                        templates_standard_recs = self.env['product.attribute.value'].search(
                            [('name', 'ilike', 'standard')])
                        templates_standard_ids = []
                        for rec in templates_standard_recs:
                            templates_standard_ids.extend(rec.attribute_id.product_tmpl_ids.ids)
                        for line in bom.bom_line_ids:
                            if line.product_id.product_tmpl_id.id in templates_standard_ids:
                                other_attrs_vals_ids = []
                                for val in line.product_id.product_template_variant_value_ids:
                                    if val.attribute_id.id != color_attribute_id:
                                        other_attrs_vals_ids.append(val.id)
                                new_line_color_id = self.get_new_line_color(new_color_id,
                                                                            line.product_id.product_tmpl_id.id)
                                other_attrs_vals_ids.append(new_line_color_id.id)
                                new_product = self.get_new_variant(line.product_id,
                                                                   [(4, val) for val in other_attrs_vals_ids])
                                if not new_product:
                                    continue
                                new_line = self.env['mrp.bom.line'].create({'product_id': new_product.id,
                                                                            'product_qty': line.product_qty,
                                                                            'product_uom_id': line.product_uom_id.id,
                                                                            'bom_id': bom.id})
                                bom.bom_line_ids = [(3, line.id)]
                                bom.bom_line_ids = [(4, new_line.id)]
                elif self.product_id.product_tmpl_id.bom_ids:
                    bom = self.product_id.product_tmpl_id.bom_ids.filtered(lambda b: not b.product_id)
                    if bom:
                        new_bom = bom.copy()
                        new_bom.write({'product_id': self.product_id.id})
                        self.product_id.variant_bom_ids = [(4, new_bom.id)]
                        templates_standard_recs = self.env['product.attribute.value'].search(
                            [('name', 'ilike', 'standard')])
                        templates_standard_ids = []
                        for rec in templates_standard_recs:
                            templates_standard_ids.extend(rec.attribute_id.product_tmpl_ids.ids)
                        for line in new_bom.bom_line_ids:
                            if line.product_id.product_tmpl_id.id in templates_standard_ids:
                                other_attrs_vals_ids = []
                                line.product_id._compute_combination_indices()
                                for val in line.product_id.product_template_variant_value_ids:
                                    if val.attribute_id.id != color_attribute_id:
                                        other_attrs_vals_ids.append(val.id)
                                new_line_color_id = self.get_new_line_color(new_color_id,
                                                                            line.product_id.product_tmpl_id.id)
                                other_attrs_vals_ids.append(new_line_color_id.id)
                                new_product = self.get_new_variant(line.product_id,
                                                                   [(4, val) for val in other_attrs_vals_ids])
                                if not new_product:
                                    continue
                                new_line = self.env['mrp.bom.line'].create({'product_id': new_product.id,
                                                                            'product_qty': line.product_qty,
                                                                            'product_uom_id': line.product_uom_id.id,
                                                                            'bom_id': new_bom.id})
                                new_bom.bom_line_ids = [(3, line.id)]
                                new_bom.bom_line_ids = [(4, new_line.id)]
            self.product_id._compute_combination_indices()
            self.write(_self)
            self.write({'color': color_id})
            self.production_id.hide_components_details()

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.move_price_unit = self.compute_price_unit()

    def compute_price_unit(self):
        move_price_unit = 0.0
        from_pricelist = self.env['product.pricelist.item'].search(
            [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
             ('pricelist_id', '=', self.production_id.pricelist_id.id)], limit=1)
        if not from_pricelist:
            from_template = self.env['product.template'].search([('id', '=', self.product_id.product_tmpl_id.id)],
                                                                limit=1)
            if from_template:
                move_price_unit = from_template.list_price
        else:
            move_price_unit = from_pricelist.fixed_price


        return move_price_unit

    def update_product(self):
        if not self.product_id:
            self.move_price_unit = 0.0
            return
        if self.production_id.pricelist_id:
            self.product_id.with_context(
                quantity=self.product_uom_qty,
                pricelist=self.production_id.pricelist_id.id,
            )

    @api.depends('move_price_unit', 'product_qty')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.move_price_unit * line.product_qty

    def get_new_variant(self, p, attribute_values):
        attribute_values_ids = [t[1] for t in attribute_values]
        variants = self.env['product.product'].search([('product_tmpl_id', '=', p.product_tmpl_id.id)])
        for variant in variants:
            if len(list(set(variant.product_template_variant_value_ids.ids) & set(attribute_values_ids))) == len(
                    attribute_values_ids):
                return variant
        product_variant = self.env['product.product'].create({
            'product_tmpl_id': p.product_tmpl_id.id,
            'detailed_type': p.detailed_type,
            'invoice_policy': p.invoice_policy,
            'expense_policy': p.expense_policy,
            'uom_id': p.uom_id.id,
            'uom_po_id': p.uom_po_id.id,
            'lst_price': p.lst_price,
            'weight': p.weight,
            'weight_uom_name': p.weight_uom_name,
            'volume': p.volume,
            'volume_uom_name': p.volume_uom_name,
            'produce_delay': p.produce_delay,
            'sale_delay': p.sale_delay if p.sale_ok else False,
            'property_account_expense_id': p.property_account_expense_id,
            'property_account_creditor_price_difference': p.property_account_creditor_price_difference,
            'property_account_income_id': p.property_account_income_id,
            'taxes_id': p.taxes_id.id,
            'standard_price': p.standard_price,
            'categ_id': p.categ_id.id,
            'sale_ok': p.sale_ok,
            'purchase_ok': p.purchase_ok,
            'variant_seller_ids': [(4, e.id) for e in p.variant_seller_ids] if p.purchase_ok else False,
            'purchase_method': p.purchase_method if p.purchase_ok else False,
            'route_ids': [(4, e.id) for e in p.route_ids],
            'route_from_categ_ids': [(4, e.id) for e in p.route_from_categ_ids],
            'property_stock_production': p.property_stock_production.id,
            'property_stock_inventory': p.property_stock_inventory.id,
        })
        product_variant.write({
            'product_template_variant_value_ids': attribute_values,
            'combination_indices': ','.join([str(i) for i in sorted(attribute_values_ids)]),
        })
        return product_variant

    def get_new_line_color(self, new_color_id, line_tmpl_id):
        rec = self.env['product.template.attribute.value'].search(
            [('product_attribute_value_id', '=', new_color_id.product_attribute_value_id.id),
             ('product_tmpl_id', '=', line_tmpl_id)])
        if rec:
            return rec

        attribute_line_id = self.env['product.template.attribute.line'].search([('product_tmpl_id', '=', line_tmpl_id),
                                                                                ('attribute_id', '=',
                                                                                 new_color_id.attribute_id.id)])

        rec = self.env['product.template.attribute.value'].create({
            'product_attribute_value_id': new_color_id.product_attribute_value_id.id,
            'product_tmpl_id': line_tmpl_id,
            'attribute_line_id': attribute_line_id.id
        })
        return rec

    def _action_confirm(self, merge=True, merge_into=False):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        :param: merge: According to this boolean, a newly confirmed move will be merged
        in another move of the same picking sharing its characteristics.
        """
        # Use OrderedSet of id (instead of recordset + |= ) for performance
        move_create_proc, move_to_confirm, move_waiting = OrderedSet(), OrderedSet(), OrderedSet()
        to_assign = defaultdict(OrderedSet)
        for move in self:
            if move.state != 'draft':
                continue
            # if the move is preceded, then it's waiting (if preceding move is done, then action_assign has been called already and its state is already available)
            if move.move_orig_ids:
                move_waiting.add(move.id)
            else:
                if move.procure_method == 'make_to_order':
                    move_create_proc.add(move.id)
                else:
                    move_to_confirm.add(move.id)
            if move._should_be_assigned():
                key = (move.group_id.id, move.location_id.id, move.location_dest_id.id)
                to_assign[key].add(move.id)

        move_create_proc, move_to_confirm, move_waiting = self.browse(move_create_proc), self.browse(move_to_confirm), self.browse(move_waiting)

        # create procurements for make to order moves
        procurement_requests = []
        for move in move_create_proc:
            values = move._prepare_procurement_values()
            origin = move._prepare_procurement_origin()
            procurement_requests.append(self.env['procurement.group'].Procurement(
                move.sale_order_line_id, move.product_id, move.product_uom_qty, move.product_uom,
                move.location_id, move.rule_id and move.rule_id.name or "/",
                origin, move.company_id, values))
        self.env['procurement.group'].run(procurement_requests, raise_user_error=not self.env.context.get('from_orderpoint'))

        move_to_confirm.write({'state': 'confirmed'})
        (move_waiting | move_create_proc).write({'state': 'waiting'})
        # procure_method sometimes changes with certain workflows so just in case, apply to all moves
        (move_to_confirm | move_waiting | move_create_proc).filtered(lambda m: m.picking_type_id.reservation_method == 'at_confirm')\
            .write({'reservation_date': fields.Date.today()})

        # assign picking in batch for all confirmed move that share the same details
        for moves_ids in to_assign.values():
            self.browse(moves_ids).with_context(clean_context(self.env.context))._assign_picking()
        new_push_moves = self.filtered(lambda m: not m.picking_id.immediate_transfer)._push_apply()
        self._check_company()
        moves = self
        if merge:
            moves = self._merge_moves(merge_into=merge_into)

        # Transform remaining move in return in case of negative initial demand
        neg_r_moves = moves.filtered(lambda move: float_compare(
            move.product_uom_qty, 0, precision_rounding=move.product_uom.rounding) < 0)
        for move in neg_r_moves:
            move.location_id, move.location_dest_id = move.location_dest_id, move.location_id
            orig_move_ids, dest_move_ids = [], []
            for m in move.move_orig_ids | move.move_dest_ids:
                from_loc, to_loc = m.location_id, m.location_dest_id
                if float_compare(m.product_uom_qty, 0, precision_rounding=m.product_uom.rounding) < 0:
                    from_loc, to_loc = to_loc, from_loc
                if to_loc == move.location_id:
                    orig_move_ids += m.ids
                elif move.location_dest_id == from_loc:
                    dest_move_ids += m.ids
            move.move_orig_ids, move.move_dest_ids = [(6, 0, orig_move_ids)], [(6, 0, dest_move_ids)]
            move.product_uom_qty *= -1
            if move.picking_type_id.return_picking_type_id:
                move.picking_type_id = move.picking_type_id.return_picking_type_id
            # We are returning some products, we must take them in the source location
            move.procure_method = 'make_to_stock'
        neg_r_moves._assign_picking()

        # call `_action_assign` on every confirmed move which location_id bypasses the reservation + those expected to be auto-assigned
        moves.filtered(lambda move: not move.picking_id.immediate_transfer
                       and move.state in ('confirmed', 'partially_available')
                       and (move._should_bypass_reservation()
                            or move.picking_type_id.reservation_method == 'at_confirm'
                            or (move.reservation_date and move.reservation_date <= fields.Date.today())))\
             ._action_assign()
        if new_push_moves:
            neg_push_moves = new_push_moves.filtered(lambda sm: float_compare(sm.product_uom_qty, 0, precision_rounding=sm.product_uom.rounding) < 0)
            (new_push_moves - neg_push_moves)._action_confirm()
            # Negative moves do not have any picking, so we should try to merge it with their siblings
            neg_push_moves._action_confirm(merge_into=neg_push_moves.move_orig_ids.move_dest_ids)

        return moves
