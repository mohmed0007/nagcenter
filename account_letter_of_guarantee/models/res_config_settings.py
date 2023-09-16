# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    lq_account_exp_id = fields.Many2one('account.account', related="company_id.lq_account_exp_id", readonly=False, string='Commission Expence Account', domain="[('deprecated', '=', False), ('company_id', '=', company_id),('internal_group', 'in', ('expense','income'))]")
    lq_account_accr_exp_id = fields.Many2one('account.account',related="company_id.lq_account_accr_exp_id", readonly=False, string='Quarantee Receivable Account', domain="[('deprecated', '=', False), ('company_id', '=', company_id),('user_type_id.type', '=', 'receivable')]")

    lq_journal_id = fields.Many2one('account.journal', related="company_id.lq_journal_id", readonly=False, string='Journal', domain="[('type', '=', 'bank'), ('company_id', '=', company_id)]")
    lq_account_analytic_id = fields.Many2one('account.analytic.account', related="company_id.lq_account_analytic_id", readonly=False, string='Analytic Account')

