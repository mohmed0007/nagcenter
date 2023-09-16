# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)

import logging

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class TicketAllocation(models.Model):
    """ Allocation Requests Access specifications: similar to leave requests """
    _name = "flight.ticket.allocation"
    _description = "Flight Ticket Allocation"
    _order = "create_date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'

    def _default_holiday_status_id(self):
        if self.user_has_groups('hr_holidays.group_hr_holidays_user'):
            domain = [('valid', '=', True)]
        else:
            domain = [('valid', '=', True), ('allocation_type', '=', 'fixed_allocation')]
        return self.env['hr.leave.type'].search(domain, limit=1)

    def _holiday_status_id_domain(self):
        if self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            return [('valid', '=', True), ('allocation_type', '!=', 'no')]
        return [('valid', '=', True), ('allocation_type', '=', 'fixed_allocation')]

    name = fields.Char('Description', compute='_compute_description', inverse='_inverse_description', search='_search_description', compute_sudo=False)
    private_name = fields.Char('Allocation Description', groups='hr_holidays.group_hr_holidays_user')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
        ], string='Status', readonly=True, tracking=True, copy=False, default='confirm',
        help="The status is set to 'To Submit', when an allocation request is created." +
        "\nThe status is 'To Approve', when an allocation request is confirmed by user." +
        "\nThe status is 'Refused', when an allocation request is refused by manager." +
        "\nThe status is 'Approved', when an allocation request is approved by manager.")
    date_from = fields.Datetime(
        'Start Date', readonly=True, index=True, copy=False, default=fields.Date.context_today,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, tracking=True)
    date_to = fields.Datetime(
        'End Date', store=True, readonly=False, copy=False, tracking=True,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    employee_id = fields.Many2one(
        'hr.employee', store=True, string='Employee', index=True, readonly=False, ondelete="restrict", tracking=True,required=True,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    manager_id = fields.Many2one('hr.employee', compute='_compute_from_employee_id', store=True, string='Manager')
    notes = fields.Text('Reasons', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    # duration
    number_of_days = fields.Float(
        'Number of Days',  store=True, readonly=False, tracking=True, default=1,
        help='Duration in days. Reference field to use when necessary.')
    number_of_days_display = fields.Float(
        'Duration (days)',
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help="If Accrual Allocation: Number of days allocated in addition to the ones you will get via the accrual' system.")
    number_of_hours_display = fields.Float(
        'Duration (hours)',
        help="If Accrual Allocation: Number of hours allocated in addition to the ones you will get via the accrual' system.")
    duration_display = fields.Char('Allocated (Days/Hours)', compute='_compute_duration_display',
        help="Field allowing to see the allocation duration in days or hours depending on the type_request_unit")
    parent_id = fields.Many2one('hr.leave.allocation', string='Parent')

    first_approver_id = fields.Many2one(
        'hr.employee', string='First Approval', readonly=True, copy=False,
        help='This area is automatically filled by the user who validates the allocation')
    second_approver_id = fields.Many2one(
        'hr.employee', string='Second Approval', readonly=True, copy=False,
        help='This area is automaticly filled by the user who validates the allocation with second level (If allocation type need second validation)')

    can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve')

    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Allocation Mode', readonly=True, required=True, default='employee',
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help="Allow to create requests in batchs:\n- By Employee: for a specific employee"
             "\n- By Company: all employees of the specified company"
             "\n- By Department: all employees of the specified department"
             "\n- By Employee Tag: all employees of the specific employee group category")

    department_id = fields.Many2one(
        'hr.department', store=True, string='Department',related='employee_id.department_id',)

    allocation_type = fields.Selection(
        [
            ('regular', 'Regular Allocation'),
            ('accrual', 'Accrual Allocation')
        ], string="Allocation Type", default="accrual", required=True, readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

    accrual_limit = fields.Float('Balance limit',compute='_get_max_num_of',readonly=False, default=0, help="Maximum of allocation for accrual; 0 means no maximum." , store=True)
    amount_per_interval = fields.Float("Number of unit per interval",  store=True, readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]} , digits=(12, 6))
    interval_number = fields.Integer("Number of unit between two intervals", store=True, readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    unit_per_interval = fields.Selection([
        ('hours', 'Hours'),
        ('days', 'Days')
        ],  store=True, string="Unit of time added at each interval", readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    interval_unit = fields.Selection([
        ('months', 'Months'),
        ], store=True, string="Unit of time between two intervals", readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)], 'validate': [('readonly', True)]})
    nextcall = fields.Date("Date of the next accrual allocation", default=False, readonly=True)
    balance = fields.Float(readonly=True , digits=(12, 6))
    balance_taken = fields.Float(readonly=True , digits=(12, 6))
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    # balance_current = fields.Float(readonly=True)
    # self.env['flight.ticket.allocation'].search(
    #     [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate')])

    @api.constrains('number_of_days_display')
    def number_of_days_display_constrains(self):
       balance =  self.env['flight.ticket.allocation'].search(
            [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate')]).mapped('balance')

       balance_taken = self.env['flight.ticket.allocation'].search(
           [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate')]).mapped('balance_taken')
       balan = sum(balance) if balance else 0
       tacken = sum(balance_taken) if balance_taken else 0
       remain = balan  +  tacken
       print(remain ,  self.number_of_days_display , self.employee_id.contract_id.ticket_per_year )
       if (remain +  self.number_of_days_display )  > self.employee_id.contract_id.ticket_per_year   :
            raise UserError(_('the allocated number of ticket will exceed the number of ticket in contract'))

    @api.depends('employee_id.contract_id.ticket_per_year')
    def _get_max_num_of(self):
        for rec in self:
            rec.accrual_limit  = rec.employee_id.contract_id.ticket_per_year



    def action_draft(self):
        if any(holiday.state not in ['confirm', 'refuse'] for holiday in self):
            raise UserError(_('Allocation request state must be "Refused" or "To Approve" in order to reset to Draft.'))
        self.write({
            'state': 'draft',
            'first_approver_id': False,
            'second_approver_id': False,
        })

        return True

    def action_approve(self):

        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Allocation request must be confirmed ("To Approve") in order to approve it.'))
        current_employee = self.env.user.employee_id
        self.write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.action_validate()


    def action_validate(self):
        current_employee = self.env.user.employee_id
        for holiday in self:
            if holiday.state not in ['confirm', 'validate1']:
                raise UserError(_('Allocation request must be confirmed in order to approve it.'))

            holiday.write({'state': 'validate','balance': holiday.number_of_days_display})

        return True

    def action_confirm(self):
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Allocation request must be in Draft state ("To Submit") in order to confirm it.'))
        res = self.write({'state': 'confirm'})
        return res

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['confirm', 'validate', 'validate1'] for holiday in self):
            raise UserError(_('Allocation request must be confirmed or validated in order to refuse it.'))
        ticket_id = self.env['hr.flight.ticket'].search(
            [('employee_id', '=', self.employee_id.id), ('ticket_allocation_id', '=', self.id),
             ('state', '=', 'approve')])
        if ticket_id:
            raise UserError(_('Allocation con not be refused after balance consuming '))
        validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
        validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id ,'balance': 0.0 , 'nextcall': False})
        # If a category that created several holidays, cancel all related
        # linked_requests = self.mapped('linked_request_ids')

        return True
    # _sql_constraints = [
    #     ('type_value',
    #      "CHECK( (holiday_type='employee' AND employee_id IS NOT NULL) or "
    #      "(holiday_type='category' AND category_id IS NOT NULL) or "
    #      "(holiday_type='department' AND department_id IS NOT NULL) or "
    #      "(holiday_type='company' AND mode_company_id IS NOT NULL))",
    #      "The employee, department, company or employee category of this request is missing. Please make sure that your user login is linked to an employee."),
    #     ('duration_check', "CHECK ( number_of_days >= 0 )", "The number of days must be greater than 0."),
    #     ('number_per_interval_check', "CHECK(number_per_interval > 0)", "The number per interval should be greater than 0"),
    #     ('interval_number_check', "CHECK(interval_number > 0)", "The interval number should be greater than 0"),
    # ]
    def _inverse_description(self):
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        for allocation in self:
            if is_officer or allocation.employee_id.user_id == self.env.user or allocation.manager_id == self.env.user:
                allocation.sudo().private_name = allocation.name

    @api.onchange('employee_id')
    def compute_amount_per_interval(self):
        if self.employee_id:

            contract_id = self.employee_id.contract_id
            self.interval_number = 1
            print("salary" * 10,(contract_id.ticket_per_year)/(12*self.interval_number))
            self.amount_per_interval = (contract_id.ticket_per_year)/(12*self.interval_number)

    @api.depends_context('uid')
    def _compute_description(self):
        self.check_access_rights('read')
        self.check_access_rule('read')

        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')

        for allocation in self:
            if is_officer or allocation.employee_id.user_id == self.env.user or allocation.manager_id == self.env.user:
                allocation.name = allocation.sudo().private_name
            else:
                allocation.name = '*****'


    @api.depends('number_of_days')
    def _compute_number_of_days_display(self):
        for allocation in self:
            pass
            # allocation.number_of_days_display = allocation.number_of_days
    @api.model
    def _update_accrual(self):
        """
            Method called by the cron task in order to increment the ticket balance when
            necessary.
        """
        today = fields.Date.from_string(fields.Date.today())

        ticket_alloction = self.sudo().search(
            [('allocation_type', '=', 'accrual'), ('employee_id.active', '=', True), ('state', '=', 'validate'),
             '|', ('date_to', '=', False), ('date_to', '>', fields.Datetime.now()),
             '|', ('nextcall', '=', False), ('nextcall', '<=', today)])
        print("holidays" * 3, ticket_alloction)
        for holiday in ticket_alloction:
            values = {}

            # delta = relativedelta(days=0)
            delta = relativedelta(days=holiday.interval_number)
            values['nextcall'] = (holiday.nextcall if holiday.nextcall else today) + delta
            period_start = datetime.combine(today, time(0, 0, 0)) - delta
            period_end = datetime.combine(today, time(0, 0, 0))
            print("period" * 5, period_start)
            print("period" * 5, period_end)
            # We have to check when the employee has been created
            # in order to not allocate him/her too much leaves
            start_date = holiday.employee_id._get_date_start_work()
            # If employee is created after the period, we cancel the computation
            if period_end <= start_date or period_end < holiday.date_from:
                print("Holiday" * 5, holiday.id)
                holiday.write(values)
                continue

            # If employee created during the period, taking the date at which he has been created
            if period_start <= start_date:
                period_start = start_date

            employee = holiday.employee_id


            days_to_give = holiday.amount_per_interval
            print(days_to_give,holiday.number_of_days_display)
            # if holiday.unit_per_interval == 'hours':
            #     # As we encode everything in days in the database we need to convert
            #     # the number of hours into days for this we use the
            #     # mean number of hours set on the employee's calendar
            #     days_to_give = days_to_give / (employee.resource_calendar_id.hours_per_day or HOURS_PER_DAY)

            values['number_of_days_display'] = holiday.number_of_days_display + days_to_give
            values['balance'] = holiday.number_of_days_display + days_to_give
            # print("Holiday" * 5, holiday.id, values['number_of_days'], days_to_give, prorata)
            if holiday.accrual_limit > 0:
                values['number_of_days_display'] = min(values['number_of_days'], holiday.accrual_limit)

            holiday.write(values)