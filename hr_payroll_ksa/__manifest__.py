# -*- coding: utf-8 -*-

{
    'name': "HR Payroll Custom",
    'summary': """HR Payroll Custom""",
    'description': """
    """,
    'author': 'Business Horizone',
    'category': 'Human Resources',
    'version': '15.0',
    'depends': ['hr_employee_updation', 'hr_payroll', 'hr_payroll_account','hr_effective_request_ksa'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/hr_payroll_data.xml',
        'views/hr_payroll.xml',
        'views/other_rules.xml',
        'views/flight_view.xml',
    ],
    'demo': [
    ],
}
