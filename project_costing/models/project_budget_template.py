
# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectCostLines(models.Model):
    _name = 'project.budget.template'
    
    active = fields.Boolean(
        default=True,
        help="If unchecked, it will allow you to hide the Budget template without removing it.")
    company_id = fields.Many2one('res.company', string='company')

    name = fields.Char(string="Budget Template", required=True)
    
    budget_template_line_ids = fields.One2many(
        comodel_name='project.budget.template.line', inverse_name='project_budget_template_id',
        string="Lines",
        copy=True)
    

class ProjectCostLines(models.Model):
    _name = 'project.budget.template.line'
    
    project_budget_template_id = fields.Many2one('project.budget.template')
    sequence = fields.Integer(
        string="Sequence",
        help="Gives the sequence order when displaying a list of sale quote lines.",
        default=10)

    company_id = fields.Many2one(
        related='project_budget_template_id.company_id', store=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        check_company=True,
        domain="[('sale_ok', '=', True), ('company_id', 'in', [company_id, False])]")
    
    product_uom_qty = fields.Float(
        string='Quantity',
        required=True,
        digits='Product Unit of Measure',
        default=1)
    
    account_id = fields.Many2one('account.account', string='Account',
                                 domain="[('deprecated', '=', False), ('company_id', '=', company_id), ('is_off_balance', '=', False)]")
    planned_amount = fields.Float('Planned Amount', required=True,help="Amount you plan to spend.",
                                     default=0)
    price_unit = fields.Float(string='Unit Price', digits='Product Price', default=1)
    
    def _prepare_budget_line_values(self):
        """ Give the values to create the corresponding order line.

        :return: `sale.order.line` create values
        :rtype: dict
        """
        self.ensure_one()
        return {
            # 'display_type': self.display_type,
            # 'name': self.name,
            'product_id': self.product_id.id,
            'product_qty': self.product_uom_qty,
            'price_unit': self.price_unit,
            'planned_amount': self.planned_amount,
            # 'product_uom': self.product_uom_id.id,
        }
        
    @api.onchange('price_unit','product_uom_qty')
    def onchange_price_unit(self):
        for rec in self:
            rec.planned_amount = rec.product_uom_qty * rec.price_unit