# -*- coding: utf-8 -*-
# Part of odoo. See LICENSE file for full copyright and licensing detials.

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class AnnualTicket(models.Model):
    _name = 'annual.ticket'
    _description = "Annual Ticket"
    _inherit = ['mail.thread']
    
    name = fields.Char('Name', required=True, tracking=True)
    date_from = fields.Date("Date From", required=True, tracking=True)
    date_to = fields.Date("Date To", required=True, tracking=True)
    adult_fare = fields.Float('Default Adult Fare', required=True, help="This default amount shows return fare.")
    annual_ticket_detail_ids = fields.One2many('annual.ticket.detail', 'annual_ticket_id')
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.user.company_id)

    def action_annual_ticket_by_employees(self):
        self.ensure_one()
        form_view = self.env.ref('hr_leave_ksa.view_annual_ticket_by_employees', False)
        return {
            'name': _('Generate Annual Leaving'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'annual.ticket.employees',
            'views': [(form_view.id, 'form')],
            'view_id': form_view.id,
            'target': 'new',
            'context': {'date_from': self.date_from, 'date_to': self.date_to, 'adult_fare': self.adult_fare},
        }

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if any(air.date_from > air.date_to for air in self):
            raise ValidationError(_("Annual Ticket 'Date From' must be earlier 'Date To'."))

    @api.constrains('annual_ticket_detail_ids')
    def check_duplicate_emp(self):
        for rec in self:
            emp_list = []
            for line in rec.annual_ticket_detail_ids.search([('date_from', '>=', rec.date_from), ('date_to', '<=', rec.date_to)]):
                if line.employee_id.id not in emp_list:
                    emp_list.append(line.employee_id.id)
                else:
                    raise ValidationError(_('You already done %s annual ticket for this particular duration!!') % line.employee_id.name)


class AnnualTicketDetails(models.Model):
    _name = 'annual.ticket.detail'
    _description = "Annual Ticket details"
    _rec_name = 'employee_id'

    annual_ticket_id = fields.Many2one('annual.ticket')
    employee_id = fields.Many2one('hr.employee', required=True)
    adult_fare = fields.Float('Adult Fare', required=True, help="This amount shows return fare.")
    child_fare = fields.Float('Child Fare', help="80% of Adult Fare", required=True, default=0.0)
    adults = fields.Integer('Adult(s)', compute='_get_total_members', help='Employee and Spouse')
    children = fields.Integer('Children', compute='_get_total_members',
                              help='Maximum two children, if no infants(Age must be between 2 to 18)')
    
    ticket_status_ids = fields.One2many('annual.ticket.status', 'ticket_detail_id')
    date_from = fields.Date("Date From", related='annual_ticket_id.date_from', store=True)
    date_to = fields.Date("Date To", related='annual_ticket_id.date_to', store=True)
    allocated_amount = fields.Float('Allocated Amount', required=True, compute='_compute_amount')
    used_amount = fields.Float('Used Amount', compute='_compute_amount')
    remaining_amount = fields.Float('Remaining Amount', compute='_compute_amount')
    other_hr_payslip_ids = fields.One2many('other.rules', 'ticket_detail_id', readonly=True)

    def generate_air_allowance(self):
        for rec in self:
            return {
               'type': 'ir.actions.act_window',
               'res_model': 'generate.air.allowance',
               'view_mode': 'form',
               'view_type': 'form',
               'view_id': self.env.ref('hr_leave_ksa.generate_air_allowance_from_view').id,
               'target': 'new',
               'context': {'default_allowance_amount': rec.remaining_amount}
            }

    @api.depends('adults', 'children', 'adult_fare', 'child_fare', 'ticket_status_ids',
                 'other_hr_payslip_ids')
    def _compute_amount(self):
        for rec in self:
            rec.allocated_amount = rec.adult_fare + rec.child_fare #((rec.adult_fare * rec.adults) + (rec.child_fare * rec.children))
            rec.used_amount = sum(rec.ticket_status_ids.mapped('used_amount')) + sum(rec.other_hr_payslip_ids.mapped('amount'))
            rec.remaining_amount = rec.allocated_amount - rec.used_amount
            
    @api.depends('employee_id')
    def _get_total_members(self):
        for rec in self:
            rec.adults = rec.employee_id.adults
            rec.children = rec.employee_id.children if rec.employee_id else 0
                
    @api.onchange('adult_fare', 'employee_id')
    def onchange_adult_fare(self):
        for rec in self:
            rec.child_fare = 0.0
            if rec.adult_fare > 0: 
                if rec.children > 0:
                    rec.child_fare = (rec.adult_fare * 80) / 100


class AnnualTicketStatus(models.Model):
    _name = 'annual.ticket.status'
    _description = 'Annual Ticket Status'

    ticket_detail_id = fields.Many2one('annual.ticket.detail')
    member_type = fields.Selection([('adult', 'Adult'), ('child', 'Child')])
    used_amount = fields.Float('Used Amount')


class OtherRules(models.Model):
    _inherit = 'other.rules'

    ticket_detail_id = fields.Many2one('annual.ticket.detail')
