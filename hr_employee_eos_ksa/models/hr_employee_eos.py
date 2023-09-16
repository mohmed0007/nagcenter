# -*- coding: utf-8 -*-
# Part of odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.exceptions import UserError


class HrEmployeeEos(models.Model):
    _name = 'hr.employee.eos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "End of Service Indemnity (EOS)"

    EOS_TYPE = [('1', 'Expiration of contract terms, or the parties have agreed to terminate the contract'),
                ('2', 'Termination of the contract by the employer'),
                ('3',
                 'Termination of the contract by the employer for one of the terms and condition stated in Article (80)'),
                ('4', 'Leaving work as a result of force majeure'),
                ('5',
                 'The Worker terminates the laber contract within six monthhs into the marriage contract or three months into brith'),
                ('6', 'The Worker leave work for one of the condition stated in Article (81)'),
                ('7',
                 'Termination of the contract by the worker, or worker has quit work for other reasone not stated in Article 81')]

    EOS_TYPE2 = [('1', 'The worker and employer agree to terminate the contract'),
                 ('2', 'Termination of the contract by the employer'),
                 ('3', 'The resignation of a worker'),
                 ('4',
                  'Termination of the contract by the employer for one of the terms and condition stated in Article (80)'),
                 ('5', 'Leaving work as a result of force majeure'),
                 ('6',
                  'The Worker terminates the laber contract within six monthhs into the marriage contract or three months into brith'),
                 ('7', 'The Worker leave work for one of the condition stated in Article (81)'),
                 ('8',
                  'The worker leave work without submitting his/her resignation, other than the conditions stated in Article 81')]

    def _get_currency(self):
        user = self.env['res.users'].browse(self.env.uid)
        return user.company_id.currency_id.id

    def _calc_payable_eos(self):
        for eos_amt in self:
            eos_amt.payable_eos = (
                                          eos_amt.total_eos + eos_amt.current_month_salary + eos_amt.others + eos_amt.annual_leave_amount) or 0.0

    name = fields.Char('Description', size=128, required=True, readonly=True,
                       states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    eos_date = fields.Date('Date', index=True, required=True, readonly=True,
                           states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
                           default=lambda self: datetime.today().date())
    employee_id = fields.Many2one('hr.employee', "Employee", required=True, readonly=True,
                                  states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    date_of_join = fields.Date(related='employee_id.first_contract_date', type="date", string="Joining Date",
                               store=True, readonly=True)
    date_of_leave = fields.Date(related='employee_id.last_contract_date', type="date", string="Leaving Date",
                                store=True, readonly=True)
    duration_days = fields.Integer('No of Days', readonly=True,
                                   states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    duration_months = fields.Integer('No of Months', readonly=True,
                                     states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    duration_years = fields.Integer('No. of Years', readonly=True,
                                    states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    contract_type = fields.Selection([('limited', 'Limited Period'), ('unlimited', 'Unlimited Period')],
                                     related="employee_id.contract_id.contract_type", store=True)
    eos_type = fields.Selection(EOS_TYPE, 'Type', readonly=True, states={'draft': [('readonly', False)],
                                                                         'confirm': [('readonly', False)]})
    eos_type2 = fields.Selection(EOS_TYPE2, 'Type', readonly=True, states={'draft': [('readonly', False)],
                                                                           'confirm': [('readonly', False)]})
    calc_year = fields.Float('Total Years', readonly=True, states={'draft': [('readonly', False)]})
    payslip_id = fields.Many2one('hr.payslip', 'Payslip', readonly=True)
    current_month_salary = fields.Float('Salary of Current month', readonly=True,
                                        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    others = fields.Float('Others', readonly=True,
                          states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.uid)
    date_confirm = fields.Date('Confirmation Date', index=True, copy=False,
                               help="Date of the confirmation of the sheet expense. It's filled when the button Confirm is pressed.")
    date_valid = fields.Date('Validation Date', index=True, copy=False,
                             help="Date of the acceptation of the sheet eos. It's filled when the button Validate is pressed.",
                             readonly=True)
    date_approve = fields.Date('Approve Date', index=True, copy=False,
                               help="Date of the Approval of the sheet eos. It's filled when the button Approve is pressed.",
                               readonly=True)
    user_valid = fields.Many2one('res.users', 'Validation by', copy=False, readonly=True,
                                 states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, store=True)
    user_approve = fields.Many2one('res.users', 'Approval by', copy=False, readonly=True,
                                   states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
                                   store=True)
    note = fields.Text('Note')
    annual_leave_amount = fields.Float('Leave Balance', readonly=True,
                                       states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    department_id = fields.Many2one('hr.department', "Department", readonly=True)
    job_id = fields.Many2one('hr.job', 'Job', readonly=True)
    contract_id = fields.Many2one('hr.contract', 'Contract', readonly=True,
                                  states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
                                 default=lambda self: self.env.user.company_id)
    state = fields.Selection([('draft', 'New'),
                              ('cancelled', 'Refused'),
                              ('confirm', 'Waiting Approval'),
                              ('validate', 'Validated'),
                              ('accepted', 'Approved'),
                              ('done', 'Done')], 'Status', readonly=True, tracking=True, default='draft',
                             help='When the eos request is created the status is \'Draft\'.\n It is confirmed by the user and request is sent to finance, the status is \'Waiting Confirmation\'.\
        \nIf the finance accepts it, the status is \'Accepted\'.')
    total_eos = fields.Float('Total Award', readonly=True, states={'draft': [('readonly', False)]})
    payable_eos = fields.Float(compute=_calc_payable_eos, string='Total Amount')
    remaining_leave = fields.Float('Remaining Leave')
    # account
    journal_id = fields.Many2one('account.journal', 'Force Journal', help="The journal used when the eos is done.")
    account_move_id = fields.Many2one('account.move', 'Ledger Posting', copy=False)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, readonly=True,
                                  states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
                                  default=_get_currency)
    config_id = fields.Many2one('hr.allocation.accounting.configuration', required=True, string='Configuration')

    @api.model
    def create(self, values):
        if values.get('employee_id'):
            eos_ids = self.env['hr.employee.eos'].search([('employee_id', '=', values.get('employee_id'))])
            if eos_ids:
                raise UserError(_("%s's EOS is already Generated.") % (eos_ids.employee_id.name))
        return super(HrEmployeeEos, self).create(values)

    def write(self, values):
        if values.get('employee_id'):
            eos_ids = self.env['hr.employee.eos'].search([('employee_id', '=', values.get('employee_id'))])
            if eos_ids:
                raise UserError(_("%s's EOS is already in Generated.") % (eos_ids.employee_id.name))
        return super(HrEmployeeEos, self).write(values)

    def unlink(self):
        for record in self:
            if record.state in ['confirm', 'validate', 'accepted', 'done', 'cancelled']:
                raise UserError(_('You cannot remove the record which is in %s state!') % record.state)
        return super(HrEmployeeEos, self).unlink()

    def onchange_currency_id(self):
        journal_ids = self.env['account.journal'].search(
            [('type', '=', 'purchase'), ('currency_id', '=', self.currency_id.id),
             ('company_id', '=', self.company_id.id)], limit=1)
        if journal_ids:
            self.journal_id = journal_ids[0].id

    def calc_eos(self):
        for eos in self:

            diff = relativedelta(eos.date_of_leave, eos.date_of_join)
            duration_days = diff.days
            duration_months = diff.months
            duration_years = diff.years
            eos.write({'duration_days': duration_days, 'duration_months': duration_months,
                       'duration_years': duration_years})
            selected_month = eos.date_of_leave.month
            selected_year = eos.date_of_leave.year
            date_from = date(selected_year, selected_month, 1)
            date_to = date_from + relativedelta(day=eos.date_of_leave.day)

            end_date = eos.contract_id.date_end
            end_date = end_date.replace(day=1)
            worked_days = (eos.contract_id.date_end - end_date).days + 1
            employee_gross_salary_per_day = eos.employee_id.contract_id.gross_amt / 30
            total_days = (duration_years * 360) + (duration_months * 30) + duration_days
            annual_leave_amount = employee_gross_salary_per_day * eos.employee_id.remaining_leaves
            amount = 0.00000

            if not eos.date_of_leave:
                raise UserError(_('Please define employee date of leaving!'))
            elif not eos.employee_id.contract_id:
                raise UserError(_('Please define contract for selected Employee!'))
            elif not eos.journal_id:
                raise UserError(_('Please configure Journal before calculating EOS.'))

            if eos.contract_type == "limited" and eos.eos_type in ['1', '2', '4', '5', '6']:
                from_day = 1
                to_day = 99999
                factor = 1800
                factor_amount = .50000
                for i in range(1, 3):
                    if from_day <= total_days <= to_day:
                        if factor > total_days > 0:
                            amount += (total_days / 12) * (factor_amount * employee_gross_salary_per_day)
                            total_days = 0
                        elif total_days == factor:
                            amount += (factor / 12) * (factor_amount * employee_gross_salary_per_day)
                            total_days = 0
                        elif total_days > factor and total_days > 0:
                            amount += (factor / 12) * (factor_amount * employee_gross_salary_per_day)
                            total_days = total_days - factor
                    factor += 98199
                    factor_amount += .50000
            elif eos.contract_type == "limited" and eos.eos_type in ['3', '7']:
                amount = 0
            elif eos.contract_type == "unlimited" and eos.eos_type2 in ['1', '2', '5', '6', '7']:
                from_day = 1
                to_day = 99999
                factor = 1800
                factor_amount = .50000
                for i in range(1, 3):
                    if from_day <= total_days <= to_day:
                        if factor > total_days > 0:
                            amount += (total_days / 12)(factor_amount * employee_gross_salary_per_day)
                            total_days = 0
                        elif total_days == factor:
                            amount += (factor / 12) * (factor_amount * employee_gross_salary_per_day)
                            total_days = 0
                        elif total_days > factor and total_days > 0:
                            amount += (factor / 12) * (factor_amount * employee_gross_salary_per_day)
                            total_days = total_days - factor
                    factor += 98199
                    factor_amount += .50000
            elif eos.contract_type == "limited" and eos.eos_type in ['4', '8']:
                amount = 0
            elif eos.contract_type == "unlimited" and eos.eos_type2 in ['3'] and total_days > 3600:
                from_day = 1
                to_day = 99999
                factor = 1800
                factor_amount = .50000
                for i in range(1, 3):
                    if from_day <= total_days <= to_day:
                        if factor > total_days > 0:
                            amount += (total_days / 12) * (factor_amount * employee_gross_salary_per_day)
                            total_days = 0
                        elif total_days == factor:
                            amount += (factor / 12) * (factor_amount * employee_gross_salary_per_day)
                            total_days = 0
                        elif total_days > factor and total_days > 0:
                            amount += (factor / 12) * (factor_amount * employee_gross_salary_per_day)
                            total_days = total_days - factor
                    factor += 98199
                    factor_amount += .50000
            elif eos.contract_type == "unlimited" and eos.eos_type2 in ['3'] and total_days <= 3600:
                from_day = 1
                to_day = 720
                to_day1 = 1800
                to_day2 = 3600
                factor = 720
                factor1 = 1800
                factor_amount = 0
                factor_amount1 = .1666666666
                factor_amount2 = .3333333333
                factor_amount3 = .6666666666
                for i in range(1, 5):
                    if i == 1:
                        if from_day <= total_days <= to_day:
                            if factor > total_days > 0:
                                amount += (total_days / 12) * (factor_amount * employee_gross_salary_per_day)
                                total_days = 0
                            elif total_days == factor:
                                amount += (factor / 12) * (factor_amount * employee_gross_salary_per_day)
                                total_days = 0
                            elif total_days > factor and total_days > 0:
                                amount += (factor / 12) * (factor_amount * employee_gross_salary_per_day)
                                total_days = total_days - factor
                    elif i == 2:
                        if from_day <= total_days <= to_day1:
                            if factor1 > total_days > 0:
                                amount += (total_days / 12) * (factor_amount1 * employee_gross_salary_per_day)
                                total_days = 0
                            elif total_days == factor1:
                                amount += (factor1 / 12) * (factor_amount1 * employee_gross_salary_per_day)
                                total_days = 0
                            elif total_days > factor1 and total_days > 0:
                                amount += (factor1 / 12) * (factor_amount1 * employee_gross_salary_per_day)
                                total_days = total_days - factor1
                    elif i == 3:
                        if from_day <= total_days <= to_day2:
                            if factor1 > total_days > 0:
                                amount += (total_days / 12) * (factor_amount2 * employee_gross_salary_per_day)
                                total_days = 0
                            elif total_days == factor1:
                                amount += (factor1 / 12) * (factor_amount2 * employee_gross_salary_per_day)
                                total_days = 0
                            elif total_days > factor1 and total_days > 0:
                                amount += (factor1 / 12) * (factor_amount2 * employee_gross_salary_per_day)
                                total_days = total_days - factor1
                    else:
                        if from_day <= total_days <= to_day2:
                            if factor1 > total_days > 0:
                                amount += (total_days / 12) * (factor_amount3 * employee_gross_salary_per_day)
                                total_days = 0
                            elif total_days == factor1:
                                amount += (factor1 / 12) * (factor_amount3 * employee_gross_salary_per_day)
                                total_days = 0
                            elif total_days > factor1 and total_days > 0:
                                amount += (factor1 / 12) * (factor_amount3 * employee_gross_salary_per_day)
                                total_days = total_days - factor1

            eos.write({'current_month_salary': (eos.employee_id.contract_id.gross_amt / 30) * worked_days})
            eos.write({'total_eos': amount, 'annual_leave_amount': annual_leave_amount,
                       'remaining_leave': eos.employee_id.remaining_leaves})
            return True

    @api.onchange('employee_id', 'eos_date')
    def onchange_employee_id(self):
        if self.employee_id:
            if not self.employee_id.first_contract_date:
                raise UserError(_('Please define employee date of Join!'))
            if not self.employee_id.last_contract_date:
                raise UserError(_('Please define employee date of Leave!'))
            selected_date = self.employee_id.last_contract_date
            date_from = date(selected_date.year, selected_date.month, 1)
            date_to = date_from + relativedelta(day=selected_date.day)
            if not self.employee_id.contract_id:
                raise UserError(_('Please define contract for selected Employee!'))
            calc_years = round(
                ((self.employee_id.last_contract_date - self.employee_id.first_contract_date).days / 365.0), 2)
            diff = relativedelta(self.employee_id.last_contract_date,
                                               self.employee_id.first_contract_date)
            self.contract_id = self.employee_id.contract_id
            self.date_of_leave = self.employee_id.last_contract_date
            self.date_of_join = self.employee_id.first_contract_date
            self.calc_year = calc_years
            self.department_id = self.employee_id.department_id.id or False
            self.company_id = self.employee_id.company_id.id or False
            self.job_id = self.employee_id.sudo().job_id.id or False
            self.duration_years = diff.years or 0
            self.duration_months = diff.months or 0
            self.duration_days = diff.days or 0

    def eos_confirm(self):
        self.ensure_one()
        self.write({'state': 'confirm',
                    'date_confirm': time.strftime('%Y-%m-%d')})
        self.message_post(message_type="email", subtype_xmlid='mail.mt_comment', body=_('EOS Confirmed.'))

    def eos_validate(self):
        self.ensure_one()
        for record in self:
            record.calc_eos()
            partner_ids = []
            if record.employee_id.parent_id.user_id:
                partner_ids.append(record.employee_id.parent_id.user_id.partner_id.id)
            record.message_subscribe(partner_ids=partner_ids)
        self.write({'state': 'validate',
                    'date_valid': time.strftime('%Y-%m-%d'),
                    'user_valid': self.env.uid})
        self.message_post(message_type="email", subtype_xmlid='mail.mt_comment', body=_('EOS Validated.'))

    def eos_accept(self):
        self.ensure_one()
        self.write({'state': 'accepted',
                    'date_approve': time.strftime('%Y-%m-%d'),
                    'user_approve': self.env.uid})
        self.message_post(message_type="email", subtype_xmlid='mail.mt_comment', body=_('EOS Approved.'))

    def eos_cancelled(self):
        self.ensure_one()
        self.state = 'cancelled'
        self.message_post(message_type="email", subtype_xmlid='mail.mt_comment', body=_('EOS Cancelled.'))

    def eos_draft(self):
        self.ensure_one()
        self.state = 'draft'
        self.message_post(message_type="email", subtype_xmlid='mail.mt_comment', body=_('EOS Draft.'))

    def action_receipt_create(self):
        for eos in self:
            if not eos.employee_id.address_home_id:
                raise UserError(_('The employee must have a home address.'))
            if not eos.employee_id.address_home_id.property_account_payable_id.id:
                raise UserError(_('The employee must have a payable account set on his home address.'))
            company_currency = eos.company_id.currency_id.id
            diff_currency_p = eos.currency_id.id != company_currency
            eml = []
            if not eos.journal_id:
                raise UserError(_('Please configure employee EOS for journal.'))
            timenow = time.strftime('%Y-%m-%d')
            amount = 0.0
            amount -= eos.payable_eos
            eos_name = eos.name.split('\n')[0][:64]
            reference = eos.name
            journal_id = eos.journal_id.id
            debit_account_id = eos.config_id.end_service_allocation_acc_id.id
            credit_account_id = eos.journal_id.default_account_id.id
            if not debit_account_id:
                raise UserError(_("Please configure %s journal's debit account.") % eos.journal_id.name)
            debit_vals = {
                'name': eos_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'partner_id': eos.employee_id.address_home_id.id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                'analytic_account_id': eos.contract_id.analytic_account_id.id or False,
            }
            credit_vals = {
                'name': eos_name,
                'account_id': debit_account_id,
                'partner_id': eos.employee_id.address_home_id.id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                'analytic_account_id': eos.contract_id.analytic_account_id.id or False,
            }
            vals = {
                'name': '/',
                'narration': eos_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            self.write({'account_move_id': move.id, 'state': 'done'})

    def action_view_receipt(self):
        assert len(self.ids) == 1, 'This option should only be used for a single id at a time'
        self.ensure_one()
        assert self.account_move_id
        try:
            dummy, view_id = self.env['ir.model.data'].get_object_reference('account', 'view_move_form')
        except ValueError:
            view_id = False
        result = {
            'name': _('EOS Account Move'),
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': self.account_move_id.id,
        }
        return result
