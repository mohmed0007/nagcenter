# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, readonly=True,
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('suspend_salary', '=', False), '|', ('active', '=', True), ('active', '=', False)]")

    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        worked_days = 0
        effective_date = self.employee_id.effective_date
        first_day_of_month = (self.date_from + relativedelta(day=1)).day
        last_day_of_month = (self.date_to + relativedelta(months=+1, day=1, days=-1)).day
        if self.date_from.day == 1 and self.date_to.day == last_day_of_month:
            if effective_date:
                if self.date_to >= effective_date > self.date_from:
                    worked_days = (30 - effective_date.day) + 1
                else:
                    worked_days = 30
            else:
                worked_days = 30
        elif (self.date_from.day == first_day_of_month and self.date_to.day == first_day_of_month) or (self.date_from.day == last_day_of_month and self.date_to.day == last_day_of_month):
            worked_days = 1
        elif self.date_from.day != 1 and self.date_to.day == last_day_of_month:
            worked_days = (30 - self.date_from.day) + 1
        else:
            worked_days = (self.date_to.day - self.date_from.day) + 1
        res = []
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        work_hours = self.contract_id._get_work_hours(self.date_from, self.date_to, domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0
        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            days = round(hours / hours_per_day, 5) if hours_per_day else 0
            if work_entry_type_id == biggest_work:
                days += add_days_rounding
            day_rounded = self._round_days(work_entry_type, days)
            add_days_rounding += (days - day_rounded)
            if work_entry_type.code == "WORK100":
                attendance_line = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type_id,
                    'number_of_days': worked_days,
                    'number_of_hours': worked_days * hours_per_day,
                }
            else:
                attendance_line = {
                    'sequence': work_entry_type.sequence,
                    'work_entry_type_id': work_entry_type_id,
                    'number_of_days': day_rounded,
                    'number_of_hours': hours,
                }
            res.append(attendance_line)
        return res


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'payslip_id.normal_wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        for worked_days in self.filtered(lambda wd: not wd.payslip_id.edited):
            if not worked_days.contract_id or worked_days.code == 'OUT':
                worked_days.amount = 0
                continue
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
            else:
                if worked_days.code == "WORK100":
                    worked_days.amount = (worked_days.payslip_id.normal_wage / 30) * worked_days.number_of_days
                else:
                    worked_days.amount = worked_days.payslip_id.normal_wage * worked_days.number_of_hours / (
                            worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0
