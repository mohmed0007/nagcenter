# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Loan",
    'summary': """A module to manage employee loan""",
    'description': """
    """,
    'author': 'Business Horizone',
    'category': 'Human Resources',
    'version': '15.0',
    'depends': ['hr_payroll_ksa', 'hr_employee_updation'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'wizard/hr_loan_payment_view.xml',
        'views/hr_payroll.xml',
        'views/hr_loan.xml',
    ],
    'demo': [
    ],
}
