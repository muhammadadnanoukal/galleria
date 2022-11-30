from odoo import api, fields, models, _, SUPERUSER_ID


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    source_production = fields.Char(string="Source MO", default="none")
