# -*- coding: utf-8 -*-

{
    'name': "HR Employee Effective",
    'summary': """Empoyee effective after leave""",
    'description': """
    """,
    'author': 'Business Horizone',
    'category': 'Human Resources',
    'version': '15.0',
    'depends': ['hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/effective_request_view.xml',
    ],
    'demo': [
    ],
}
