# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = 'product.template'

    production_id = fields.Many2one('mrp.production', store=True)


class ProductProductInherit(models.Model):
    _inherit = "product.product"

    @api.depends('product_template_attribute_value_ids')
    def _compute_combination_indices(self):
        for product in self:
            if self.env['product.product'].search([('combination_indices', '=', product.product_template_attribute_value_ids._ids2str())]):
                return
            product.combination_indices = product.product_template_attribute_value_ids._ids2str()