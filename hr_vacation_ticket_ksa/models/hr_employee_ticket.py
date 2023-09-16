# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Ticket Price
    """
    _inherit = 'hr.contract'
    country_id = fields.Many2one('res.country', string='Country', related='employee_id.country_id')
    ticket_price = fields.Float(string='Ticket price')
    ticket_per_year = fields.Float(string='Number of ticket')
    amount_per_month = fields.Float(string='Price per month', store=True )




    @api.onchange('ticket_price', 'ticket_per_year')
    def compute_ticket_per_mount(self):
        for rec in self:
            rec.amount_per_month = (rec.ticket_per_year * rec.ticket_price) / 12



class CountryFlightTicket(models.Model):
    _inherit = 'res.country'
    # _name = 'country.flight.ticket'

    # country_id = fields.Many2one('res.country',string='Country')
    ticket_price = fields.Float(string='Ticket price')
    nationality_name = fields.Char(string='Nationality')


class HrFlightTicket(models.Model):
    _name = 'hr.flight.ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    # name = fields.Char()
    name = fields.Char(string="Ticket Name", default="/", readonly=True, help="Name of the Ticket")
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee")
    # employee_id = fields.Many2one('hr.leave', string='Employee', help="Employee", )
    amount = fields.Float(string="Amount", required=True, help="amount")
    employee_account_id = fields.Many2one('account.account', string="Expanse Account")
    treasury_account_id = fields.Many2one('account.account', string="Treasury Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    move_id = fields.Many2one('account.move', string="Account move")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('waiting_approval_2', 'Waiting Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )
    ticket_allocation_id = fields.Many2one('flight.ticket.allocation', string="Allocation")
    number_of_ticket = fields.Float(string="Number of Ticket")

    company_id = fields.Many2one('res.company', 'Company', help="Company",
                                 default=lambda self: self.env.company)

    # @api.model
    # def create(self, vals):
    #
    #     res = super(HrFlightTicket, self).create(vals)
    #     return res
    def action_submit(self):
        self.ticket_allocation_id = self.env['flight.ticket.allocation'].search(
            [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate')])

        if not self.ticket_allocation_id  or self.number_of_ticket > self.ticket_allocation_id.balance :
            raise ValidationError(_("insufficient Balance installment"))
        self.write({'state': 'waiting_approval_1'})

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.write({'state': 'approve'})

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                pass
                # raise UserError(
                #     'You cannot delete a request which is not in draft or cancelled state')
        return super(HrFlightTicket, self).unlink()


    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_cancel(self):
        if any(holiday.move_id.state in ['draft', 'posted'] for holiday in self):
            raise UserError(_('you must cancel the journal entry'))
        else:
            self.write({
                'state': 'cancel'
            })
            self.ticket_allocation_id.balance += self.number_of_ticket
            self.ticket_allocation_id.balance_taken -= self.number_of_ticket

    def action_approve(self):
        """This create account move for request.
            """
        pass
        loan_approve = self.env['ir.config_parameter'].sudo().get_param('account.ticket_approve')
        contract_obj = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
        if not contract_obj:
            raise UserError('You must Define a contract for employee')

        if loan_approve:
            self.write({'state': 'waiting_approval_2'})
        else:



            if not self.employee_account_id or not self.treasury_account_id or not self.journal_id:
                raise UserError("You must enter employee account & Treasury account and journal to approve ")
            elif self.ticket_allocation_id.balance < self.number_of_ticket :
                raise UserError("insufficient Ticket Balance")

            timenow = time.strftime('%Y-%m-%d')
            for tick in self:
                amount = tick.amount * self.number_of_ticket
                loan_name = tick.employee_id.name
                reference = tick.name
                journal_id = tick.journal_id.id
                debit_account_id = tick.treasury_account_id.id
                credit_account_id = tick.employee_account_id.id
                debit_vals = {
                    # 'name': loan_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    # 'loan_id': loan.id,
                }
                credit_vals = {
                    # 'name': loan_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    # 'loan_id': loan.id,
                }
                vals = {
                    # 'name': 'Ticket Fees For' + ' ' + loan_name + ' ' + tick.name,
                    'narration': loan_name,
                    # 'ref': reference,
                    'journal_id': journal_id,
                    'date': timenow,
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = self.env['account.move'].create(vals)
                # move.post()

            self.ticket_allocation_id.balance_taken += self.number_of_ticket
            self.ticket_allocation_id.balance -= self.number_of_ticket
            # print(self.ticket_balance_id.balance_taken)
            self.write({'state': 'approve', 'move_id': move.id})
            self.write({'state': 'approve'})
        return True



    def action_double_approve(self):
        """This create account move for request in case of double approval.
            """
        if not self.employee_account_id or not self.treasury_account_id or not self.journal_id:
            raise UserError("You must enter employee account & Treasury account and journal to approve ")
        # if not self.loan_lines:
        #     raise UserError('You must compute Loan Request before Approved')
        timenow = time.strftime('%Y-%m-%d')
        for tick in self:
            amount = tick.amount
            loan_name = tick.employee_id.name
            reference = tick.name
            journal_id = tick.journal_id.id
            debit_account_id = tick.treasury_account_id.id
            credit_account_id = tick.employee_account_id.id
            debit_vals = {
                # 'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                # 'loan_id': loan.id,
            }
            credit_vals = {
                # 'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                # 'loan_id': loan.id,
            }
            vals = {
                # 'name': 'Ticket Fees For' + ' ' + loan_name + ' ' + tick.name,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.post()
        self.ticket_balance_id.balance_taken = self.ticket_balance_id.balance_taken + self.amount
        self.write({'state': 'approve', 'move_id': move.id})
        return True

    def action_view_invoice(self):
        return {
            'name': _('Flight Ticket Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'type':'in_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_id.id,
        }
