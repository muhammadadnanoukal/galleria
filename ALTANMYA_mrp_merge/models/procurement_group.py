import logging
from collections import namedtuple
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    Procurement = namedtuple('Procurement', ['line', 'product_id', 'product_qty',
        'product_uom', 'location_id', 'name', 'origin', 'company_id', 'values'])