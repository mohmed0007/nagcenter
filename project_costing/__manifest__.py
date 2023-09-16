# -*- coding: utf-8 -*-
{
    'name': "Project Budet",

    'summary': """Track Project Budget""",

    'description': """""",

    'author': "My Company",
    'website': "http://www.yourcompany.com",


    'category': 'Project',
    'version': '15',

    'depends': ['account','project','stock_account','purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/project_cost_security.xml',
        'data/sequence_data.xml',
        'views/project_budget_views.xml',
        'views/project_budget_template_views.xml',
        'views/stock_views.xml',
        'views/project_budget_operation_views.xml',
        'views/purchase_views.xml',
        'views/res_config_views.xml',
        'views/project_views.xml',
    ],
}
