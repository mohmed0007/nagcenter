# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProjectProject(models.Model):
    _inherit = 'project.project'
    
    create_location = fields.Boolean('Create location from Project', related='company_id.create_location', 
                                    readonly=True, store=True)
    project_warehouse_id = fields.Many2one('stock.warehouse', string='Projects Warehouse',
                                           related='company_id.project_warehouse_id', readonly=True, store=True)
    location_id = fields.Many2one('stock.location', string="Project Location", compute="compute_location", 
                                  store=True, readonly=False)
    view_location_id = fields.Many2one('stock.location', string="View Project Location", related="project_warehouse_id.view_location_id")
    location_ids = fields.One2many('stock.location', 'project_id', 'locations')
    
    def action_create_location(self):
        if not self.project_warehouse_id:
            raise ValidationError(
                    _("Please configure Projects warehouse from the settings."))
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_location_form")
        action['domain'] = [('project_id','=', self.id)]
        action['context'] = dict(self._context, default_project_id=self.id, 
                                 default_location_id=self.project_warehouse_id.view_location_id.id)
        return action
    
    @api.depends('location_ids')
    def compute_location(self):
        for rec in self:
            if not rec.location_id:
                rec.location_id = rec.location_ids and rec.location_ids[0] or False
        