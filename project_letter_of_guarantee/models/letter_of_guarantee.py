# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError

class AccountLetterOfGurantee(models.Model):
    _inherit = "account.guarantee"
    
    project_id = fields.Many2one('project.project', string="Project")
    
    



    

