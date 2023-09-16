# -*- coding: utf-8 -*-

from odoo.exceptions import Warning
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import math
import time
from datetime import datetime, date
from dateutil import relativedelta


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    def _get_default_notice_days(self):
        if self.env['ir.config_parameter'].get_param(
                'hr_resignation.notice_period'):
            return self.env['ir.config_parameter'].get_param(
                            'hr_resignation.no_of_days')
        else:
            return 0

    notice_days = fields.Integer(string="Notice Period", default=_get_default_notice_days)
    basic = fields.Monetary('Basic', compute_sudo=True, tracking=True, help='Basic Salary of Employee')
    HRA = fields.Monetary(string='Housing Allowance', help="HRA of employee (25% of basic)", tracking=True)
    TA = fields.Monetary(string='Transport Allowance', help="Transport Allowance of employee (10% of Basic)",
                         tracking=True)
    gross_amt = fields.Monetary('Gross Salary', compute_sudo=True,
                                help="Gross Amount is Sum of Basic Salary + HRA + TA.", store=True)
    other_amt = fields.Monetary('Other Allowance', tracking=True)
    other_amt2 = fields.Monetary('Fixed/OT Amount', tracking=True)
    gosi_deduction = fields.Monetary('GOSI Deduction', tracking=True)
    calc_gosi_deduction = fields.Monetary('GOSI Calculated Amount', readonly=True,
                                          help='GOSI deduction amount of Employee')
    leave_per_year = fields.Float(string='Annual Leave')
    leave_per_month = fields.Float(string='Monthly Leave', )
    monthly_leave_salary = fields.Float(string='Monthly Leave Salary', store=True)
    insurance_company = fields.Float(string="Company Percentage ", help="Company insurance percentage")
    insurance_employee = fields.Float(string="Employee Percentage ", help="Company insurance percentage")
    deduced_employee_per_month = fields.Float(string="Employee deduced per month",
                                              help="Amount that is deduced from employee salary per month", store=True)
    deduced_company_per_month = fields.Float(string="Company deduced per month",
                                             help="Amount that is paid by the Company per year", store=True)
    contract_type = fields.Selection([('limited', 'Limited Period'), ('unlimited', 'Unlimited Period')],
                                     string="Contract Type")

    @api.onchange('insurance_employee', 'insurance_company', 'wage', 'HRA')
    def get_deduced_amount(self):
        current_date = datetime.now()
        print("Osman" * 12)
        current_datetime = datetime.strftime(current_date, "%Y-%m-%d ")
        for cont in self:
            if (((cont.wage + cont.HRA) * cont.insurance_employee) / 100) > 4500:
                cont.deduced_employee_per_month = 4500
            else:
                cont.deduced_employee_per_month = ((cont.wage + cont.HRA) * cont.insurance_employee) / 100
            if ((cont.wage + cont.HRA) * cont.insurance_company) / 100 > 5400:
                cont.deduced_employee_per_month = 5400
            else:
                cont.deduced_company_per_month = ((cont.wage + cont.HRA) * cont.insurance_company) / 100

    @api.onchange('leave_per_year', 'wage', 'HRA', 'TA', 'other_amt', 'other_amt2')
    def get_amount(self):
        # print('leave_per_year', self.leave_per_year)
        for contract in self:
            contract.basic = 0.0
            contract.gross_amt = 0.0
            if contract.wage > 0:
                contract.basic = contract.wage
                contract.gross_amt = contract.wage + contract.HRA + contract.TA + \
                                     contract.other_amt + contract.other_amt2
            if contract.leave_per_year:
                leave_salary = (contract.wage + contract.HRA + contract.other_amt + contract.other_amt2
                                + contract.TA) / 30
                contract.leave_per_month = contract.leave_per_year / 12
                print(leave_salary)
                contract.monthly_leave_salary = leave_salary * contract.leave_per_month
            else:
                contract.leave_per_month = 0.0
                contract.monthly_leave_salary = 0.0

    def compute_rule_amount(self):
        for contract in self:
            hra_value = 0.0
            ta_value = 0.0
            if contract.wage > 0:
                hra_value = round(contract.wage * 0.25)
                ta_value = round(contract.wage * 0.1)
            contract.HRA = hra_value
            contract.TA = ta_value

    def compute_gosi_amount(self):
        for contract in self:
            if not contract.employee_id.country_id:
                raise UserError('Please define nationality of employee.')
            final_amt = 0.0
            calc_amt = contract.basic + contract.HRA
            if contract.employee_id.country_id.code == 'SA':
                final_amt = (calc_amt > 45000 and 45000 * 0.0975 or calc_amt * 0.0975)
            elif contract.employee_id.country_id.code == 'BH':
                final_amt = (calc_amt > 40000 and 40000 * 0.06 or calc_amt * 0.06)
            fractional, whole = math.modf(final_amt)
            final_amt = round(final_amt, 0)
            if fractional == 0.5:
                final_amt += 1
            contract.calc_gosi_deduction = final_amt
