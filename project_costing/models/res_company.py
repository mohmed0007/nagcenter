# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    project_warehouse_id = fields.Many2one('stock.warehouse', string='Projects Warehouse')
    create_location = fields.Boolean('Create location from Project', default=False)