from odoo import models, fields, api, _


class AccConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    ticket_approve = fields.Boolean(default=False, string="Approval from Accounting Department",
                                  help="Flight Ticket Approval from account manager")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    @api.model
    def get_values(self):
        res = super(AccConfig, self).get_values()
        res.update(
            ticket_approve=self.env['ir.config_parameter'].sudo().get_param('account.ticket_approve')
        )
        return res

    def set_values(self):
        super(AccConfig, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('account.ticket_approve', self.ticket_approve)