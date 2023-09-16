# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class HrBranch(models.Model):
    _name = 'hr.branch'
    _description = "Multiple branch."

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)


class Company(models.Model):
    _inherit = 'res.company'
    
    payroll_logo = fields.Image('Payroll Logo')
