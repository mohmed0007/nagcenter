from odoo import fields, models,api,_


class ResPartnerEmp_fin(models.Model):
    _inherit = 'res.partner'
    emp_tick = fields.Boolean(string='Employee')
    
    