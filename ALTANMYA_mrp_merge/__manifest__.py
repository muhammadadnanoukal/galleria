# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'ALTANMYA MRP Merge',
    'version': '1.0',
    'summary': 'Tanmya MRP Merge',
    'author': 'ALTANMYA - TECHNOLOGY SOLUTIONS',
    'company': 'ALTANMYA - TECHNOLOGY SOLUTIONS Part of ALTANMYA GROUP',
    'website': "http://tech.altanmya.net",
    'category': 'Manufacturing/Manufacturing',
    'depends': ['mrp', 'stock', 'sale_product_configurator', 'sale'],
    'description': "ALTANMAY MRP Merge",
    'data': [
        'views/mrp_production_views.xml',
        'views/sale_order_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3'
}