
import time
from odoo import models, fields, api, _
from dateutil import relativedelta
from datetime import date,datetime
from odoo.exceptions import UserError


class HrEmployeeEos(models.Model):
    _name = 'hr.eos.pay'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "End of Service Indemnity (EOS)"

    

    ref = fields.Char('Description', size=128, required=True, readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    date = fields.Date('Date', index=True, required=True, readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=lambda self: datetime.today().date())
    employee_id = fields.Many2one('hr.employee', "Employee", required=True, readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    amount = fields.Float()
    state = fields.Selection([('draft','Draft'),('confirm','Confirmed'),('cancelled','cancelled')],default='draft')

    def confirm(self):
        for rec in self:
            rec.write({'state':'confirm'})
    def cancelled(self):
        for rec in self:
            rec.write({'state':'cancelled'})

