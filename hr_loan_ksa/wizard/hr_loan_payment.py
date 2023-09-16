# -*- coding: utf-8 -*-
from odoo import models, fields, api , _
from odoo.exceptions import UserError , ValidationError
import time
from dateutil import relativedelta
from datetime import date,datetime
from dateutil.relativedelta import relativedelta




class LoanPayment(models.TransientModel):
    _name = "hr.loan.payment"
    _description = "Register Loan Payment"

    amount = fields.Monetary(string='Payment Amount', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Payment Method', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))])
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True, copy=False)
    loan_id = fields.Many2one('hr.loan')
    debit_account_id = fields.Many2one('account.account', string="Employee Account")
    config_id = fields.Many2one('hr.allocation.accounting.configuration' , string= "Configuration")

    @api.model
    def default_get(self, fields):
        rec = super(LoanPayment, self).default_get(fields)
        if rec.get('loan_id'):
            loan_id = self.env['hr.loan'].browse(rec.get('loan_id'))
            rec['amount'] = loan_id.mapped('loan_amount')[0]
        return rec

    # def action_validate_loan_payment(self):
    #     for loan in self.loan_id:
    #         payment_id = self.env['account.payment'].create(self.loan_payment_create(loan))
    #         payment_id.action_post()
    #         loan.payment_done = True


    def action_validate_loan_payment(self):
        for rec in self:
            if not rec.loan_id.employee_id.address_home_id:
                    raise UserError(_('The employee must have a home address.'))
            # if not eos.employee_id.address_home_id.property_account_payable_id.id:
            #     raise UserError(_('The employee must have a payable account set on his home address.'))
            # company_currency = rec.company_id.currency_id.id
            # diff_currency_p = rec.currency_id.id != company_currency
            eml = []
            if not rec.journal_id:
                raise UserError(_('Please configure  journal.'))
            timenow = time.strftime('%Y-%m-%d')
            amount = 0.0
            print(type(rec.amount) , "ne"*10)
            amount -= rec.amount
            # eos_name = rec.name.split('\n')[0][:64]
            reference = rec.loan_id.name
            journal_id = rec.journal_id.id
            # partner = rec.employee_id.address_home_id.id
            debit_account_id =  rec.journal_id.default_account_id.id
            credit_account_id = rec.config_id.loan_Payment_account.id
            if not debit_account_id:
                raise UserError(_("Please configure %s journal's debit account.") % rec.journal_id.name)
            debit_vals = {
                'name': rec.loan_id.name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'partner_id': rec.loan_id.employee_id.address_home_id.id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                'analytic_account_id': rec.loan_id.employee_id.contract_id.analytic_account_id.id or False,
            }
            credit_vals = {
                'name': rec.loan_id.name,
                'account_id': credit_account_id,
                'partner_id': rec.loan_id.employee_id.address_home_id.id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                'analytic_account_id': rec.loan_id.employee_id.contract_id.analytic_account_id.id or False,
            }
            vals = {
                'name': '/',
                'narration': rec.loan_id.name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            self.loan_id.write({'account_move_id': move.id})
    # def loan_payment_create(self, loan):
    #     self.ensure_one()
    #
    #     # x = self.journal_id.inbound_payment_method_line_ids
    #     # y = self.bank_journal_id.inbound_payment_method_line_ids
    #     # try:
    #     #     if x.mapped('payment_account_id'):
    #     #         outbound = max(y.mapped('payment_account_id'))
    #     #         print(outbound, "outbound" * 3)
    #     #         # self.journal_default_account_id = outbound
    #     # except:
    #     #     raise UserError(
    #     #         _("Missing 'Outstanding Receipts Account' on the bank journal '%s'.")
    #     #         % self.bank_journal_id.display_name
    #     #     )
    #     # payment_methods = self.journal_id.outbound_payment_method_ids
    #     if not loan.employee_id.address_home_id:
    #         raise UserError('You must Define a Private address for employee.')
    #     return {
    #         'payment_type': 'outbound',
    #         # 'payment_method_id': payment_methods and payment_methods[0].id or False,
    #         'partner_type': 'customer',
    #         'partner_id': loan.employee_id.address_home_id.id,
    #         'amount': loan.loan_amount,
    #         'currency_id': self.currency_id.id,
    #         'date': self.payment_date,
    #         'journal_id': self.journal_id.id,
    #         'company_id': loan.company_id.id,
    #         'ref': loan.name,
    #     }


class LoanReschedule(models.TransientModel):
    _name = "hr.loan.reschedule"
    _description = "Loan Reschedule"

    amount = fields.Monetary(string='Amount')
    date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True, copy=False)
    loan_id = fields.Many2one('hr.loan')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    installment = fields.Integer(string="No of Installments", default=1, help="Number of installments")

    @api.model
    def default_get(self, fields):
        rec = super(LoanReschedule, self).default_get(fields)
        if rec.get('loan_id'):
            loan_id = self.env['hr.loan'].browse(rec.get('loan_id'))
            print(self.env['hr.loan'].browse(rec.get('loan_id')) , rec.get('loan_id'),'kkjdfhkdfhfd7eeee7e77e77e')
            rec['amount'] = loan_id.mapped('balance_amount')[0]
            rec['installment'] = loan_id.mapped('installment')[0] - len(loan_id.loan_lines.filtered(lambda r: r.paid == True))
        return rec

    def action_validate_loan_payment1(self):
        # to_be_deleted = self.loan_id.loan_lines.filtered(lambda r: r.paid == False)
        # for line in to_be_deleted :
        #     line.unlink()
        #     print(line , 'line'*4)
        for loan in self:
            to_be_deleted = loan.loan_id.loan_lines.filtered(lambda r: r.paid == False)
            print(to_be_deleted)
            for line in to_be_deleted:
                line.unlink()
                # loan.loan_id.write({'loan_lines': [(4, line.id)]})
                # print(line, 'line' * 4)
            date_start = datetime.strptime(str(loan.date), '%Y-%m-%d')
            amount = loan.amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.loan_id.employee_id.id,
                    'loan_id': loan.loan_id.id})
                date_start = date_start + relativedelta(months=1)
            loan.loan_id._compute_loan_amount()
        return True








