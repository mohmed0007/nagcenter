# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
from collections import defaultdict

from babel.dates import format_date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    input_line_ids = fields.One2many(compute='_compute_input_line_ids', store=True, readonly=False,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    loan_line_ids = fields.One2many(
        'hr.loan.line', 'payslip_id', string='Loan Installment',
        help="Loan Installment to employee.",
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    installment_count = fields.Integer(compute='_compute_installment_count')

    @api.depends('loan_line_ids', 'loan_line_ids.payslip_id')
    def _compute_installment_count(self):
        for payslip in self:
            payslip.installment_count = len(payslip.loan_line_ids.ids)

    @api.onchange('input_line_ids')
    def _onchange_input_line_ids(self):
        loan_type = self.env.ref('hr_loan_ksa.hr_rule_input_loan', raise_if_not_found=False)
        if not self.input_line_ids.filtered(lambda line: line.input_type_id == loan_type):
            self.loan_line_ids.write({'payslip_id': False})

    @api.depends('loan_line_ids')
    def _compute_input_line_ids(self):
        loan_type = self.env.ref('hr_loan_ksa.hr_rule_input_loan', raise_if_not_found=False)
        for payslip in self:
            total = sum(payslip.loan_line_ids.mapped('amount'))
            if not total or not loan_type:
                payslip.input_line_ids = payslip.input_line_ids
                continue
            lines_to_keep = payslip.input_line_ids.filtered(lambda x: x.input_type_id != loan_type)
            input_lines_vals = [(5, 0, 0)] + [(4, line.id, False) for line in lines_to_keep]
            input_lines_vals.append((0, 0, {
                'amount': total,
                'input_type_id': loan_type.id,
            }))
            payslip.update({'input_line_ids': input_lines_vals})

    def get_other_allowance_deduction(self, employee_id, date_from, date_to):
        domain = [('employee_id', '=', employee_id.id), ('state', '=', 'done'),
                  ('date', '>=', date_from), ('date', '<=', date_to)]
        other_ids = self.env['other.rules'].search(domain)
        res = []
        if other_ids:
            alw_amt = 0.0
            ded_amt = 0.0
            for other in other_ids:
                if other.operation_type == 'allowance':
                    alw_amt += other.amount
                elif other.operation_type == 'deduction':
                    ded_amt += other.amount

            if alw_amt > 0:
                res.append({'code': 'OTHER_ALLOWANCE_AMOUNT', 'amount': alw_amt})
            if ded_amt > 0:
                res.append({'code': 'OTHER_DEDUCTION_AMOUNT', 'amount': ded_amt})
        return res

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        # res = super()._onchange_employee()
        for rec in self:
            other_types = {
                'OTHER_ALLOWANCE_AMOUNT': self.env.ref('hr_payroll_ksa.other_allowance_input').id,
                'OTHER_DEDUCTION_AMOUNT': self.env.ref('hr_payroll_ksa.other_deduction_input').id,
            }
            if not rec.contract_id:
                lines_to_remove = rec.input_line_ids.filtered(lambda x: x.input_type_id.id in other_types.values())
                rec.update({'input_line_ids': [(3, line.id, False) for line in lines_to_remove]})

            other_allowance_data = rec.get_other_allowance_deduction(rec.employee_id, rec.date_from, rec.date_to)
            if other_allowance_data:
                lines_to_keep = rec.input_line_ids.filtered(lambda x: x.input_type_id.id not in other_types.values())
                input_line_vals = [(5, 0, 0)] + [(4, line.id, False) for line in lines_to_keep]

                for other_type in other_allowance_data:
                    if other_types.get(other_type['code']):
                        input_line_vals.append((0, 0, {
                            'amount': other_type['amount'],
                            'input_type_id': other_types[other_type['code']],
                        }))
                rec.update({'input_line_ids': input_line_vals})

            #Loan
            if rec.state == 'draft':
                rec.loan_line_ids = rec.env['hr.loan.line'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('loan_state', '=', 'approve'), ('paid', '!=', True), ('date', '<=', rec.date_to),
                    ('date', '>=', rec.date_from)])
        # return res

    def action_payslip_done(self):
        for line in self.loan_line_ids:
            if line.loan_id:
                line.paid = True
                line.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()

    def open_loan(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Installment'),
            'res_model': 'hr.loan',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.mapped('loan_line_ids.loan_id').ids)],
        }

    def _action_create_account_move(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        # Add payslip without run
        payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
        for run in payslip_runs:
            if run._are_payslips_ready():
                payslips_to_post |= run.slip_ids

        # A payslip need to have a done state and not an accounting move.
        payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

        # Check that a journal exists on all the structures
        if any(not payslip.struct_id for payslip in payslips_to_post):
            raise ValidationError(_('One of the contract for these payslips has no structure type.'))
        if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
            raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        # Map all payslips by structure journal and pay slips month.
        # {'journal_id': {'month': [slip_ids]}}
        slip_mapped_data = {slip.struct_id.journal_id.id: {fields.Date().end_of(slip.date_to, 'month'): self.env['hr.payslip']} for slip in payslips_to_post}
        for slip in payslips_to_post:
            slip_mapped_data[slip.struct_id.journal_id.id][fields.Date().end_of(slip.date_to, 'month')] |= slip

        for journal_id in slip_mapped_data: # For each journal_id.
            for slip_date in slip_mapped_data[journal_id]: # For each month.
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                date = slip_date
                move_dict = {
                    'narration': '',
                    'ref': date.strftime('%B %Y'),
                    'journal_id': journal_id,
                    'date': date,
                }

                for slip in slip_mapped_data[journal_id][slip_date]:
                    move_dict['narration'] += slip.number or '' + ' - ' + slip.employee_id.name or ''
                    move_dict['narration'] += '\n'
                    for line in slip.line_ids.filtered(lambda line: line.category_id):
                        amount = -line.total if slip.credit_note else line.total
                        #if line.code == 'NET': # Check if the line is the 'Net Salary'.
                        #    for tmp_line in slip.line_ids.filtered(lambda line: line.category_id):
                        #        if tmp_line.salary_rule_id.not_computed_in_net: # Check if the rule must be computed in the 'Net Salary' or not.
                        #            if amount > 0:
                        #                amount -= abs(tmp_line.total)
                        #            elif amount < 0:
                        #                amount += abs(tmp_line.total)
                        if float_is_zero(amount, precision_digits=precision):
                            continue
                        debit_account_id = line.salary_rule_id.account_debit.id
                        credit_account_id = line.salary_rule_id.account_credit.id

                        if debit_account_id: # If the rule has a debit account.
                            debit = amount if amount > 0.0 else 0.0
                            credit = -amount if amount < 0.0 else 0.0
                        
                            debit_line = self._get_existing_lines(
                                line_ids, line, debit_account_id, debit, credit)

                            if not debit_line:
                                debit_line = self._prepare_line_values(line, debit_account_id, date, debit, credit)
                                line_ids.append(debit_line)
                            else:
                                debit_line['debit'] += debit
                                debit_line['credit'] += credit
                        
                        if credit_account_id: # If the rule has a credit account.
                            debit = -amount if amount < 0.0 else 0.0
                            credit = amount if amount > 0.0 else 0.0
                            credit_line = self._get_existing_lines(
                                line_ids, line, credit_account_id, debit, credit)

                            if not credit_line:
                                credit_line = self._prepare_line_values(line, credit_account_id, date, debit, credit)
                                line_ids.append(credit_line)
                            else:
                                credit_line['debit'] += debit
                                credit_line['credit'] += credit

                for line_id in line_ids: # Get the debit and credit sum.
                    debit_sum += line_id['debit']
                    credit_sum += line_id['credit']

                # The code below is called if there is an error in the balance between credit and debit sum.
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    acc_id = slip.journal_id.default_account_id.id
                    if not acc_id:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                    existing_adjustment_line = (
                        line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                    )
                    adjust_credit = next(existing_adjustment_line, False)

                    if not adjust_credit:
                        adjust_credit = {
                            'name': _('Adjustment Entry'),
                            'partner_id': False,
                            'account_id': acc_id,
                            'journal_id': slip.journal_id.id,
                            'date': date,
                            'debit': 0.0,
                            'credit': debit_sum - credit_sum,
                        }
                        line_ids.append(adjust_credit)
                    else:
                        adjust_credit['credit'] = debit_sum - credit_sum

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    acc_id = slip.journal_id.default_account_id.id
                    if not acc_id:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                    existing_adjustment_line = (
                        line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                    )
                    adjust_debit = next(existing_adjustment_line, False)

                    if not adjust_debit:
                        adjust_debit = {
                            'name': _('Adjustment Entry'),
                            'partner_id': False,
                            'account_id': acc_id,
                            'journal_id': slip.journal_id.id,
                            'date': date,
                            'debit': credit_sum - debit_sum,
                            'credit': 0.0,
                        }
                        line_ids.append(adjust_debit)
                    else:
                        adjust_debit['debit'] = credit_sum - debit_sum

                # Add accounting lines in the move
                move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
                move = self.env['account.move'].create(move_dict)
                for slip in slip_mapped_data[journal_id][slip_date]:
                    slip.write({'move_id': move.id, 'date': date})
        return True

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        res = super(HrPayslip, self)._prepare_line_values(line, account_id, date, debit, credit)
        res.update({'analytic_tag_ids': line.salary_rule_id.analytic_tag_ids.ids})
        return res

    def _get_existing_lines(self, line_ids, line, account_id, debit, credit):
        existing_lines = (
            line_id for line_id in line_ids if
            line_id['name'] == line.name
            and line_id['account_id'] == account_id
            and line_id['analytic_account_id'] == (line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id)
            and line_id['analytic_tag_ids'] == (line.salary_rule_id.analytic_tag_ids.ids)
            and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
        return next(existing_lines, False)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            today = fields.date.today()
            first_day = today + relativedelta(day=1)
            last_day = today + relativedelta(day=31)
            if from_date == first_day and end_date == last_day:
                batch_name = from_date.strftime('%B %Y')
            else:
                batch_name = _('From %s to %s', format_date(self.env, from_date), format_date(self.env, end_date))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': batch_name,
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        #Prevent a payslip_run from having multiple payslips for the same employee
        employees -= payslip_run.slip_ids.employee_id
        success_result = {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
        if not employees:
            return success_result

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        contracts = employees._get_contracts(
            payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
        ).filtered(lambda c: c.active)
        contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end),
            ('date_stop', '>=', payslip_run.date_start),
            ('employee_id', 'in', employees.ids),
        ])
        self._check_undefined_slots(work_entries, payslip_run)

        if(self.structure_id.type_id.default_struct_id == self.structure_id):
            work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
            if work_entries._check_if_error():
                work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])

                for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
                    work_entries_by_contract[work_entry.contract_id] |= work_entry

                for contract, work_entries in work_entries_by_contract.items():
                    conflicts = work_entries._to_intervals()
                    time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in conflicts._items]])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Some work entries could not be validated.'),
                        'message': _('Time intervals to look for:%s', time_intervals_str),
                        'sticky': False,
                    }
                }


        default_values = Payslip.default_get(Payslip.fields_get())
        payslips_vals = []
        for contract in contracts:
            values = dict(default_values, **{
                'name': _('New Payslip'),
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            })
            payslips_vals.append(values)
        payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
        payslips._onchange_employee()
        payslips._compute_name()
        payslips.compute_sheet()
        payslip_run.state = 'verify'

        return success_result
