# -*- coding: utf-8 -*-
{
    'name': "Project Letter Of Guarantee (LG)",

    'summary': """Letter Of Guarantee for project""",

    'description': """""",

    'author': "Smart Visions",
    'website': "http://smartvisions.com.sa",

    'category': 'Project',
    'version': '15.1',

    # any module necessary for this one to work correctly
    'depends': ['project', 'account_letter_of_guarantee'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/letter_of_gurantee_views.xml',
        'views/project_views.xml',
    ],
    'installable' : True,
    'application' : False,
}
