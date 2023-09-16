# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError,ValidationError


from collections import defaultdict
from datetime import datetime, date, time
import pytz

from odoo.exceptions import UserError


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    # def reset_draft(self):
    #     if not self.slip_ids:
    #        self.state = 'draft'

    def action_draft(self):
        if self.slip_ids:
            raise UserError(_('You cannot delete a Batch which hase payslip'))
        return self.write({'state': 'draft'})


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    _description = 'Generate payslips for all selected employees'





    @api.model
    def default_get(self, fields):
        res = super(HrPayslipEmployees, self).default_get(fields)

        print("NEw",self.env.context.get('active_id'))
        res.update({
            'hr_payslip_run': self.env.context.get('active_id'),
            # 'warehouse_id': warehouse_id

        })

        return res

    hr_payslip_run = fields.Many2one('hr.payslip.run', string='Batch')
    # def _get_available_contracts_domain(self):
    #     return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id)]

    def _get_employees(self):
        active_employee_ids = self.env.context.get('active_employee_ids', False)
        if active_employee_ids:
            return self.env['hr.employee'].browse(active_employee_ids)
        # YTI check dates too
        employee_ids = self.env['hr.employee'].search(self._get_available_contracts_domain())
        leave_obj = self.env['hr.leave'].search(
                [('employee_id', 'in', employee_ids.ids),('state', '=', 'validate')])
        employee_list = self.env['hr.resignation'].search(
            [('employee_id', 'in', employee_ids.ids), ('state', '=', 'approved')]).mapped('employee_id')
        #
        leave_obj = leave_obj.filtered(lambda x: x.holiday_status_id.is_paid == True)
        print('employee_ids', employee_ids, tuple(leave_obj.ids), self.hr_payslip_run)
        emp_obj = leave_obj.filtered(lambda x: not x.resumption_date).mapped('employee_id')
        employee_ids = employee_ids.filtered(lambda x: x.id not in  tuple(emp_obj.ids))
        employee_ids = employee_ids.filtered(lambda x: x.id not in  tuple(employee_list.ids))
        print('employee_ids',employee_ids , tuple(leave_obj.ids),self.hr_payslip_run)
        return employee_ids


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # leave_salary = fields.Boolean(string='Leave Salary', help="Check leave if salary should be paid for the employee if is on ;leave")
    number_of_days = fields.Float(string="Days",compute="_compute_number_of_days",store=True)
    payment_type = fields.Selection(
        [
            ('regular', 'Regular'),
            ('in_advance', 'In advance')
        ], string="Payment Type", readonly=True,compute="_compute_number_of_days",store=True,
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]},
        tracking=True)
    # unpaid_leave = fields.One2many('hr.leave')
    unpaid = fields.Float(string="Unpaid" )

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        res = super(HrPayslip, self)._onchange_employee()
        print()
        Unpaid_leave_obj = self.env['hr.leave'].search(
            [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate')])
        Unpaid_leave_obj = Unpaid_leave_obj.filtered(lambda x: x.date_from.date() >= self.date_from  and x.date_to.date() <= self.date_to  and x.holiday_status_id.is_paid != True)
        self.unpaid = sum(Unpaid_leave_obj.mapped('number_of_days')) if Unpaid_leave_obj.mapped('number_of_days') else 0
        print(self.unpaid, 'self.unpaid', Unpaid_leave_obj.mapped('number_of_days'))
        leave_obj = self.env['hr.leave'].search(
                    [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate'),('resumption_date', '!=', False)],order='request_date_from')

        for rec in leave_obj :
            print(rec.request_date_from)

        if leave_obj.mapped('resumption_date'):
           stare_date = max(leave_obj.mapped('resumption_date'))
           print("leave_obj" * 5, leave_obj, type(stare_date))
           leave_ob2 = self.env['hr.leave'].search(
               [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate'),
                ('resumption_date', '!=', False)], order='request_date_from' , limit=1)
           if stare_date.month == self.date_from.month and leave_ob2.term_type != 'short' and leave_ob2.holiday_status_id.is_paid == True:
              self.date_from = stare_date

        # leave_obj = leave_obj.filtered(lambda
        #                                    x: x.resumption_date)


        return res



    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days(self):

        for payslip in self:
            pass




    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_date(self):

        for payslip in self.filtered('employee_id'):
            domain = [
                ('date_from', '<', payslip.date_to),
                ('date_to', '>', payslip.date_from),
                ('employee_id', '=', payslip.employee_id.id),
            ]
            npayslip = self.search_count(domain)



