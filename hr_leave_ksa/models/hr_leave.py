# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models, _


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    is_annual_leave = fields.Boolean('Annual Leave', default=False)


class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'

    ticket_required = fields.Boolean('Ticket Required', default=False)
    flight_booking_id = fields.Many2one('flight.booking', 'Ticket Details', readonly=True, 
        states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})
    exit_entry_required = fields.Boolean('Exit Entry Required',default=False)
    hr_visa_id = fields.Many2one('hr.visa','Visa Details',readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]})

    def create_ticket_request(self):
        res = {}
        flight_obj = self.env['flight.booking']
        if self.ids:
            view = self.env.ref('hr_payroll_ksa.flight_booking_form_view')
            leaves = self.browse(self.ids[0])
            if not leaves.flight_booking_id:
                leaves.flight_booking_id = flight_obj.create({
                    'employee_id': leaves.employee_id and leaves.employee_id.id or False,
                    'job_id' : leaves.employee_id.job_id and leaves.employee_id.job_id.id,
                    'department_id' : leaves.employee_id.department_id and leaves.employee_id.department_id.id,
                    'branch_id': leaves.employee_id.branch_id.id,
                    'reason': 'annual_ticket',
                    'flight_type': 'single',
                    'destination': leaves.employee_id.address_home_id and leaves.employee_id.address_home_id.city or '',
                    'source': leaves.employee_id and leaves.employee_id.address_id.city or leaves.employee_id.company_id.city or leaves.employee_id.company_id.name,
                    'departure_date': leaves.date_from,
                    'description': leaves.name or 'Generate From Leave',
                    })
            res = {
                'type': 'ir.actions.act_window',
                'name': _('Flight Booking'),
                'res_model': 'flight.booking',
                'res_id': leaves.flight_booking_id and leaves.flight_booking_id.id or False,
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
            leaves = self.browse(self.ids[0])
            view = self.env.ref('hr_employee_updation.hr_visa_form')
            if not leaves.hr_visa_id:
                leaves.hr_visa_id = visa_obj.create({
                    'employee_id': leaves.employee_id and leaves.employee_id.id or False,
                    'country_id': leaves.employee_id.sudo().country_id.id,
                    'department_id' : leaves.employee_id.department_id and leaves.employee_id.department_id.id,
                    'branch_id': leaves.employee_id.branch_id.id,
                    'reason_of_visa': 'annual_leave',
                    'purpose_of_visa': 'annual_vacation',
                    'ticket_type': 'single',
                    'requested_date_from': leaves.date_from,
                    })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Visa Request'),
            'res_model': 'hr.visa',
            'res_id': leaves.hr_visa_id and leaves.hr_visa_id.id or False,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'current',
            'nodestroy': True,
        }
    

class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    is_annual_leave = fields.Boolean(related='holiday_status_id.is_annual_leave', string='Annual Leave', store=True)
    
    def create_encashment_leave(self):
        context = self._context.copy()
        if self.ids:
            leave = self.browse(self.ids[0])
            view = self.env.ref('hr_leave_ksa.leave_encashment_form_view')
            
            context.update({'default_employee_id': leave.employee_id.id, 
                'default_leave_allocation_id': leave.id,
                'default_remaining_days': leave.max_leaves - leave.leaves_taken})
            
        return {
            'type': 'ir.actions.act_window',
            'name': _('Leave Encashment'),
            'res_model': 'leave.encashment',
            'view_mode': 'form',
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }