# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AnnualTicketEmployees(models.TransientModel):
    _name = 'annual.ticket.employees'
    _description = 'Generate Annual Ticket Record for all selected employees'

    employee_ids = fields.Many2many('hr.employee', string='Employees')

    def generate_records(self):
        for rec in self.employee_ids:
            ctx = self.env.context
            ticket_details_obj = self.env['annual.ticket.detail']
            employee = ticket_details_obj.search([('date_from', '>=', ctx.get('date_from')), ('date_to', '<=', ctx.get('date_to')), ('employee_id', '=', rec.id)])
            if employee:
                raise ValidationError(_('You already done %s annual ticket for this particular Duration!!') % rec.name)
            else:
                ticket_details_obj = self.env['annual.ticket.detail']
                ticket_details_ids = ticket_details_obj.search([('employee_id', '=', rec.id), ('annual_ticket_id', '=', ctx.get('active_id'))])
                if ticket_details_ids:
                    raise ValidationError(_('You already generate %s annual ticket details!!') % rec.name)
                else:
                    child_fare = 0
                    adult_fare = ctx.get('adult_fare', 0.0)
                    if rec.children > 0 and adult_fare > 0:
                        children = rec.children if rec.children <= 2 else 2
                        child_fare = children * adult_fare * 0.80

                    self.env['annual.ticket.detail'].create({'employee_id': rec.id,
                                                             'annual_ticket_id': ctx.get('active_id'),
                                                             'adult_fare': adult_fare * rec.adults,
                                                             'child_fare': child_fare,
                                                             'date_from': ctx.get('date_from'),
                                                             'date_to': ctx.get('date_to'),
                                                            })

