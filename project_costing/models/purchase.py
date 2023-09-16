# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'purchase.order'
    
    project_id = fields.Many2one('project.project', string='Project', copy=True)
    project_cost_id = fields.Many2one('project.budget', string='Project Budget', copy=True)
    from_project = fields.Boolean(string='Created From Project', default=False, copy=True)
    subcontractor = fields.Boolean(string='Subcontractor', default=False, copy=True)
