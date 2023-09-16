# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': "HR Leave Custom",
    'summary': """Leaves extention""",
    'description': """
    """,
    'author': 'Business Horizone',
    'category': 'Human Resources',
    'version': '15.0',
    'depends': ['hr_employee_updation', 'hr_holidays', 'hr_payroll_ksa'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/generate_annual_ticket.xml',
        'wizard/generate_air_allowance_view.xml',
        'wizard/leave_encashment_view.xml',
        'views/annual_ticket_view.xml',
        'views/hr_public_holidays_view.xml',
        'views/hr_leave_view.xml',
    ],
    'demo': [
    ],
}
