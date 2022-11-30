from odoo import api, fields, models


class MrpProduction(models.Model):
    _name = 'components.details'

    production_id = fields.Many2one('mrp.production', string="Created for One2Many Relationship")
    product_id = fields.Many2one('product.product', string="Component")
    product_qty = fields.Float(string="Quantity")
    product_uom = fields.Many2one('uom.uom', string="Product Unit of Measure")
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

