# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"
    
    lq_account_exp_id = fields.Many2one('account.account', string='Commission Expence Account', domain="[('deprecated', '=', False), ('company_id', '=', company_id),('internal_group', 'in', ('expense','income'))]")
    lq_account_accr_exp_id = fields.Many2one('account.account', string='Quarantee Receivable Account', domain="[('deprecated', '=', False), ('company_id', '=', company_id),('user_type_id.type', '=', 'receivable')]")

    lq_journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type', '=', 'bank'), ('company_id', '=', company_id)]")
    lq_account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')