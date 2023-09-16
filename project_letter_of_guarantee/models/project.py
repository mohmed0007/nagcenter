# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProjectProject(models.Model):
    _inherit = 'project.project'
    
    gurantee_ids = fields.One2many('account.guarantee', 'project_id', string="Letter Of Gurantee")
    
    
    def action_create_letter_of_gurantee(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account_letter_of_guarantee.action_account_guarantee")
        action['domain'] = [('project_id','=', self.id)]
        action['context'] = dict(self._context, default_project_id=self.id, default_account_analytic_id=self.analytic_account_id.id)
        return action