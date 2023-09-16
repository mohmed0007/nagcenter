# -*- coding: utf-8 -*-
{
    'name': "Letter Of Guarantee (LG)",

    'summary': """Letter Of Guarantee""",

    'description': """""",

    'author': "",
    'website': "",

    'category': 'Account',
    'version': '15.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'account_asset'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/res_config_settings_views.xml',
        'views/letter_of_gurantee_views.xml',
    ],
    'installable' : True,
    'application' : False,
}
