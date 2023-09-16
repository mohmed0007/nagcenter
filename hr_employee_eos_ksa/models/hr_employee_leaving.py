# -*- coding: utf-8 -*-
# Part of odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

leaving_states = [('draft', 'Draft'),
                  ('confirm', 'Waiting Approval'),
                  ('approve', 'Approved'),
                  ('validate', 'Validated'),
                  ('refuse', 'Refused')]


class HREmployeeLeaving(models.Model):
    _name = "hr.employee.leaving"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "HR Employee Leaving"

    def unlink(self):
        for record in self:
            if record.state in ['confirm', 'validate', 'approve', 'refuse']:
                raise UserError(_('You cannot remove the record which is in %s state!') % record.state)
        return super(HREmployeeLeaving, self).unlink()

    @api.constrains('notice_start_date', 'requested_date')
    def _check_start_date(self):
        for rec in self:
            if rec.notice_start_date and rec.requested_date and rec.notice_start_date <= rec.requested_date:
                raise ValidationError(_("Notice Start Date must be greater than Requested Date"))

    @api.constrains('notice_end_date', 'notice_start_date')
    def _check_end_date(self):
        for rec in self:
            if rec.notice_end_date and rec.notice_start_date and rec.notice_end_date < rec.notice_start_date:
                raise ValidationError(_("Notice End Date must be greater than Notice Start Date"))

    @api.constrains('exit_date', 'notice_end_date')
    def _check_exit_date(self):
        for rec in self:
            if rec.notice_end_date and rec.exit_date and rec.exit_date < rec.notice_end_date:
                raise ValidationError(_("Exit Date must be greater than Notice End Date"))

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    department_id = fields.Many2one('hr.department', 'Department', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    reason = fields.Char('Reason', size=128, required=True)
    requested_date = fields.Date('Requested Date', default=datetime.strftime(datetime.now(), '%Y-%m-%d'))
    notice_start_date = fields.Date('Notice Start Date')
    notice_end_date = fields.Date('Notice End Date')
    exit_date = fields.Date('Exit Date', compute='compute_exit_date', store=True)
    contact_person = fields.Many2one('res.users', 'Contact Person' , )
    description = fields.Text('Description', required=True)
    state = fields.Selection(leaving_states, 'Status', tracking=True, default='draft')
    approved_date = fields.Datetime('Approved Date', readonly=True, tracking=True, copy=False)
    approved_by = fields.Many2one('res.users', 'Approved By', readonly=True, tracking=True, copy=False)
    refused_by = fields.Many2one('res.users', 'Refused By', readonly=True, tracking=True, copy=False)
    refused_date = fields.Datetime('Refused Date', readonly=True, tracking=True, copy=False)
    applied_on_contract = fields.Boolean("Apply on Contract", default=False, copy=False, tracking=True)

    def name_get(self):
        res = []
        for leave in self:
            name = leave.employee_id.name or ''
            res.append((leave.id, name))
        return res

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.department_id = self.employee_id.department_id.id or False
        self.company_id = self.employee_id.company_id.id or False

    @api.onchange('notice_start_date')
    def onchange_notice_start_date(self):
        if self.notice_start_date:
            self.notice_end_date = self.notice_start_date + timedelta(days=60)

    @api.depends('notice_end_date')
    def compute_exit_date(self):
        for rec in self:
            rec.exit_date = rec.notice_end_date or False

    def leaving_confirm(self):
        self.ensure_one()
        self.state = 'confirm'

    def leaving_approve(self):
        self.ensure_one()
        today = datetime.today()
        if self.employee_id and self.applied_on_contract:
            contract_ids = self.employee_id._get_contracts(self.notice_start_date, self.notice_end_date, states=['open'])
            #print ("contract_ids:::", contract_ids)
            if contract_ids:
                contract_ids[0].date_end = self.notice_end_date
                #contract_ids.write({'notice_start_date': self.notice_start_date or False, 'notice_end_date': self.notice_end_date or False, 'is_leaving': True})
        self.write({'state': 'approve',
                    'approved_by': self.env.uid,
                    'approved_date': today})
        
    def leaving_validate(self):
        self.ensure_one()
        self.state = 'validate'

    def leaving_refuse(self):
        self.ensure_one()
        self.write({'state': 'refuse',
                    'refused_by': self.env.uid,
                    'refused_date': datetime.today()})

    def set_draft(self):
        self.ensure_one()
        self.state = 'draft'
