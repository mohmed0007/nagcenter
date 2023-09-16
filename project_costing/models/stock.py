# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    project_id = fields.Many2one('project.project', string='Project', copy=True)
    from_project = fields.Boolean(string='Created From Project', default=False, copy=True)
    project_cost_id = fields.Many2one('project.budget', string='Project Budget', copy=True)
    
class StockMove(models.Model):
    _inherit = 'stock.move'
    
    from_project = fields.Boolean(string='Created From Project', related='picking_id.from_project', store=True)
    project_budget_line = fields.Many2one('project.budget.lines', string='Budget Item')
    project_cost_id = fields.Many2one('project.budget', related="project_budget_line.project_cost_id")
    

class StockLocation(models.Model):
    _inherit = 'stock.location'
    project_id = fields.Many2one('project.project', string='Project', copy=True)