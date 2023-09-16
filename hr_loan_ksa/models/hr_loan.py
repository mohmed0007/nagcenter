# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.total_amount = loan.loan_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    name = fields.Char(string="Reference", default="/", readonly=True, help="Name of the loan")
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee")
    job_id = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position",
                                   help="Job position")
    branch_id = fields.Many2one('hr.branch', related="employee_id.branch_id", readonly=True, string="Branch")
    installment = fields.Integer(string="No of Installments", default=1, help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today(), help="Date of the paymemt")
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    loan_amount = fields.Float(string="Loan Amount", required=True, help="Loan amount")
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_loan_amount',
                                help="Total loan amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_loan_amount', help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True, compute='_compute_loan_amount',
                                     help="Total paid amount")
    payment_done = fields.Boolean('Loan Amount Given', default=False)
    account_move_id = fields.Many2one('account.move', 'Account move', copy=False , readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Submitted'),
        ('waiting_approval_2', 'Waiting Finance Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', tracking=True, copy=False)

    @api.model
    def create(self, values):
        loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
            ('balance_amount', '!=', 0)])
        if loan_count:
            raise ValidationError(_("The employee has already a pending installment"))
        else:
            values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
            res = super(HrLoan, self).create(values)
            return res

    def compute_installment(self):
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
            loan._compute_loan_amount()
        return True

    def action_refuse(self):
        self.state = 'refuse'

    def action_submit(self):
        self.state = 'waiting_approval'

    def action_cancel(self):
        self.state = 'cancel'

    def action_double_approve(self):
        self.state = 'waiting_approval_2'

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.state = 'approve'

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError('You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()

    def action_loan_payment(self):
        return {
            'name': _('Register Loan Payment'),
            'type': 'ir.actions.act_window',
            'context': {'default_loan_id': self.id},
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.loan.payment',
            'view_id': self.env.ref('hr_loan_ksa.view_hr_loan_payment_form').id,
            'target': 'new',
        }

    def action_loan_reschedule(self):
        return {
            'name': _('Loan Reschedule'),
            'type': 'ir.actions.act_window',
            'context': {'default_loan_id': self.id},
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.loan.reschedule',
            'view_id': self.env.ref('hr_loan_ksa.view_hr_loan_reschedule_form').id,
            'target': 'new',
        }


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")
    employee_id = fields.Many2one('hr.employee', related='loan_id.employee_id', store=True,
        string="Employee", help="Employee")
    loan_state = fields.Selection(related='loan_id.state', store=True, string="Status")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid", default=False)
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Payslip")

