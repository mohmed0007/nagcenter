# -*- coding: utf-8 -*-


{
    "name": "HR Portal",
    "version": "15.0.0.1",
    "author": "ME",
    "description": "",
    "depends": ['portal', 'website', 'hr', 'hr_holidays',],
    "data": [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/hr_self_service_template.xml',
        'views/portal.xml',
    ],

    'qweb': [],
    'installable': True,
    'application': True,
}
