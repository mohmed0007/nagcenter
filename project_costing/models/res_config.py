# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    project_warehouse_id = fields.Many2one('stock.warehouse', string='Projects Warehouse',
                                           related='company_id.project_warehouse_id', readonly=False, store=True)
    create_location = fields.Boolean('Create location from Project', related='company_id.create_location', 
                                     readonly=False, store=True)