# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

bt_states = [('draft', 'Draft'), ('confirm', 'Waiting Approval'), ('validate', 'Validated'),
 ('validate1', 'Approved by HR Manager'), ('approved', 'Approved'), ('refuse', 'Refused')]


class BusinessTrip(models.Model):
    _name = 'business.trip'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Business Trip"

    def _get_currency(self):
        user = self.env['res.users'].browse(self.env.uid)
        return user.company_id.currency_id.id

    name = fields.Char('Reference', size=64, required=True, default=_('New'))
    state = fields.Selection(bt_states, string='Status', default='draft', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    branch_id = fields.Many2one('hr.branch', string='Branch', readonly=True)
    transportation_type = fields.Selection([('car', 'Car'), ('flight', 'Flight')], 
        required=False, string='Transportation Type', default='flight')
    departure_date = fields.Date(string='Departure Date', required=True, default=datetime.strftime(datetime.now(), '%Y-%m-%d'))
    arrival_date = fields.Date(string='Return Date')
    cost_center = fields.Selection([('company', 'Company'), ('client', 'Client')], 'Cost Center')
    source = fields.Char(string='Leaving From', required=True)
    destination = fields.Char(string='Going To', required=True)
    no_of_days = fields.Integer(string='No. of Days', required=False, default=1)
    no_of_night = fields.Integer(string='No. of Night', required=False, default=1)
    advance_required = fields.Boolean('Advance Required', default=False, tracking=True)
    visa_required = fields.Boolean('Visa Required', default=False, tracking=True)
    approved_date = fields.Datetime(string='Approved Date', readonly=True, tracking=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Approved by', readonly=True, tracking=True, copy=False)
    description = fields.Text(string='Travel Details', required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, readonly=True, 
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=_get_currency)
    flight_booking_id = fields.Many2one('flight.booking', 'Ticket Details', readonly=True, 
        states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    hr_visa_id = fields.Many2one('hr.visa','Visa Details',readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    per_diem_amount = fields.Monetary('Per Diem Amount')
    estimated_amount = fields.Monetary(string='Estimated Amount', compute='_compute_estimated_amount', copy=False)
    advance_amount = fields.Monetary('Advance Amount', default=0.0)
    total_expense = fields.Monetary('Total Expense Amount', compute='_compute_expense_amount', store=True)
    adjustment_amount = fields.Monetary('Adjustment Amount', default=0.0)
    advance_payment_id = fields.Many2one('account.payment', 'Advance Payment', copy=False)
    payment_entry_id = fields.Many2one('account.payment', 'Payment Entry', copy=False)

    @api.depends('no_of_night', 'per_diem_amount')
    def _compute_estimated_amount(self):
        for rec in self:
            rec.estimated_amount = rec.no_of_night * rec.per_diem_amount

    @api.depends('advance_amount', 'adjustment_amount')
    def _compute_expense_amount(self):
        for rec in self:
            rec.total_expense = rec.advance_amount + rec.adjustment_amount

    @api.constrains('no_of_days')
    def check_days(self):
        for rec in self:
            if rec.no_of_days <= 0.0:
                raise UserError('Days must be greater than 0.0.')

    def unlink(self):
        for bt in self:
            if bt.state not in ['draft']:
                raise UserError(_('You cannot remove the record which is not in draft state!'))
        return super(BusinessTrip, self).unlink()

    @api.model
    def create(self, values):
        if values.get('company_id'):
            values['name'] = self.env['ir.sequence'].with_context(company=values['company_id']).next_by_code(
                'business.trip') or _('New')
        else:
            values['name'] = self.env['ir.sequence'].next_by_code('business.trip') or _('New')
        return super(BusinessTrip, self).create(values)

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.job_id = False
        self.department_id = False
        self.branch_id = False
        if self.employee_id:
            self.job_id = self.employee_id.job_id and self.employee_id.job_id.id
            self.per_diem_amount = self.employee_id.grade_id.per_diem_amount
            self.department_id = self.employee_id.department_id and self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id and self.employee_id.company_id.id
            self.branch_id = self.employee_id.branch_id.id
            
    @api.onchange('departure_date', 'arrival_date')
    def onchange_date(self):
        if self.arrival_date and self.departure_date:
            duration = self.arrival_date - self.departure_date
            self.no_of_days = duration.days + 1
            self.no_of_night = duration.days + 1

    def _message_auto_subscribe_followers(self, updated_values, subtype_ids):
        res = super(BusinessTrip, self)._message_auto_subscribe_followers(updated_values, subtype_ids)
        if updated_values.get('employee_id'):
            employee = self.env['hr.employee'].browse(updated_values['employee_id'])
            if employee.user_id:
                res.append((employee.user_id.partner_id.id, subtype_ids, False))
        return res

    def bt_confirm(self):
        self.ensure_one()
        self.state = 'confirm'

    def bt_validate(self):
        self.ensure_one()
        self.write({'state': 'validate',
                    'approved_by': self.env.user.id,
                    'approved_date': datetime.today()})

    def bt_validate1(self):
        self.ensure_one()
        self.state = 'validate1'

    def bt_approved(self):
        self.ensure_one()
        self.state = 'approved'

    def bt_refuse(self):
        self.ensure_one()
        self.state = 'refuse'

    def set_draft(self):
        self.ensure_one()
        self.write({'state': 'draft', 'approved_by': False, 'approved_date': False})

    def create_ticket_request(self):
        res = {}
        flight_obj = self.env['flight.booking']
        if self.ids:
            view = self.env.ref('business_trip_ksa.flight_booking_form_view')
            bt = self.browse(self.ids[0])
            if not bt.flight_booking_id:
                bt.flight_booking_id = flight_obj.create({
                    'employee_id': bt.employee_id and bt.employee_id.id or False,
                    'job_id' : bt.employee_id.job_id and bt.employee_id.job_id.id,
                    'department_id' : bt.employee_id.department_id and bt.employee_id.department_id.id,
                    'branch_id': bt.employee_id.branch_id and bt.employee_id.branch_id.id,
                    'reason': 'business_trip',
                    'flight_type': 'return',
                    'destination': bt.destination,
                    'source': bt.source,
                    'departure_date':bt.departure_date,
                    'arrival_date': bt.arrival_date,
                    'description': bt.name or 'Generate From Business Trip',
                    })
            res = {
                'type': 'ir.actions.act_window',
                'name': _('Flight Booking'),
                'res_model': 'flight.booking',
                'res_id': bt.flight_booking_id and bt.flight_booking_id.id or False,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'current',
                'nodestroy': True,
            }
        return res

    def create_visa_request(self):
        visa_obj = self.env['hr.visa']
        if self.ids:
            bt = self.browse(self.ids[0])
            view = self.env.ref('business_trip_ksa.hr_visa_form')
            if not bt.advance_payment_id:
                bt.hr_visa_id = visa_obj.create({
                    'employee_id': bt.employee_id and bt.employee_id.id or False,
                    'country_id': bt.employee_id.country_id.id,
                    'department_id': bt.employee_id.department_id.id,
                    'branch_id': bt.employee_id.branch_id.id,
                    'reason_of_visa': 'annual_leave',
                    'purpose_of_visa': 'business_trip',
                    'ticket_type': 'single',
                    'country_id': bt.employee_id.sudo().country_id and bt.employee_id.sudo().country_id.id or False,
                    'requested_date_from': bt.departure_date,
                    'requested_date_to': bt.arrival_date,
                    })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Visa Request'),
            'res_model': 'hr.visa',
            'res_id': bt.hr_visa_id and bt.hr_visa_id.id or False,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'nodestroy': True,
        }
    
    def create_advance_payment(self):
        payment_obj = self.env['business.trip.payment']
        context = self._context.copy()
        if self.ids:
            bt = self.browse(self.ids[0])
            view = self.env.ref('business_trip_ksa.view_business_trip_payment_form')
            context.update({'default_business_trip_id': bt.id})
            if context.get('advance_payment', False):
                context.update({'default_amount': bt.estimated_amount})
            else:
                context.update({'default_amount': bt.estimated_amount - bt.advance_amount})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Business Trip Payment'),
            'res_model': 'business.trip.payment',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'context': context,
            'nodestroy': True,
        }
    
