# -*- coding: utf-8 -*-
{
    'name': "HR Letter Request",
    'summary': """Letter request management module""",
    'description': """
    """,
    'author': 'Business Horizone',
    'category': 'Human Resources',
    'version': '15.0',
    'depends': ['hr_employee_updation'],
    'data': [
        'security/ir.model.access.csv',

        'data/sequence.xml',
        'data/salary_introduction_report_template.xml',
        'data/salary_transfer_report_template.xml',
        'data/letter_of_authority_report_template.xml',
        'data/experience_certificate_report_template.xml',

        'report/salary_introduction_template.xml',
        'report/salary_transfer_template.xml',
        'report/letter_of_authority_template.xml',
        'report/experience_certificate_template.xml',
        'report/report_action.xml',

        'views/service_request_view.xml',
        'views/res_config_settings.xml',

    ],
    'demo': [
    ],
}
