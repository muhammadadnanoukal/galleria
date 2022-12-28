from odoo import api, fields, models, _, tools

import logging

import requests
from odoo.exceptions import ValidationError, UserError
import json
_logger = logging.getLogger(__name__)
import pprint
import base64


class PublishProductTemplate(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    @api.model
    def to_dict(self):
        #-------------------------
        #api for category list
        #api for attributes -> values 
        #------------------------------
        return {
            'name':self.name,
            'template_id':self.product_tmpl_id.id,
            # 'image':self.image_1920.decode('utf-8') if self.image_1920 else self.image_1920,
            'uom_id':self.uom_id.name,
            'list_price':self.list_price,
            'price_extra': self.price_extra,
            'qty_available': self.qty_available,
            'taxes_id': self.taxes_id.name,
            'taxes_value': self.taxes_id.amount,
            'category': self.categ_id.name,
            'category_id': self.categ_id.id,
            #'variant_id': {val.attribute_id.id: val.id  for val in self.product_template_variant_value_ids},
            #'variant': {val.attribute_id.name: val.name  for val in self.product_template_variant_value_ids},
        }


class PublishProductTemplate(models.Model):
    _inherit = 'product.template'

    sync_with_lara = fields.Boolean(string="synchronize with Laravel",defualt=False, tracking=True)
    
    def to_dict(self):
        product_variants ={}
        for product in self.product_variant_ids:
            product_variants.update({product.id : product.to_dict()})
        return product_variants

    @api.model_create_multi
    def create(self, vals):


        templates =  super(PublishProductTemplate, self).create(vals)

        for temp in templates:
            if temp.sync_with_lara:
                temp.sync_to_lara()
        return templates

    def write(self, vals):
        res = super(PublishProductTemplate, self).write(vals)

        if self.sync_with_lara:
                self.sync_to_lara()
        return res

    #------------------------------------------------------
    #
    # Remember app Key
    #
    #
    #------------------------------------------------------

    def sync_to_lara(self):
        if not self.sync_with_lara:
            return

        url = self.env['ir.config_parameter'].sudo().get_param('laravel_sync_url')
        payload = self.to_dict()
        try:
            payload={
                "id": 0,
                "jsonrpc": "2.0",
                "method": "call",
                "params": {'json_product':payload},
            }


            response = requests.request('POST', url, 
                data=json.dumps(payload).encode(), 
                headers={"Content-Type": "application/json"}, timeout=60)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError("HyperPay: " + _("Could not establish the connection to the API."))
        except requests.exceptions.HTTPError:
            _logger.exception("invalid API request at %s with data %s", url, payload)
            raise ValidationError("Laravel server: " + _("The communication with the API failed."))

        except requests.exceptions.MissingSchema:
            _logger.exception("invalid Url link at %s with data %s", url, payload)
            raise ValidationError("Configuration error: " + _("please set a correct url in setting."))

            # response_content = response.content.decode("utf-8")

            # _logger.info("laravel server response erorr:\n%s", pprint.pformat(response_content))
    
    def product_category(self, cat = None):

        cats = cat.child_id if cat else self.env['product.category'].search([('parent_id','=',False)]) 

        result = []
        for cat in cats:
            result.append({
                'id': cat.id,
                'name': cat.name,
                'product_count': cat.product_count,
                'children':self.product_category(cat),
            })

        return result

    def product_attributes(self):
        attrs = self.env['product.attribute'].search([])
        result = [
                {
                    'id': attr.id,
                    'name':attr.name,
                    'values': [{'id':val.id ,'name':val.name} for val in attr.value_ids]
                }for attr in attrs
            ]
        return result


