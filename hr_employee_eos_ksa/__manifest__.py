# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "Employee EOS",
    'summary': """A module to manahe employees end of service""",
    'description': """
    """,
    'author': 'Business Horizone',
    'category': 'Human Resources',
    'version': '15.2',
    'depends': ['hr_payroll_account','hr_employee_updation'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_eos_view.xml',
        'views/employee_leaving_view.xml',
    ],
    'demo': [
    ],
}
