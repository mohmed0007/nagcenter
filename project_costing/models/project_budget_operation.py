# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProjectBudgerOperation(models.Model):
    _name = 'project.budget.operation'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Operation Reference', required=True, index=True, copy=False, 
                       default=lambda self: self.env['ir.sequence'].next_by_code('budget.operation'))
    project_cost_id = fields.Many2one('project.budget', string="Budget" , ondelete="restrict")
    project_id = fields.Many2one('project.project', string='Project', ondelete="restrict")
    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account', related='project_cost_id.analytic_account_id')
    operation_line_ids = fields.One2many('project.budget.operation.line', 'budget_operation_id', string='Operation Lines')
    currency_id = fields.Many2one('res.currency', related='project_cost_id.currency_id', string='Currency', store=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
    note = fields.Text('Note')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
        ('validate', 'Validated'),
        ('done', 'Done')
        ], 'Status', default='draft', index=True, required=True, readonly=True, copy=False, tracking=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    
    
    @api.onchange('project_cost_id')
    def onchange_project_cost_id(self):
        self.company_id = self.project_cost_id.company_id        
    
    
    def action_confirm(self):
        for rec in self:
            if not rec.operation_line_ids:
                raise ValidationError(_("You have to enter operation items."))
            amount_from = 0
            amount_to = 0
            for line in rec.operation_line_ids:
                amount_from += line.amount_from
                amount_to += line.amount_to
            if amount_from != amount_to:
                raise ValidationError(_("Total Transferred amount should be equal to total received amount"))
                
        self.write({'state': 'confirm'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_validate(self):
        self.write({'state': 'validate'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_done(self):
        self.write({'state': 'done'})
        for rec in self:
            for line in rec.operation_line_ids.filtered(lambda r: r.item_type == 'new'):
                vals = {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'account_id': line.account_id.id,
                    'project_cost_id': line.project_cost_id.id,
                    'calc_actual': line.calc_actual
                }
                new_budget_line = self.env['project.budget.lines'].create(vals)
                line.project_budget_line = new_budget_line

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('You can not delete records not in draft state'))
        return super(ProjectBudgerOperation ,self).unlink()

class ProjectBudgerOperation(models.Model):
    _name = 'project.budget.operation.line'
    
    budget_operation_id = fields.Many2one('project.budget.operation', string='Budget Operation', ondelete="cascade")
    project_cost_id = fields.Many2one('project.budget', string="Budget", related='budget_operation_id.project_cost_id')
    item_type = fields.Selection([('exist','Existed Item'),('new','Create New Item')], string='Item Type')
    project_budget_line = fields.Many2one('project.budget.lines', string='Budget Item')
    action = fields.Selection([('from','From Item'),('to','To Item')],'Transfer Type')
    currency_id = fields.Many2one('res.currency', related='project_cost_id.currency_id', string='Currency')
    amount_from = fields.Monetary('Transferred Amount', help='Amount to be transferred to other items')
    amount_to = fields.Monetary('Received Amount', help='Amount to be received from other items')
    product_id = fields.Many2one('product.product','Product')
    name = fields.Text('Description')
    remaining_amount = fields.Monetary('Remaining Amount', copy="False")
    account_id = fields.Many2one('account.account', string='Account',
                                 domain="[('deprecated', '=', False), ('company_id', '=', company_id), ('is_off_balance', '=', False)]")
    company_id = fields.Many2one('res.company', 'Company', related='budget_operation_id.company_id', store=True)
    state = fields.Selection(related='budget_operation_id.state', string='state', store=True)
    calc_actual = fields.Selection([('delivery','Stock Delivery'),('account','Item Account')], 
                                   string='Actual Calc. On' )
    
    @api.constrains('amount_from')
    def check_amount_from(self):
        for rec in self:
            if rec.amount_from > rec.remaining_amount:
                raise ValidationError(
                    _("Transferred Amount for the item %s should be less or equal to %s.")%(rec.name,rec.remaining_amount))
                
    
    @api.onchange('project_budget_line','product_id')
    def onchange_budget_line(self):
        for rec in self:
            rec.product_id = rec.project_budget_line.product_id or rec.product_id
            rec.name = rec.project_budget_line.name or rec.product_id.name
            rec.account_id = rec.project_budget_line.account_id or rec.product_id._get_product_accounts()['expense']
            rec.remaining_amount = rec.project_budget_line.remaining_amount or 0
            calc_actual = rec.product_id.detailed_type == 'service' and 'account' or 'delivery'
            rec.calc_actual =  rec.project_budget_line.calc_actual or calc_actual     
    
    @api.onchange('action')
    def onchange_action(self):
        if self.action == 'from':
            self.item_type = 'exist'