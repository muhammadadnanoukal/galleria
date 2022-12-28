# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import http, _
from odoo.http import request
import logging
from odoo.addons.http_routing.models.ir_http import slug

logger = logging.getLogger(__name__)

from odoo.addons.portal.controllers import portal


class ProductPublisher(portal.CustomerPortal):

    @http.route(["/product/categories"],
                type='json', auth='public')
    def ProductCategory(self, **kwargs):
        try:
            categories = request.env['product.template'].product_category()
            return categories or {
                'code':100,
                'error':'Failed to get product categories'
            }
        except Exception:
            logger.exception("Failed to get product categories")

        return request.not_found()
    

    @http.route(["/product/variants"],
                type='json', auth='public')
    def ProductVariants(self, **kwargs):
        try:
            categories = request.env['product.template'].product_attributes()
            return categories or {
                'code':100,
                'error':'Failed to get product categories'
            }
        except Exception:
            logger.exception("Failed to get product variants")

        return request.not_found()


   