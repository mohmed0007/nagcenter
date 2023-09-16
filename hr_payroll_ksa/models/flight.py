# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

booking_states = [('draft', 'Draft'), ('confirm', 'Waiting Approval'), ('validate', 'Validated'),
                  ('validate1', 'Approved by HR Manager'), ('in_progress', 'In Progress'),
                  ('received', 'Received'), ('refuse', 'Refused')]


class FlightBooking(models.Model):
    _name = 'flight.booking'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Flight Booking"

    name = fields.Char('Reference', size=64, required=True, default=_('New'))
    state = fields.Selection(booking_states, string='Status', default='draft', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  default=lambda self: self.env['hr.employee'].get_employee())
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    branch_id = fields.Many2one('hr.branch', string='Branch', readonly=True)

    flight_type = fields.Selection([('single', 'One Way'),
                                    ('return', 'Round Trip')], required=True, string='Type', default='single')
    departure_date = fields.Date(string='Preferred Start Date', required=True,
                                 default=datetime.strftime(datetime.now(), '%Y-%m-%d'),
                                 )
    arrival_date = fields.Date(string='Preferred End Date')
    supplier_id = fields.Many2one('res.partner', string='Travel Agency')
    source = fields.Char(string='Leaving From', required=True)
    destination = fields.Char(string='Going To', required=True)
    seats = fields.Integer(string='No. of Seats', required=True, default=1)
    booking_lines = fields.One2many('flight.booking.line', 'booking_id', string='Booking Lines')
    reason = fields.Selection([('business_trip', 'Business Trip'), ('annual_ticket', 'Annual Ticket'),
                               ('internal', 'Internal Meeting'), ('personal', 'Personal'), ('others', 'Others')],
                              required=True,
                              string='Purpose of Travel', default='business_trip')
    approved_date = fields.Datetime(string='Approved Date', readonly=True, tracking=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Approved by', readonly=True, tracking=True, copy=False)
    description = fields.Text(string='Description', required=True)
    po_number = fields.Char(string='PO Number')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True,
                                 default=lambda self: self.env.user.company_id)

    def unlink(self):
        for booking in self:
            if booking.state not in ['draft']:
                raise UserError(_('You cannot remove the record which is not in draft state!'))
        return super(FlightBooking, self).unlink()

    @api.model
    def create(self, values):
        if values.get('company_id'):
            values['name'] = self.env['ir.sequence'].with_context(company=values['company_id']).next_by_code(
                'flight.booking') or _('New')
        else:
            values['name'] = self.env['ir.sequence'].next_by_code('flight.booking') or _('New')
        return super(FlightBooking, self).create(values)

    @api.onchange('flight_type')
    def onchange_flight_type(self):
        self.arrival_date = False

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.job_id = False
        self.department_id = False
        if self.employee_id:
            self.job_id = self.employee_id.job_id and self.employee_id.job_id.id
            self.department_id = self.employee_id.department_id and self.employee_id.department_id.id
            self.branch_id = self.employee_id.branch_id and self.employee_id.branch_id.id
            self.company_id = self.employee_id.company_id and self.employee_id.company_id.id

    def _add_followers(self):
        partner_ids = []
        partner_ids.append(self.employee_id.user_id.partner_id.id)
        if self.employee_id.sudo().parent_id.user_id:
            partner_ids.append(self.employee_id.sudo().parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)

    def flight_booking_confirm(self):
        self.ensure_one()
        self.state = 'confirm'

    def flight_booking_validate(self):
        self.ensure_one()
        self.write({'state': 'validate',
                    'approved_by': self.env.user.id,
                    'approved_date': datetime.today()})

    def flight_booking_validate1(self):
        self.ensure_one()
        self.state = 'validate1'

    def flight_booking_inprogress(self):
        self.ensure_one()
        self.state = 'in_progress'

    def ticket_received(self):
        self.ensure_one()
        booking = self
        if not booking.booking_lines:
            raise UserError(_('Please add Ticket Details first !'))

        if booking.reason == 'annual_ticket':
            for book in booking.booking_lines:
                if book.invoice_amount <= 0:
                    raise UserError(_('Invoice Amount should be greater then 0'))
                annual_ticket_id = self.env['annual.ticket.detail'].search(
                    [('employee_id', '=', booking.employee_id.id),
                     ('date_from', '<=', book.travel_date), ('date_to', '>=', book.travel_date)], limit=1)
                if annual_ticket_id:
                    self.env['annual.ticket.status'].create({'ticket_detail_id': annual_ticket_id.id,
                                                             'member_type': book.member_type,
                                                             # 'ticket_status': 'used',
                                                             'used_amount': book.invoice_amount
                                                             })
        self.state = 'received'

    def flight_booking_refuse(self):
        self.ensure_one()
        self.state = 'refuse'

    def set_draft(self):
        self.ensure_one()
        self.write({'state': 'draft', 'approved_by': False, 'approved_date': False,
                    })


class FlightBookingLine(models.Model):
    _name = 'flight.booking.line'
    _order = 'id desc'
    _inherit = 'mail.thread'
    _description = "Flight Booking Lines"

    def _set_currency(self):
        self.currency_id = self.company_id.currency_id.id if self.company_id else False

    ticket_no = fields.Char(string='Ticket Number', required=True)
    booking_id = fields.Many2one('flight.booking', string='Booking Request')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    travel_date = fields.Date(string='Date of Journey', required=True)
    source = fields.Char(string='Leaving From', required=True)
    destination = fields.Char(string='Going To', required=True)
    airline = fields.Char(string='Airline', required=True)
    invoice_amount = fields.Monetary(string='Invoice Amount', required=True)
    currency_id = fields.Many2one('res.currency', compute=_set_currency)
    remarks = fields.Text(string='Remarks')
    seats = fields.Integer(string='No. of Seats', default=1, readonly=True)
    member_type = fields.Selection([('adult', 'Adult'), ('child', 'Child'), ('infant', 'Infant')],
                                   string="Member Type", default="adult")
    flight_class = fields.Selection([('first', 'First'),
                                     ('business', 'Business'), ('guest', 'Guest')], string='Class', default='first')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, values):
        if values.get('booking_id'):
            self._check_state(values['booking_id'])
        return super(FlightBookingLine, self).create(values)

    def _check_state(self, booking_id):
        booking = self.env['flight.booking'].browse(booking_id)
        if booking.state not in ['in_progress', 'received']:
            raise UserError(_("You can't set details for the Booking which is not in 'In Progress' state!"))
        return True

    def write(self, values):
        if values.get('booking_id'):
            self._check_state(values['booking_id'])
        else:
            self._check_state(self.booking_id.id, )
        return super(FlightBookingLine, self).write(values)

    @api.depends('ticket_no', 'travel_date')
    def name_get(self):
        res = []
        for ticket in self:
            name = ''.join([ticket.ticket_no, ' - ', str(ticket.travel_date)])
            res.append((ticket.id, name))
        return res
