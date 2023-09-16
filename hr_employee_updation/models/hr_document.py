# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _


class HRDocumentType(models.Model):
    _name = 'hr.document.type'
    _description = 'Document Type'

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
    notification_days = fields.Integer('Notification Days', default=30, required=True)

    _sql_constraints = [
        ('code', 'unique(code)', 'Code must be unique per Document!'),
    ]


class HRDocument(models.Model):
    _name = 'hr.document'
    _inherit = ['mail.thread']
    _description = 'HR Document'

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        return employee

    type_id = fields.Many2one('hr.document.type', 'Type')
    name = fields.Char('Number', required=True)
    issue_date = fields.Date('Date of Issue', tracking=True)
    expiry_date = fields.Date('Date of Expiry', tracking=True)
    notes = fields.Text('Notes')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=_default_employee_id)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('issue', 'Issued'),
            ('refuse', 'Refused'),
            ('renew', 'Renew'),
            ('expiry', 'Expiry')], string='Status', readonly=True, copy=False, default='draft', tracking=True)

    @api.model
    def run_scheduler(self):
        today = fields.Date.today()
        for document in self.search([('state', '=', 'issue')]):
            if document.expiry_date and document.employee_id.user_id:
                notification_days = document.type_id.notification_days
                notification_date = (document.expiry_date - relativedelta(days=+notification_days))
                if today == notification_date:
                    try:
                        template_id = self.env.ref('hr_employee_updation.email_template_hr_document_notify')
                    except ValueError:
                        template_id = False
                    email_to = ''
                    user = document.employee_id.user_id
                    if user.email:
                        email_to = email_to and email_to + ',' + user.email or email_to + user.email
                    template_id.write({'email_to': email_to, 'reply_to': email_to, 'auto_delete': False})
                    template_id.send_mail(document.id, force_send=True)
            if document.expiry_date and document.expiry_date == today:
                document.state = 'expiry'
                try:
                    template_id = self.env.ref('hr_employee_updation.email_template_hr_document_expire')
                except ValueError:
                    template_id = False
                if template_id:
                    template_id.send_mail(document.id, force_send=True, raise_exception=False, email_values=None)
        return True

    def set_draft(self):
        for record in self:
            record.state = 'draft'

    def _add_followers(self):
        partner_ids = []
        if self.employee_id.user_id:
            partner_ids.append(self.employee_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)

    def document_submit(self):
        for record in self:
            record.state = 'confirm'

    def document_issue(self):
        for record in self:
            if not record.issue_date:
                record.issue_date = datetime.today()
            record.state = 'issue'

    def document_refuse(self):
        for record in self:
            record.state = 'refuse'

    def document_renew(self):
        self.write({'state': 'renew',
                    'expiry_date': False,
                    'issue_date': False})