# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_compare 

class AccountMove(models.Model):
    _inherit = 'account.move'

    quar_id = fields.Many2one('account.guarantee', string='Letter Of Guarantee', index=True, ondelete='cascade', copy=False, domain="[('company_id', '=', company_id)]")

    @api.model
    def _prepare_move_for_quar_depreciation(self, vals):
        
        asset = vals['quar_id']
        account_analytic_id = asset.account_analytic_id
        depreciation_date = vals.get('date', fields.Date.context_today(self))
        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        prec = company_currency.decimal_places
        amount = current_currency._convert(vals['amount'], company_currency, asset.company_id, depreciation_date)
        amount2 = current_currency._convert(vals['amount2'], company_currency, asset.company_id, depreciation_date)
        amount3 = current_currency._convert(vals['amount3'], company_currency, asset.company_id, depreciation_date)
        move_line_bank_1 = {
            'name': vals['move_ref'],
            # 'account_id': asset.journal_id.default_credit_account_id.id or asset.journal_id.default_debit_account_id.id or,
            'account_id': asset.journal_id.default_account_id.id ,
            # 'partner_id': vals['partner_id'],
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            # 'analytic_account_id': account_analytic_id.id if asset.account_accr_exp_id.user_type_id.internal_group == 'expense' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * vals['amount'] or 0.0,
        }
        
        move_line_rece_1 = {
            'name': vals['move_ref'],
            'account_id': asset.account_accr_exp_id.id,
            # 'partner_id': vals['partner_id'],
            'credit': 0.0 if float_compare(amount2, 0.0, precision_digits=prec) > 0 else -amount2,
            'debit': amount2 if float_compare(amount2, 0.0, precision_digits=prec) > 0 else 0.0,
            # 'analytic_account_id': account_analytic_id.id if asset.account_exp_id.user_type_id.internal_group == 'expense' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and vals['amount2'] or 0.0,
        }
        move_line_comm_2 = {
            'name': vals['move_ref'],
            'account_id': asset.account_exp_id.id,
            # 'partner_id': vals['partner_id'],
            'credit': 0.0 if float_compare(amount3, 0.0, precision_digits=prec) > 0 else -amount3,
            'debit': amount3 if float_compare(amount3, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id if asset.account_exp_id.user_type_id.internal_group == 'expense' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and vals['amount3'] or 0.0,
        }
        
        move_vals_1 = {
            'ref': vals['move_ref'],
            'date': depreciation_date,
            'journal_id': asset.journal_id.id,
            'line_ids': [(0, 0, move_line_rece_1), (0, 0, move_line_comm_2), (0, 0, move_line_bank_1)],
            #'auto_post': asset.state == 'open',
            'quar_id': asset.id,
            'amount_total': amount,
            'name': '/',
            'move_type': 'entry',
        }
        
        return move_vals_1


    @api.model
    def _prepare_move_for_quar_reverse_depreciation(self, vals):
        
        asset = vals['quar_id']
        account_analytic_id = asset.account_analytic_id
        depreciation_date = vals.get('date', fields.Date.context_today(self))
        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        prec = company_currency.decimal_places
        amount = current_currency._convert(vals['amount'], company_currency, asset.company_id, depreciation_date)

        move_line_bank_1 = {
            'name': vals['move_ref'],
            # 'account_id': asset.journal_id.default_credit_account_id.id or asset.journal_id.default_debit_account_id.id,
            'account_id': asset.journal_id.default_account_id.id,
            # 'partner_id': vals['partner_id'],
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else abs(amount),
            'debit': abs(amount) if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            # 'analytic_account_id': account_analytic_id.id if asset.account_accr_exp_id.user_type_id.internal_group == 'expense' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and (vals['amount'] > 0 and vals['amount'] or -1.0 * vals['amount']) or 0.0,
        }
        
        move_line_rece_1 = {
            'name': vals['move_ref'],
            'account_id': asset.account_accr_exp_id.id,
            # 'partner_id': vals['partner_id'],
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else abs(amount),
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            # 'analytic_account_id': account_analytic_id.id if asset.account_exp_id.user_type_id.internal_group == 'expense' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and (vals['amount'] < 0 and vals['amount'] or -1.0 * vals['amount']) or 0.0,
        }
        
        move_vals_1 = {
            'ref': vals['move_ref'],
            'date': depreciation_date,
            'journal_id': asset.journal_id.id,
            'line_ids': [(0, 0, move_line_bank_1), (0, 0, move_line_rece_1)],
            #'auto_post': asset.state == 'open',
            'quar_id': asset.id,
            'amount_total': amount,
            'name': '/',
            'move_type': 'entry',
        }
        
        return move_vals_1



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    quar_id = fields.Many2one('account.guarantee', string='Letter Of Guarantee', ondelete="set null", copy=False)
