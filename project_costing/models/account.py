# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAccount(models.Model):
    _inherit = 'account.account'
    
    move_line_ids = fields.One2many('account.move.line', 'account_id', string="Move Lines")