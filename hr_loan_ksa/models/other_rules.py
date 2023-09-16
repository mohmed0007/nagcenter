# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time


class OtherRules(models.Model):
    _name = 'other.rules'
    _inherit = ['mail.thread']
    _description = "Other Rules"

    name = fields.Char(related='employee_id.name')
    amount = fields.Float('Amount')
    no_of_days = fields.Float('No of Days')
    operation_type = fields.Selection([('allowance', 'Allowance'), ('deduction', 'Deduction')],
                                      string='Type', default='allowance', required=True)
    date = fields.Date('Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    description = fields.Text('Description', required=True)
    approved_date_to = fields.Date('Approved Date To', copy=False)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], string='State', default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.user.company_id)

    def unlink(self):
        for line in self:
            if line.state in ['done']:
                raise UserError(_('You cannot remove the record which is in %s state!') % line.state)
        return super(OtherRules, self).unlink()

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.department_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id

    def other_hr_payslip_done(self):
        for rec in self:
            rec.state = 'done'

    def set_draft(self):
        for rec in self:
            rec.state = 'draft'
