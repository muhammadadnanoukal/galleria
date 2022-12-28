# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Product Publisher',
    'version' : '0.0.1',
    'summary': 'Publish product to laravel e-commerce site',
    'sequence': -50,
    'description':'',
    'category': 'Accounting/Accounting',
    'website': 'https://www.odoo.com/app/invoicing',
    'images' : [],
    'depends' : ['product','stock'],
    'data': [
        'views/product_view.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'assets': {},
    'license': 'LGPL-3',
}
