# -*- coding: utf-8 -*-

from odoo import api, models, _


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    @api.model
    def get_html(self, bom_id=False, searchQty=1, searchVariant=False):
        if self.env.context['model'] == 'mrp.production':
            bom_id = self.env['mrp.production'].search([('id', '=', self.env.context['active_id'])]).bom_id.id
        if not self.env['mrp.bom'].search([('id', '=', bom_id)]):
            bom_id = self.env['mrp.production'].search([('id', '=', self.env.context['active_id'])]).bom_id.id
        res = self._get_report_data(bom_id=bom_id, searchQty=searchQty, searchVariant=searchVariant)
        res['lines']['report_type'] = 'html'
        res['lines']['report_structure'] = 'all'
        res['lines']['has_attachments'] = res['lines']['attachments'] or any(component['attachments'] for component in res['lines']['components'])
        res['lines'] = self.env.ref('mrp.report_mrp_bom')._render({'data': res['lines']})
        return res
