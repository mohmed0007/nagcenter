# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError



class ApproveRequest(models.Model):
    _inherit = 'approval.request'

    date = fields.Date(string="Date")
    # request_owner_id = fields.Many2one('res.users', string="Request Owner",
    #                                    check_company=True, domain="['|', ('employee_id.parent_id.user_id.id', '=', user.id), ('employee_id.user_id.id', '=', user.id)]")
    @api.depends('request_owner_id')
    def compute_emp_no(self):
        for rec in self:
            if rec.request_owner_id:
                print("ASLKFFKKGJG")
                employee_record = self.env['hr.employee'].search([('user_id', '=', rec.request_owner_id.id)],limit=1)
                rec.employee_number = int(employee_record.employee_number)
                rec.department_id = employee_record.department_id.id
                rec.employee_id = employee_record.id
            else:
                rec.employee_number = 0
                rec.department_id = False
                rec.employee = False

    employee_number = fields.Integer(string='Employee No', store=True,comput="compute_emp_no")
    department_id = fields.Many2one('hr.department', string="Department",help='Department of the employee', store=True, compute="compute_emp_no")
    employee_id = fields.Many2one('hr.employee', string="Employee",help='Employee', store=True, compute="compute_emp_no")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    # @api.onchange('employee_id')
    # def restrict_request(self):
    #     if self.request_owner_id:
    #         if self.request_owner_id != self.employee_id.parent_id.user_id.id or self.request_owner_id != self.employee_id.user_id.id :
    #             raise ValidationError(_('You can only create request for you or for direct employees') )

    @api.model
    def create(self, values):
        print("UYYYYTTTTTT")
        res = super(ApproveRequest, self).create(values)
        user_id = self.env['res.users'].search([('id', '=', values['request_owner_id'])], limit=1)
        employee_id = self.env['hr.employee'].search([('user_id', '=', user_id.id)], limit=1)
        print("UYYYYTTTTTT",user_id.id ,employee_id.parent_id.user_id.id,employee_id.user_id.id )
        if user_id.id != user_id.parent_id.user_id.id and user_id.id != employee_id.user_id.id:
            raise ValidationError(_('You can only create request for you or for direct employees'))

        return res

