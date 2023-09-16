# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, time
from .hijri_date import HijriDate

import re

class AccountLetterOfGurantee(models.Model):
    _name = "account.guarantee"
    _description = 'Letter of Quarantee'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_lq_account_exp_id(self):
        account = self.env.company.sudo().lq_account_exp_id and self.env.company.sudo().lq_account_exp_id.id or False
        return account

    @api.model
    def _get_default_lq_account_accr_exp_id(self):
        account = self.env.company.sudo().lq_account_accr_exp_id and self.env.company.sudo().lq_account_accr_exp_id.id or False
        return account

    @api.model
    def _get_default_lq_journal_id(self):
        journal = self.env.company.sudo().lq_journal_id and self.env.company.sudo().lq_journal_id.id or False
        return journal

    @api.model
    def _get_default_lq_account_analytic_id(self):
        analytic = self.env.company.sudo().lq_account_analytic_id and self.env.company.sudo().lq_account_analytic_id.id
        return analytic
        
    name = fields.Char(readonly=True,default='New',copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete="cascade")
    quar_desc = fields.Text(string='Description')
    quar_no = fields.Char(string='Quarantee No.')
    quar_type = fields.Selection([('initial', 'Initial'), ('final', 'Final')], 'Quarantee Type', copy=False, required=True)
    quar_amount = fields.Float(string='Quatantee Amount', digits='Product Price', readonly=False, default=0.0)
    quar_commi_amount = fields.Float(string='Commission Amount', digits='Product Price', readonly=False, default=0.0)

    date = fields.Date(string='Accounting Date')
    date_h = fields.Char(string='Date(Hijri)')
    expiry_date = fields.Date(string='Expiry Date')

    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.company)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm','Confirmed'),
                              ('done', 'Validated'), 
                              ('returned', 'Returned'),
                              ('cancel','Cancelled')], 'Status', copy=False, default='draft')
    active = fields.Boolean(default=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',default=_get_default_lq_account_analytic_id,  domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", states={'returned': [('readonly', True)]})

    reversed_entry_id = fields.Many2one('account.move', string='Reversed Entry', ondelete='cascade', states={'returned': [('readonly', True)]})
    reversed_entry_date = fields.Date(string='Return Date', states={'returned': [('readonly', True)]})

    depreciation_move_ids = fields.One2many('account.move', 'quar_id', string='Quarantee Letter Entries', readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)], 'paused': [('readonly', False)]})


    account_exp_id = fields.Many2one('account.account', string='Commission Expence Account',default=_get_default_lq_account_exp_id, readonly=True, states={'draft': [('readonly', False)], 'model': [('readonly', False)]}, domain="[('deprecated', '=', False), ('company_id', '=', company_id),('internal_group', 'in', ('expense','income'))]")
    account_accr_exp_id = fields.Many2one('account.account', string='Quarantee Receivable Account',default=_get_default_lq_account_accr_exp_id, readonly=True, states={'draft': [('readonly', False)]}, domain="[('deprecated', '=', False), ('company_id', '=', company_id),('internal_type', 'in', ('receivable'))]")

    journal_id = fields.Many2one('account.journal', string='Journal',default=_get_default_lq_journal_id,  readonly=True, states={'draft': [('readonly', False)], 'model': [('readonly', False)]}, domain="[('type', '=', 'bank'), ('company_id', '=', company_id)]")

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('letter.gurantee')
        vals.update({
            'name': number,
        })
        return super(AccountLetterOfGurantee, self).create(vals)
            
    @api.onchange('date')
    def _ct_ct_ct_date_date_ff(self):
        if self.date:
            um = HijriDate()
            date_entry = fields.Datetime.from_string(self.date)
            um.set_date_from_gr(date_entry.year, date_entry.month, date_entry.day)
            self.date_h = str(format(int(um.day), '02d')) + '-' + str(format(int(um.month), '02d')) + '-' + str(int(um.year))

    @api.onchange('date_h')
    def _ct_ct_ct_date_h_date_h_ff_hh(self):
        if self.date_h:
            um = HijriDate()
            d, m, y = map(int, self.date_h.split('-'))
            um.set_date(y, m, d)
            x = str(int(um.day_gr)) + '-' + str(int(um.month_gr)) + '-' + str(int(um.year_gr))
            self.date = datetime.strptime(x, '%d-%m-%Y')
    
    def action_confirm(self):
        
        self.write({'state':'confirm'})
        
    def action_cancel(self):
        
        self.write({'state':'cancel'})
        
    def action_set_to_draft(self):
        
        self.write({'state':'draft'})
    
    def compute_rent_reverse(self):
        self.ensure_one()
        if not self.reversed_entry_date:
            raise UserError(_("Please Enter Return Date!"))
        depreciation_date = self.date
        entr = self.env['account.move']._prepare_move_for_quar_reverse_depreciation({
                'amount': self.quar_amount,
                'quar_id': self,
                # 'move_ref': _("Return Letter of Quarantee of ") + "/ " + str(self.partner_id and self.partner_id.name or ''),
                'move_ref': _("Return Letter of Quarantee of ") + "/ " + self.name,
                'partner_id': self.partner_id.id,
                #'commi_contract_no': self.commi_contract_no,
                'date': self.reversed_entry_date,
                })
   
        new_moves = self.env['account.move'].create(entr)
        new_moves.action_post()
        self.write({'reversed_entry_id': new_moves.id, 'state': 'returned'})

    def compute_rent_board(self):
        self.ensure_one()
        if not self.date:
            raise UserError(_('Please Enter Accounting Date'))
        depreciation_date = self.date
        self.depreciation_move_ids = [(6, 0, [])]
        commands = [(2, line_id.id, False) for line_id in self.depreciation_move_ids.filtered(lambda x: x.state in ('draft', 'posted'))]
        entr = self.env['account.move']._prepare_move_for_quar_depreciation({
                'amount': self.quar_amount + self.quar_commi_amount,
                'amount2': self.quar_amount,
                'amount3': self.quar_commi_amount,
                'quar_id': self,
                # 'move_ref': _("Quarantee Letter of ") + "/ " + str(self.partner_id and self.partner_id.name or ''),
                'move_ref': _("Quarantee Letter of ") + "/ " + self.name,
                'partner_id': self.partner_id.id,
                #'commi_contract_no': self.commi_contract_no,
                'date': depreciation_date,
                })
   
        new_moves = self.env['account.move'].create(entr)
        new_moves.action_post()
        for move in new_moves:
            commands.append((4, move.id))

        return self.write({'depreciation_move_ids': commands, 'state': 'done'})


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You can not delete record not in draft state'))



    

