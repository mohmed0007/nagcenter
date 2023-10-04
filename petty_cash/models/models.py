from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class AccountMove(models.Model):
    _inherit = 'account.move'

    petty_cash = fields.Many2one('financial.dependents', string='Petty Cash')
    clearance_id = fields.Many2one('liquidation.dependents', string='Clearance')
    
    
class FinancialDependents(models.Model):
    _name = 'financial.dependents'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'New Description'

    @api.model
    def _get_default_conf_dep_journal(self):
        company = self.env.company.id
        param_obj = self.env['petty.cash.settings'].search([('company_id','=',company)])
        return param_obj.conf_dep_journal

    @api.model
    def _get_default_conf_dep_account_1(self):
        company = self.env.company.id
        param_obj = self.env['petty.cash.settings'].search([('company_id', '=', company)])
        return param_obj.conf_dep_account_1


    @api.model
    def _get_default_conf_cre_account_2(self):
        company = self.env.company.id
        param_obj = self.env['petty.cash.settings'].search([('company_id', '=', company)])
        return param_obj.conf_cre_account_2


    @api.onchange('emp_partner_id')
    def onchange_set_code_req(self):
        for rec in self:
            return {'domain': {'emp_partner_id': [('emp_tick', '=', 'True')]}}

    @api.onchange('credit_account_custom')
    def onchange_set_credit_account_custom_req(self):
        for rec in self:
            return {'domain': {'credit_account_custom': [('user_type_id', '=', 'Bank and Cash')]}}

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)

    dep_journal_id = fields.Many2one('account.journal', string='Journal', default=_get_default_conf_dep_journal,
                                      domain="[('company_id', '=', company_id)]")
    name = fields.Char(string="Sequence", readonly=1)

    dep_amount = fields.Float(string='Amount')
    liquidated_amount = fields.Float(string='Liquidated Amount', default=0.0)
    dep_date = fields.Date(string='Date',default=fields.Date.today())
    dep_memo = fields.Char(string='Description')

    dep_dibet_account = fields.Many2one('account.account', string='Debit Account', readonly=1,
                                        default=_get_default_conf_dep_account_1,
                                        domain="[('company_id', '=', company_id)]")
    credit_cridet_account = fields.Many2one('account.account', string='Credit Account', readonly=1,
                                            default=_get_default_conf_cre_account_2,
                                            domain="[('company_id', '=', company_id)]")
    credit_account_custom = fields.Many2one('account.account', string='Credit Account')
    # ,default=self.credit_cridet_account.id

    emp_partner_id = fields.Many2one('res.partner', string='Employee')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('manager', 'Manager Approve'),
        ('done', 'Done'),], string='Status', track_visibility='onchange', default='draft')
    sequence = fields.Boolean(string='Sequence', default=True)
    config_tick = fields.Boolean(string='tick', default=True)
    account_move = fields.Many2one('account.move', string='Journal Entry')

    def create_aprove(self):
        move_obj = self.env['account.move']
        move_id = move_obj.create({
            'ref': self.name,
            'state': 'draft',
            'journal_id': self.dep_journal_id.id,
            'date': self.dep_date,
            'petty_cash': self.id,
        })
        obj_move_line = self.env['account.move.line']
        obj_move_line.with_context(check_move_validity=False).create({
            'name': 'PettyCash',
            'move_id': move_id.id,
            'account_id': self.credit_account_custom.id,
            'credit': self.dep_amount,
            'debit': 0.0,
            'journal_id': self.dep_journal_id.id,
            'date_maturity': self.dep_date, })

        obj_move_line.with_context(check_move_validity=False).create({
            'name': 'PettyCash',
            'move_id': move_id.id,
            'account_id': self.dep_dibet_account.id,
            'credit': 0.0,
            'debit': self.dep_amount,
            'journal_id': self.dep_journal_id.id,
            'partner_id': self.emp_partner_id.id,
            'date_maturity': self.dep_date, })
        move_id._recompute_tax_lines(recompute_tax_base_amount=True)
        move_id.action_post()
        self.account_move = move_id.id
        self.state = 'done'


    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('financial.dependents') or '/'
        vals['name'] = seq
        res = super(FinancialDependents, self).create(vals)
        return res

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You Can't delete any record not in draft."))
            else:
                return super(FinancialDependents, self).unlink()

    def set_draft(self):
        for rec in self:
            if self.account_move:
                self.account_move.button_cancel()
            rec.write({'state':'draft'})

    def manager_approve(self):
        for rec in self:
            rec.write({'state':'manager'})


class LiquidationDependents(models.Model):
    _name = 'liquidation.dependents'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'New Description'

    @api.model
    def _get_default_conf_dep_journal(self):
        company = self.env.company.id
        param_obj = self.env['petty.cash.settings'].search([('company_id', '=', company)])
        return param_obj.conf_dep_journal

    @api.model
    def _get_default_credit_liq_account(self):
        company = self.env.company.id
        param_obj = self.env['petty.cash.settings'].search([],limit=1)
        return param_obj.conf_cre_account_2

    @api.model
    def _get_default_debit_liq_account(self):
        param_obj = self.env['ir.config_parameter'].sudo()
        return int(param_obj.get_param('conf_dep_filtering_account_1')) or False

    @api.onchange('financial_dep_ids')
    def _onchange_financial_dep(self):
        total = 0
        for rec in self.financial_dep_ids:
            total += rec.dep_amount
        self.custody_amount = total

    @api.onchange('liq_partner_id')
    def onchange_liq_partner_id(self):
        if self.liq_partner_id:
            domain = [('emp_partner_id', '=', self.liq_partner_id.id)]
            return {'domain': {'financial_dep_ids': domain}}

    name = fields.Char(string='Descrption')
    account_move = fields.Many2one('account.move', string='Journal Entry')
    liq_journal_id = fields.Many2one('account.journal', string='Journal', default=_get_default_conf_dep_journal,
                                     readonly=True, domain="[('company_id', '=', company_id)]")
    # name = fields.Char(string="Sequence Liquidation Dependents", readonly=1)
    sequence_liquidation = fields.Char(string='Sequence Liquidation')
    financial_dep_ids = fields.Many2many('financial.dependents', string="Origin")
    custody_amount = fields.Float(string='Custody Amount')
    total_amount_liq = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    date_liq = fields.Date(string='Date', required=True,default=fields.Date.today())
    dep_memo = fields.Char(string='Description')
    liq_line_ids = fields.One2many('liquidation.line', 'liq_dep_id', string="Clearance Lines")
    credit_liq_account = fields.Many2one('account.account', string='Credit Account', readonly=1,
                                         default=_get_default_credit_liq_account,
                                         domain="[('company_id', '=', company_id)]")
    deb_liq_account = fields.Many2one('account.account', string='Debit Account', readonly=1,
                                      default=_get_default_debit_liq_account,
                                      domain="[('company_id', '=', company_id)]")

    liq_partner_id = fields.Many2one('res.partner', string='Employee',domain=" [('emp_tick', '=', 'True')]")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'), ], string='Status', default='draft',track_visibility='onchange',)

    @api.model
    def create(self, vals):

        seq = self.env['ir.sequence'].next_by_code('liquidation.dependents') or '/'
        vals['sequence_liquidation'] = seq
        res = super(LiquidationDependents, self).create(vals)
        return res

    def action_confirm(self):
        # if not self.attachment_ids:
        #     raise ValidationError(_('You can only create request for you or for direct employees'))
        for line in self.liq_line_ids:
            fin_dep = line.financial_dep
            total = fin_dep.dep_amount
            new_amount = fin_dep.liquidated_amount + line.amount_liq

            fin_dep.write({'liquidated_amount': new_amount})
            if new_amount == total:
                fin_dep.write({'state': 'fully'})
            elif new_amount > 0 and fin_dep.state != 'partially':
                fin_dep.write({'state': 'partially'})
        move_obj = self.env['account.move']
        move_id = move_obj.create({
            'ref': self.sequence_liquidation,
            'journal_id': self.liq_journal_id.id,
            'date': self.date_liq,
        })
        print("self.credit_liq_account.id>>>>>>>>>>>>>>>>>",self.credit_liq_account.id)
        self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': "Liquidation",
            'move_id': move_id.id,
            'account_id': self.credit_liq_account.id,
            'credit': self.total_amount_liq,
            'debit': 0.0,

            'partner_id': self.liq_partner_id.id,
            # 'tax_ids': [(6, 0, [line.tax_liquid_id.id])],

        })
        for rec in self:
            for line in rec.liq_line_ids:
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    'move_id': move_id.id,
                    'account_id': line.liq_account_id.id,
                    'credit': 0.0,
                    'debit': line.amount_liq,
                    'partner_id': line.partner_id.id,
                    'tax_ids': [(6, 0, [line.tax_liquid_id.id])],

                    
                    # 'journal_id':rec.liq_partner_id.id,
                    # 'date_maturity':rec.date_liq
                })
                
        m = move_id.with_context(check_move_validity=False)


        m._recompute_tax_lines(recompute_tax_base_amount=False)
        # move_id._onchange_recompute_dynamic_lines()
        move_id.action_post()
        self.account_move = move_id.id
        self.state = 'done'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Please Upload clearance documents."))
            else:
                return super(LiquidationDependents, self).unlink()

    def set_draft(self):
        for rec in self:
            if self.account_move:
                self.account_move.button_cancel()
            rec.write({'state': 'draft'})

    def name_get(self):
        result = []
        for rec in self:
            name = rec.sequence_liquidation
            result.append((rec.id, name))
        return result

    @api.depends('liq_line_ids.sub_amount_liq')
    def _compute_total_amount(self):
        total = sum(self.liq_line_ids.mapped('sub_amount_liq'))
        self.total_amount_liq = total


class DependentsSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def get_values(self):
        res = super(DependentsSettings, self).get_values()
        param_obj_dep = self.env['ir.config_parameter'].sudo()
        res.update(
            conf_dep_journal=int(param_obj_dep.get_param('conf_dep_journal', default='0')),
            conf_dep_account_1=int(param_obj_dep.get_param('conf_dep_account_1', default='0')),
            conf_cre_account_2=int(param_obj_dep.get_param('conf_cre_account_2', default='0')),
            conf_dep_filtering_journal=int(param_obj_dep.get_param('conf_dep_filtering_journal', default='0')),
            conf_dep_filtering_account_1=int(param_obj_dep.get_param('conf_dep_filtering_account_1', default='0')),
            conf_cre_filtering_account_2=int(param_obj_dep.get_param('conf_cre_filtering_account_2', default='0'))
        )
        return res

    def set_values(self):
        res = super(DependentsSettings, self).set_values()
        param_obj_dep = self.env['ir.config_parameter'].sudo()
        param_obj_dep.set_param('conf_dep_journal', self.conf_dep_journal and self.conf_dep_journal.id or False)
        param_obj_dep.set_param('conf_dep_account_1', self.conf_dep_account_1 and self.conf_dep_account_1.id or False)
        param_obj_dep.set_param('conf_cre_account_2', self.conf_cre_account_2 and self.conf_cre_account_2.id or False)
        param_obj_dep.set_param('conf_dep_filtering_journal',
                                self.conf_dep_filtering_journal and self.conf_dep_filtering_journal.id or False)
        param_obj_dep.set_param('conf_dep_filtering_account_1',
                                self.conf_dep_filtering_account_1 and self.conf_dep_filtering_account_1.id or False)
        param_obj_dep.set_param('conf_cre_filtering_account_2',
                                self.conf_cre_filtering_account_2 and self.conf_cre_filtering_account_2.id or False)
        return res

    conf_dep_journal = fields.Many2one('account.journal', string='Defuelt journal')

    conf_dep_account_1 = fields.Many2one('account.account', string='Defuelt Debit Account')
    conf_cre_account_2 = fields.Many2one('account.account', string='Defuelt Credit Account')

    conf_dep_filtering_journal = fields.Many2one('account.journal', string='Defuelt journal')

    conf_dep_filtering_account_1 = fields.Many2one('account.account', string='Defuelt Debit Account')
    conf_cre_filtering_account_2 = fields.Many2one('account.account', string='Defuelt Credit Account')

    @api.model
    def get_default_name(self):
        mado = self.conf_dep_journal
        return mado


class PettyCashSettings(models.Model):
    _name = 'petty.cash.settings'

    conf_dep_journal = fields.Many2one('account.journal', string='Defuelt journal')

    conf_dep_account_1 = fields.Many2one('account.account', string='Defuelt Debit Account')
    conf_cre_account_2 = fields.Many2one('account.account', string='Defuelt Credit Account')

    conf_dep_filtering_journal = fields.Many2one('account.journal', string='Defuelt journal')

    conf_dep_filtering_account_1 = fields.Many2one('account.account', string='Defuelt Debit Account')
    conf_cre_filtering_account_2 = fields.Many2one('account.account', string='Defuelt Credit Account')

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)

    def name_get(self):
        result = []
        for rec in self:
            name = "Settings"
            result.append((rec.id, name))
        return result

    @api.model
    def create(self, values):
        company = self.env.company.id
        print ('aaaaaaaaaaaaaaaaaaaaaaaaaaa',company)
        count = self.env['petty.cash.settings'].search_count([('company_id','=',company)])
        print ('aaaaaaaaaaaaaaaaaaaaaaaaaaa',count,company)
        if count >0:
            raise ValidationError(_('You cant create more than one record by company'))
        return super(PettyCashSettings, self).create(values)


class LiquidationLine(models.Model):
    _name = 'liquidation.line'
    _description = 'Liquidation Line'

    name = fields.Char(string='Name')
    liq_account_id = fields.Many2one('account.account', string='Account',)
    # liq_account_id = fields.Many2one('account.account', string='Account',
                                     # domain=[('user_type_id', '=', 'Expenses')])
    amount_liq = fields.Float(string='Amount')
    description = fields.Text(string='Description')
    liq_dep_id = fields.Many2one('liquidation.dependents', string='Liquidation Dependent')
    financial_dep_ids = fields.Many2many(related='liq_dep_id.financial_dep_ids', string="financial dependents")
    financial_dep = fields.Many2one('financial.dependents', string='From')
    tax_liquid_id = fields.Many2one('account.tax', string='Tax')
    sub_amount_liq = fields.Float(string='Sub Amount')
    facility_name = fields.Char(string='Vendor')
    tax_id_liq = fields.Char(string='Tax ID')
    tax_id_liq = fields.Char(string='Tax ID')
    inv_num_liq = fields.Char(string='Inv Number')
    inv_date_liq = fields.Date(string='Inv Date',default=fields.Date.today())
    partner_id = fields.Many2one('res.partner', string='Partner')


    @api.onchange('financial_dep_ids')
    def list_financial_dep(self):
        domain = [('name', 'in', self.financial_dep_ids.mapped('name'))]
        return {'domain': {'financial_dep': domain}}

    @api.onchange('amount_liq')
    def list_amount_liq(self):
        if self.tax_liquid_id:
            self.sub_amount_liq = self.amount_liq + (self.amount_liq * (self.tax_liquid_id.amount * 1 / 100))
        else:
            self.sub_amount_liq = self.amount_liq

    @api.onchange('tax_liquid_id')
    def list_tax_liquid_id(self):
        self.sub_amount_liq = self.amount_liq + (self.amount_liq * (self.tax_liquid_id.amount * 1 / 100))

    @api.onchange('tax_liquid_id')
    def onchange_set_tax_liquid_id(self):
        for rec in self:
            return {'domain': {'tax_liquid_id': [('type_tax_use', '=', 'purchase')]}}
