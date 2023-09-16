# -*- coding: utf-8 -*-
###################################################################################
#
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Employee Info',
    'version': '15.0',
    'summary': """Adding Advanced Fields In Employee Master""",
    'description': 'This module helps you to add more information in employee records.',
    'category': 'Human Resources',
    'author': 'ُEra Group',
    'company': 'Era Group',
    'website': "https://era.net.sa",
    'depends': ['hr', 'hr_gamification', 'mail', 'hr_contract', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'data/document_data.xml',
        'views/updation_config.xml',
        'views/hr_document_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_branch_view.xml',
        'views/hr_grade_view.xml',
        'views/hr_visa_view.xml',
        'views/transfer_employee_view.xml',
        'views/hr_notification.xml',
        'report/transfer_employee_report.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
