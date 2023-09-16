# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil import relativedelta as rdelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrVisa(models.Model):
    _name = 'hr.visa'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "HR Visa"

    @api.depends('approved_date_from', 'approved_date_to')
    def period_of_stay(self):
        for stay in self:
            if stay.approved_date_from and stay.approved_date_to:
                diff = rdelta.relativedelta(stay.approved_date_to, stay.approved_date_from)
                if diff.years > 0:
                    self.years = diff.years
                if diff.months > 0:
                    self.months = diff.months
                if diff.days > 0:
                    self.days = diff.days

    # Fields HR Visa
    name = fields.Char('Reference', size=64, required=True, default=_('New'))
    visa_title = fields.Char(string='Visa Title', size=32)
    client_id = fields.Char(string='Client Name', size=50)
    reason_of_visa = fields.Selection([
        ('annual_leave', 'Exit re-entry Visa'), 
        ('final_exit', 'Final Exit'),
        ('renew_visa', 'Extension of Exit re-entry Visa')], string='Type of Visa', required=True)
    purpose_of_visa = fields.Selection([
        ('business_trip', 'Business Trip'), ('annual_vacation', 'Annual Vacation'),
        ('holiday', 'Holiday'), ('emergency', 'Emergency'), ('other', 'Other')], string='Purpose of Visa', copy=False)
    ticket_type = fields.Selection([('single', 'Single'), ('multi', 'Multiple')], string='Type', default='single', copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  default=lambda self: self.env['hr.employee'].get_employee())
    country_id = fields.Many2one('res.country', string='Nationality', readonly=True)
    years = fields.Float(string='Visa Duration', compute='period_of_stay', store=True)
    months = fields.Float(compute='period_of_stay', store=True)
    days = fields.Float(compute='period_of_stay', store=True)
    department_id = fields.Many2one('hr.department', readonly=True, string='Department')
    branch_id = fields.Many2one('hr.branch', readonly=True, string="Branch")
    requested_date_to = fields.Date(string='Return Date', tracking=True)
    requested_date_from = fields.Date(string='Departure Date', required=True, tracking=True)
    approved_date_to = fields.Date(string='Approved Date To', tracking=True)
    approved_date_from = fields.Date(string='Approved Date From', tracking=True)
    visa_ref = fields.Char(string='Visa Number', tracking=True)
    old_visa_ref = fields.Char(string='Old Visa Number')
    required_documents = fields.Text(string='List of Documents Required', readonly=True)
    description = fields.Text(string='Description')
    state = fields.Selection([('draft', 'To Submit'), ('confirm', 'Waiting Approval'), ('validate1', 'Approved'),
                              ('inprogress', 'In Progress'), ('received', 'Issued'),
                              ('refused', 'Refused')], string='State', default='draft', tracking=True)
    approved_date = fields.Datetime('Approved Date', readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved by', readonly=True)
    handled_by = fields.Many2one('hr.employee', string='Handled by')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

    def unlink(self):
        for record in self:
            if record.state in ['confirm', 'validate', 'validate1', 'inprogress', 'received', 'refused']:
                raise UserError(_('You cannot remove the record which is in %s state!') % record.state)
        return super(HrVisa, self).unlink()

    @api.onchange('requested_date_from', 'requested_date_to')
    def _onchange_requested_date(self):
        for rec in self:
            if rec.requested_date_to and rec.requested_date_from and rec.requested_date_to < rec.requested_date_from:
                raise ValidationError(_('Departure Date must be greater then Return Date.'))

    @api.onchange('approved_date_to', 'approved_date_from')
    def _onchange_approve_date(self):
        for rec in self:
            if rec.approved_date_to and rec.approved_date_from and rec.approved_date_to < rec.approved_date_from:
                raise ValidationError(_('Approve Date to must be greater then Approve Date from.'))

    @api.model
    def create(self, values):
        if values.get('company_id'):
            values['name'] = self.env['ir.sequence'].with_context(company=values['company_id']).next_by_code(
                'visa.request') or _('New')
        else:
            values['name'] = self.env['ir.sequence'].next_by_code('visa.request') or _('New')
        res = super(HrVisa, self).create(values)
        return res

    @api.constrains('requested_date_from', 'requested_date_to')
    def _check_request_dates(self):
        for contract in self.read(['requested_date_from', 'requested_date_to']):
            if contract['requested_date_from'] and contract['requested_date_to'] \
                    and contract['requested_date_from'] > contract['requested_date_to']:
                raise ValidationError(_('Error! Departure Date must be less than Return Date.'))

    @api.constrains('approved_date_from', 'approved_date_to')
    def _check_approved_dates(self):
        for contract in self.read(['approved_date_from', 'approved_date_to']):
            if contract['approved_date_from'] and contract['approved_date_to'] \
                    and contract['approved_date_from'] > contract['approved_date_to']:
                raise ValidationError(_('Error! Approved Date From must be less than Approved Date To.'))

    def _add_followers(self):
        partner_ids = []
        if self.employee_id.user_id:
            partner_ids.append(self.employee_id.user_id.partner_id.id)
        if self.employee_id.sudo().parent_id.user_id:
            partner_ids.append(self.employee_id.sudo().parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)

    def visa_confirm(self):
        self.ensure_one()
        self.state = 'confirm'

    def visa_validate1(self):
        self.ensure_one()
        self.write({'state': 'validate1',
                    'approved_by': self.env.uid,
                    'approved_date': datetime.today()})
        
    def visa_inprogress(self):
        self.ensure_one()
        self.state = 'inprogress'

    def visa_received(self):
        self.ensure_one()
        if self.approved_date_from and self.visa_ref:
            self.state = 'received'

            if self.handled_by.user_id:
                self.message_subscribe(partner_ids=[self.handled_by.user_id.partner_id.id])
            self.message_post(message_type="email", subtype_xmlid='mail.mt_comment', body=_("Visa Request Received."))
        else:
            raise UserError(_('Please Enter Values For Visa Number, Approved Date From and Approved Date To'))

    def visa_refuse(self):
        self.ensure_one()
        self.state = 'refused'

    def set_draft(self):
        self.ensure_one()
        self.write({'state': 'draft',
                    'approved_by': False,
                    'approved_date': False})

    @api.onchange('reason_of_visa')
    def onchange_reason_of_visa(self):
        document_list = ""
        if self.reason_of_visa:
            if self.reason_of_visa == 'final_exit':
                document_list = """
                    1. Date of Ticket.
                    2. Clearance Letter from Bank.
                    3. Clearance Letter of Traffic Payment.
                    4. Clearance of Car.
                                    """
            if self.reason_of_visa == 'annual_leave':
                document_list = """
                    1. Valid IQAMA.
                    2. Valid Passport.
                    3. Clear Traffic Violence (If Any).
                """
        self.required_documents = document_list

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.department_id = False
        self.country_id = False
        self.branch_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.country_id = self.employee_id.sudo().country_id.id
            self.branch_id = self.employee_id.branch_id.id
