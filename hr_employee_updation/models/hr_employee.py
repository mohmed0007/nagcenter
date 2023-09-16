# -*- coding: utf-8 -*-
###################################################################################
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
from datetime import datetime, timedelta
from odoo import models, fields, _, api

GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.family'
    _description = 'HR Employee Family'

    employee_id = fields.Many2one('hr.employee', string="Employee", help='Select corresponding Employee',
                                  invisible=1)
    relation_id = fields.Many2one('hr.employee.relation', string="Relation", help="Relationship with the employee")
    member_name = fields.Char(string='Name')
    member_contact = fields.Char(string='Contact No')
    birth_date = fields.Date(string="DOB", tracking=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        """Sending expiry date notification for ID and Passport"""

        now_time = datetime.today() + timedelta(days=1)
        date_now = now_time.date()
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                if date_now >= exp_date1:
                    mail_content = "  Hello  " + i.name + ",<br>Your Passport " + i.passport_id + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    personal_mobile = fields.Char(string='Mobile', related='address_home_id.mobile', store=True,
                  help="Personal mobile number of the employee")
    joining_date = fields.Date(string='Joining Date', help="Employee joining date computed from the contract start date",compute='compute_joining', store=True)
    id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Passport ID')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
                                        string="Attachment", help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1',
                                              string="Attachment",
                                              help='You can attach the copy of Passport')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information')
    grade_id = fields.Many2one('hr.grade', 'Grade')
    branch_id = fields.Many2one('hr.branch', 'Branch')
    adults = fields.Integer(string='Number of Adults', default=1, groups="hr.group_hr_user", tracking=True)
    last_contract_date = fields.Date(compute='_compute_last_contract_date', groups="hr.group_hr_user")
    document_ids = fields.One2many('hr.document', 'employee_id', 'Personal Docs')
    documents_count = fields.Integer(string='Documents', compute='_compute_documents')

    @api.depends('contract_ids.state', 'contract_ids.date_end', 'contract_ids.date_start')
    def _compute_last_contract_date(self):
        for employee in self:
            contracts = self.env['hr.contract'].sudo().search([('id', 'in', employee.contract_ids.ids)],
                                                              order='date_start desc')
            if contracts and max(contracts).date_end:
                employee.last_contract_date = contracts[0].date_end
                print(contracts[0].date_end, "Osmakjkjkd" * 3)
            else:
                employee.last_contract_date = False

    def _compute_documents(self):
        for employee in self:
            documents = self.env['hr.document'].search([('employee_id', '=', employee.id)])
            employee.documents_count = len(documents) if documents else 0

    @api.model
    def get_employee(self):
        employee_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return employee_ids[0] if employee_ids else False

    @api.onchange('job_id')
    def onchange_job_id(self):
        self.grade_id = self.job_id.grade_id

    def action_documents(self):
        self.ensure_one()
        tree_view = self.env.ref('hr_employee_updation.hr_document_view_tree')
        form_view = self.env.ref('hr_employee_updation.hr_document_view_form')
        context = {'default_employee_id': self.id}
        return {'type': 'ir.actions.act_window',
                'name': _('Documents'),
                'res_model': 'hr.document',
                'view_mode': 'tree',
                'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
                'domain': [('employee_id', '=', self.id)],
                'res_id': self.document_ids.ids and self.document_ids.ids[0] or False,
                'context': context,
                }

    @api.depends('contract_id')
    def compute_joining(self):
        if self.contract_id:
            date = min(self.contract_id.mapped('date_start'))
            self.joining_date = date
        else:
            self.joining_date = False

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def onchange_spouse(self):
        relation = self.env.ref('hr_employee_updation.employee_relationship')
        lines_info = []
        spouse_name = self.spouse_complete_name
        date = self.spouse_birthdate
        if spouse_name and date:
            lines_info.append((0, 0, {
                'member_name': spouse_name,
                'relation_id': relation.id,
                'birth_date': date,
            })
                              )
            self.fam_ids = [(6, 0, 0)] + lines_info


class EmployeeRelationInfo(models.Model):
    """Table for keep employee family information"""
    _name = 'hr.employee.relation'

    name = fields.Char(string="Relationship", help="Relationship with thw employee")


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    grade_id = fields.Many2one('hr.grade', 'Grade')
    branch_id = fields.Many2one('hr.branch', 'Branch')


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    grade_id = fields.Many2one('hr.grade', 'Grade', readonly=True)
    branch_id = fields.Many2one('hr.branch', 'Branch', readonly=True)

