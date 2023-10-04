# -*- coding: utf-8 -*-pack
# Part of YoungWings Technologies.See the License file for full copyright and licensing details.
{
    # Product Information 
    'name': 'Purchase Order Automation',
    'category': 'Purchases',
    'version': '15.0.0.1',
    'license': 'OPL-1',
    'sequence': 1,
    'summary': 'The Purchase Order Automation Modules helps to done your purchase order automatically. It has done your vendor bill & incoming shipment automatically',

    # Author
    'author': 'YoungWings Technologies',
    'maintainer': 'YoungWings Technologies',
    'website': 'https://www.youngwingstechnologies.in/',
    'support': 'youngwingstechnologies@gmail.com',

    # Dependencies
    'depends': ['purchase', 'stock'],

    # Views
    'data': ['security/ir.model.access.csv',
             'views/ywt_purchase_order_automation_views.xml',
             'data/auto_cron_ywt_purchase_order_automation.xml',
             'data/ywt_purchase_order_automation_history_sequence.xml',
             'views/ywt_purchase_order_automation_history_views.xml',
             'views/res_partner_views.xml',
             'views/purchase_order_views.xml'
             ],

    # Banner
    'images': ['static/description/banner.png'],

    # Technical
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 17.50,
    'currency': 'USD',

}
