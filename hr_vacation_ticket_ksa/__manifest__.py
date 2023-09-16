# -*- coding: utf-8 -*-
###################################################################################

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
    'name': "Vacation Management",
    'version': '14.0.1.0.0',
    'summary': """Vacation Management,manages employee vacation""",
    'description': """HR Vacation management""",
    'author': 'Unknown',
    'company': 'Snit',
    'website': 'Unknown',
    'category': 'Generic Modules/Human Resources',
    'depends': [  'account', 'hr_payroll','hr_holidays'],
    'data': [
        # 'security/hr_vacation_security.xml',
        'security/ir.model.access.csv',
        'views/country_ticket.xml',
        'views/ticket_request_seq.xml',
        'views/hr_employee_ticket.xml',
        'views/ticket_allocation.xml',
        'views/res_config_setting.xml',
        'views/hr_account_wizard_sync.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
