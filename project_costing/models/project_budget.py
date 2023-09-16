# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectCost(models.Model):
    _name = 'project.budget'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    project_id = fields.Many2one('project.project', string='Project')
    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account')
    date_from = fields.Date('Start Date', states={'done': [('readonly', True)]})
    date_to = fields.Date('End Date', states={'done': [('readonly', True)]})
    company_id = fields.Many2one('res.company', 'Company', required=True,
        default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
        ('validate', 'Validated'),
        ('done', 'Done')
        ], 'Status', default='draft', index=True, required=True, readonly=True, copy=False, tracking=True)
    description = fields.Text('Description')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True, store=True)
    line_ids = fields.One2many('project.budget.lines', 'project_cost_id', string="Budget Items")
    project_budget_template_id = fields.Many2one('project.budget.template', string='Budget Template')
    stock_move_ids = fields.One2many('stock.move', 'project_cost_id', string="Stock Moves")
    allow_over_flow = fields.Boolean(string='Allow budget Overflow', default=False)
    budget_operation_ids = fields.One2many('project.budget.operation', 'project_cost_id', string="Budget Operations")
    budget_operation_line_ids = fields.One2many('project.budget.operation.line', 'project_cost_id', string="Operation Lines")
    project_warehouse_id = fields.Many2one('stock.warehouse', string='Projects Warehouse',
                                           related='company_id.project_warehouse_id', readonly=True, store=True)
    location_id = fields.Many2one('stock.location', string="Project Location", related="project_id.location_id")
    
    @api.onchange('project_budget_template_id')
    def _onchange_project_budget_template_id(self):
        budget_template = self.project_budget_template_id

        budget_lines_data = [fields.Command.clear()]
        budget_lines_data += [
            fields.Command.create(line._prepare_budget_line_values())
            for line in budget_template.budget_template_line_ids
        ]

        # set first line to sequence -99, so a resequence on first page doesn't cause following page
        # lines (that all have sequence 10 by default) to get mixed in the first page
        # if len(budget_lines_data) >= 2:
        #     budget_lines_data[1][2]['sequence'] = -99

        self.line_ids = budget_lines_data
        for line in self.line_ids:
            line.onchange_product_id()

    @api.onchange('project_id')
    def onchange_project_id(self):
        self.analytic_account_id = self.project_id.analytic_account_id
    
    def action_budget_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(
                    _("You have to enter at least one budget item."))
        self.write({'state': 'confirm'})

    def action_budget_draft(self):
        self.write({'state': 'draft'})

    def action_budget_validate(self):
        self.write({'state': 'validate'})

    def action_budget_cancel(self):
        self.write({'state': 'cancel'})

    def action_budget_done(self):
        self.write({'state': 'done'})
        
    def action_view_delivery(self):
        if not self.project_warehouse_id:
            raise ValidationError(
                    _("Please configure Projects warehouse from the settings."))
        if not self.location_id:
            raise ValidationError(
                    _("Please configure Project's location ."))
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        action['domain'] = [('project_id','=', self.project_id.id)]
        action['context'] = dict(self._context, default_project_id=self.project_id.id, 
                                 default_from_project=True, default_origin=self.name, default_project_cost_id=self.id,
                                 default_picking_type_id=self.project_warehouse_id.out_type_id.id,
                                 default_location_id=self.location_id.id)
        return action
    
    def action_view_operation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("project_costing.act_project_budget_operation_view")
        action['domain'] = [('project_id','=', self.project_id.id),('project_cost_id','=',self.id)]
        action['context'] = dict(self._context, default_project_id=self.project_id.id, default_project_cost_id=self.id)
        return action
    
    def action_view_purchase(self):
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        action['domain'] = [('project_id','=', self.project_id.id),('project_cost_id','=',self.id),
                            ('subcontractor','=',False)]
        action['context'] = dict(self._context, default_project_id=self.project_id.id, 
                                 default_project_cost_id=self.id, default_from_project=True)
        return action
    
    def action_view_subcontractor(self):
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        action['domain'] = [('project_id','=', self.project_id.id),('project_cost_id','=',self.id),
                            ('subcontractor','=',True)]
        action['context'] = dict(self._context, default_project_id=self.project_id.id, 
                                 default_project_cost_id=self.id, default_from_project=True, default_subcontractor=True)
        return action
    
    @api.constrains('date_from','date_to', 'analytic_account_id','state')
    def check_dates_overflow(self):
        self.ensure_one()
        if self.state in ['draft','cancel']:
            return True
        budgets = self.env['project.budget'].search([('analytic_account_id','=',self.analytic_account_id.id),('id','!=',self.id),('state','not in',['draft','cancel']),
                                                     #'&',
                                                     '|',
                                                     '&',
                                                     ('date_from','<=',self.date_from),('date_to','>=',self.date_from),
                                                     '&',
                                                     ('date_from','<=',self.date_to),('date_to','>=',self.date_to)])
        if budgets:
            raise ValidationError(
                    _("Budget for the project %s can't be overlapped in dates")%self.analytic_account_id.name)


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('You can not delete records not in draft state'))
        return super(ProjectCost,self).unlink()


class ProjectCostLines(models.Model):
    _name = 'project.budget.lines'

    project_cost_id = fields.Many2one('project.budget', string="Budget" , ondelete="cascade",)
    product_id = fields.Many2one('product.product','Item')
    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account', related="project_cost_id.analytic_account_id", store=True)
    account_id = fields.Many2one('account.account', string='Account',
                                 domain="[('deprecated', '=', False), ('company_id', '=', company_id), ('is_off_balance', '=', False)]")
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure',  readonly=False, default=1)
    planned_amount = fields.Monetary('Planned Amount', required=True,help="Amount you plan to spend.",
                                     default=0)
    practical_amount = fields.Monetary(compute='_compute_practical_amount', 
                                       string='Practical Amount', help="Amount really spent.", store=True)
    remaining_amount = fields.Monetary(compute='_compute_remaining_amount', 
                                       string='Remaining Amount', help="remaining of budget.", store=True)
    company_id = fields.Many2one('res.company', 'Company', related='project_cost_id.company_id', store=True)
    state = fields.Selection(related='project_cost_id.state', string='Status')
    is_above_budget = fields.Boolean(compute='_is_above_budget')
    currency_id = fields.Many2one('res.currency', related='project_cost_id.currency_id', readonly=True, store=True)
    name = fields.Text('Description')
    calc_actual = fields.Selection([('delivery','Stock Delivery'),('account','Item Account')], 
                                   string='Actual Calc. On' )
    stock_move_ids = fields.One2many('stock.move', 'project_budget_line', string="Stock Moves")
    operation_amount = fields.Monetary(compute='_compute_operation_amount', 
                                       string='Modification Amount', help='Amount resulted from Opeartion on Budgets', store=True)
    budget_operation_line_ids = fields.One2many('project.budget.operation.line', 'project_budget_line', string="Operation Lines")
    price_unit = fields.Float(string='Unit Price', digits='Product Price', default=1)
    
    @api.depends('account_id.move_line_ids','account_id.move_line_ids.parent_state',
                 'state','analytic_account_id', 'stock_move_ids', 
                 'stock_move_ids.stock_valuation_layer_ids', 'project_cost_id.state')
    def _compute_practical_amount(self):
        for line in self:
            line.practical_amount = 0
            if line.state not in ['validate', 'done']:
                continue
                
            if line.calc_actual == 'account' and line.analytic_account_id and line.account_id:
                self.env.cr.execute("""
                    SELECT SUM(line.balance) AS balance
                    FROM account_move_line line
                    JOIN res_company comp ON comp.id = line.company_id
                    left join account_move move ON move.id = line.move_id
                    WHERE move.state = 'posted'
                    AND line.account_id = %s 
                    AND line.analytic_account_id = %s 
                    AND line.date >= %s 
                    AND line.date <= %s
                """, (line.account_id.id,line.analytic_account_id.id, line.project_cost_id.date_from, line.project_cost_id.date_to))
                result = self.env.cr.dictfetchall()
                line.practical_amount = result[0]['balance'] or 0
            if line.calc_actual == 'delivery' and line.stock_move_ids:
                layers = line.stock_move_ids.mapped('stock_valuation_layer_ids')
                line.practical_amount = abs(sum(l.value for l in layers))
    
    @api.depends('practical_amount','planned_amount', 'name', 'stock_move_ids',
                 'account_id.move_line_ids', 'account_id.move_line_ids.parent_state', 'project_cost_id.state', 'operation_amount', 
                 'budget_operation_line_ids.state')
    def _compute_remaining_amount(self):
        for line in self:
            line.remaining_amount = line.planned_amount + line.operation_amount - line.practical_amount
            
    
    @api.depends('budget_operation_line_ids', 'project_cost_id.state',
                 'budget_operation_line_ids.state', 
                 'project_cost_id.budget_operation_ids.state')
    def _compute_operation_amount(self):
        for line in self:
            operation_amount = 0
            line.operation_amount = 0
            if line.state not in ['validate', 'done']:
                continue
            for op_line in line.budget_operation_line_ids.filtered(lambda r: r.state == 'done'):
                operation_amount += op_line.amount_to - op_line.amount_from
            line.operation_amount = operation_amount
        
        
    def _is_above_budget(self):
        for line in self:
            line.is_above_budget = line.practical_amount > line.planned_amount
            
            
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.name = self.product_id and self.product_id.name or ''
        if self.product_id:
            self.account_id = self.product_id._get_product_accounts()['expense']
            self.calc_actual = self.product_id.detailed_type == 'service' and 'account' or 'delivery'
            
    @api.onchange('price_unit','product_qty')
    def onchange_price_unit(self):
        for rec in self:
            rec.planned_amount = rec.product_qty * rec.price_unit
    

    @api.constrains('remaining_amount')
    def check_remaining_amount(self):
        for line in self.filtered(lambda r: r.project_cost_id.allow_over_flow != True and r.state == 'validate'):
            if line.remaining_amount < 0:
                raise ValidationError(
                    _("Budget item %s for the project %s can't be out of planned.")%(line.name,line.project_cost_id.project_id.name))