# -*- coding: utf-8 -*-
# Part of odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class LeaveEncashment(models.TransientModel):
    _name = 'leave.encashment'
    _description = 'Leave Encashment'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    leave_allocation_id = fields.Many2one('hr.leave.allocation', 'Allocated Leave', required=True)
    encashment_days = fields.Float('Encashment Days')
    encashment_type = fields.Selection([('by_payslip', 'By Payslip'), ('reduse_days', 'Reduce Days'), ('bank_cash', 'Bank/Cash')], default='by_payslip', required=True)
    leaves_taken = fields.Float('Leaves Taken', related='leave_allocation_id.leaves_taken')
    remaining_days = fields.Float('Remaining Days', readonly=True)

    journal_id = fields.Many2one('account.journal', string='Payment Method')
    applied_date = fields.Date(string='Encashment Report Date', required=True, default=fields.Date.today)
    
    def generate_leave_allowance(self):
        for rec in self:
            ctx = self.env.context
            if rec.encashment_days > rec.remaining_days:
                raise UserError(_('Encashment Days need to be less than remaining days of %s Employee !!' % rec.employee_id.name))
            elif rec.encashment_days == 0:
                raise UserError(_('Encashment Days need to be greater than 0!!'))
            else: 
                if rec.encashment_type == 'by_payslip':
                    cutdown_list = []
                    rec.leave_allocation_id.write({'number_of_days': rec.leave_allocation_id.max_leaves - rec.encashment_days})
                    contract_id = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id), ('state', '=', 'open')], limit=1)
                    ded_amount = (contract_id.wage * rec.encashment_days / 30)
                    payslip_data = {'employee_id': rec.employee_id.id,
                                    'description': 'Encashment Leave Allowance',
                                    'operation_type': 'allowance',
                                    'amount': ded_amount or 0,
                                    'state': 'done',
                                    }
                    other_hr_payslip_id = self.env['other.rules'].create(payslip_data).id
                    rec.leave_allocation_id.message_post(message_type="email", subtype_xmlid='mail.mt_comment', 
                        body=_("%d no. of days are consider as encashment and provided amount by payslip." % rec.encashment_days))
                    
                elif rec.encashment_type == 'bank_cash':
                    rec.leave_allocation_id.write({'number_of_days': rec.leave_allocation_id.max_leaves - rec.encashment_days})
                        
                    contract_id = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id), ('state', '=', 'open')], limit=1)
                    amount = (contract_id.wage * rec.encashment_days / 30)
                    payment_methods = rec.journal_id.outbound_payment_method_ids
                    payment_obj = self.env['account.payment']
                    all_fields = payment_obj.fields_get()
                    account_payment_data = payment_obj.default_get(all_fields)
                    if not rec.employee_id.address_home_id:
                        raise UserError(_("No Home Address found for the employee %s, please configure one.") % (
                            rec.employee_id.name))

                    account_payment_data.update({'payment_method_id': payment_methods and payment_methods[0].id or False,
                                                'payment_type': 'outbound',
                                                'partner_type': 'supplier',
                                                'partner_id': rec.employee_id.address_home_id.id,
                                                'amount': amount,
                                                'journal_id': rec.journal_id.id,
                                                'date': fields.Date.today(),
                                                })
                    payment_id = self.env['account.payment'].create(account_payment_data)
                    payment_id.action_post()
                    rec.leave_allocation_id.message_post(message_type="email", subtype_xmlid='mail.mt_comment', 
                        body=_("%d no. of days are consider as encashment and amount will provide to employee." % rec.encashment_days))
                    
                else:
                    rec.leave_allocation_id.write({'number_of_days': rec.leave_allocation_id.max_leaves - rec.encashment_days})
                    rec.leave_allocation_id.message_post(message_type="email", subtype_xmlid='mail.mt_comment', 
                        body=_("%d no. of days are reduces." % rec.encashment_days))
                    
    