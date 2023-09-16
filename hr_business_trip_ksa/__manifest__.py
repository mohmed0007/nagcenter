# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Business Trip",
    'summary': """A module to manage hr business trips.""",
    'description': """
    """,
    'author': 'Business Horizone',
    'category': 'Human Resources',
    'version': '15.0',
    'depends': ['hr_employee_updation', 'hr_payroll_ksa'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'wizard/business_trip_payment_view.xml',
        'views/business_trip_view.xml',
    ],
    'demo': [
    ],
}
