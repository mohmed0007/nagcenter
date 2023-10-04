# -*- coding: utf-8 -*-
{
    'name': "Petty Cash",

    'summary': """
        Managing the Petty cash  and its relation to the tax, clearing the expenses 
        related to the petty cash and payments to the vendors’s bills""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.afag.odoo.com/",


    'category': 'Accounting',
    'version': '15.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/views.xml', 
        'views/partner_view_custom.xml',
        'wizard/template_ohad.xml',
        'views/templates.xml',
        'wizard/wizard.xml',
        'wizard/wizard_ohad_balance.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
