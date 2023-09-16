
from odoo import models, fields


class HrAllocationAccountingConfiguration(models.Model):
    _name = 'hr.allocation.accounting.configuration'

    name = fields.Char(string='name')
    leave_allocation_acc_id = fields.Many2one('account.account', string="Leave Allocation Account" ,required=True)
    ticket_allocation_acc_id = fields.Many2one('account.account', string="Ticket Allocation Account" ,required=True)
    end_service_allocation_acc_id = fields.Many2one('account.account', string='End of Allocation Service Account',required=True)
    gosi_allocation_acc_id = fields.Many2one('account.account', string='gosi  Allocation Account', required=True)

    leave_expenses_acc_id = fields.Many2one('account.account', string='Leave expenses Account',required=True)
    ticket_expenses_acc_id = fields.Many2one('account.account', string='Ticket expenses Account',required=True)
    end_service_expenses_acc_id = fields.Many2one('account.account', string='End of Service expenses ',required=True)
    gosi_expenses_acc_id = fields.Many2one('account.account', string='gosi expenses', required=True)
    loan_Payment_account = fields.Many2one('account.account', string='Loan Account', required=True)
    company_id = fields.Many2one('res.company', string = 'Company' , default=lambda self: self.env.user.company_id ,required=True)
    journal_id = fields.Many2one('account.journal', string="Journal", required=True)




#
#
# class ClearanceLeaveSettings(models.TransientModel):
#     _inherit = 'res.config.settings'
#
#     leave_allocation_acc1 = fields.Many2one('account.account',string="Leave Account",
#                                     config_parameter='hr_vacation_ticket.leave_allocation_acc1')
#     ticket_allocation_acc1 = fields.Many2one('account.account',string="Ticket Account",
#                                   config_parameter='hr_vacation_ticket.ticket_allocation_acc1' )
#
#     end_service_allocation_acc1 = fields.Many2one('account.account', string='End of Service Account',
#                                                  config_parameter='hr_vacation_ticket.end_service_allocation_acc1')
#
#     leave_expenses_acc1 = fields.Many2one('account.account', string='Leave expenses Account',
#                                          config_parameter='hr_vacation_ticket.leave_expenses_acc1')
#
#     ticket_expenses_acc1 = fields.Many2one('account.account', string='Ticket expenses Account',
#                                           config_parameter='hr_vacation_ticket.ticket_expenses_acc1')
#
#     end_service_expenses_acc1 = fields.Many2one('account.account', string='End of Service expenses Account',
#                                                config_parameter='hr_vacation_ticket.end_service_expenses_acc1')
#
#     gosi_allocation_acc1 = fields.Many2one('account.account', string='gosi expenses Account',
#                                           config_parameter='hr_vacation_ticket.gosi_allocation_acc1')
#
#     gosi_expenses_acc1 = fields.Many2one('account.account', string='gosi expenses Account',
#                                         config_parameter='hr_vacation_ticket.gosi_expenses_acc1')
#
#     journal_id = fields.Many2one('account.journal', string="Journal",
#                                       config_parameter='hr_vacation_ticket.journal_id')
#
#     leave_allocation_acc = fields.Many2one('account.account', string='Leave Account',
#                                            config_parameter='hr_vacation_ticket.leave_allocation_acc' )
#
#     ticket_allocation_acc = fields.Many2one('account.account', string='Ticket Account',
#                                             config_parameter='hr_vacation_ticket.ticket_allocation_acc')
#
#     end_service_allocation_acc = fields.Many2one('account.account', string='End of Service Account',
#                                                  config_parameter='hr_vacation_ticket.end_service_allocation_acc')
#
#     leave_expenses_acc = fields.Many2one('account.account', string='Leave expenses Account',
#                                          config_parameter='hr_vacation_ticket.leave_expenses_acc')
#
#     ticket_expenses_acc = fields.Many2one('account.account', string='Ticket expenses Account',
#                                           config_parameter='hr_vacation_ticket.ticket_expenses_acc')
#
#     end_service_expenses_acc = fields.Many2one('account.account', string='End of Service expenses Account',
#                                                config_parameter='hr_vacation_ticket.end_service_expenses_acc')
#
#     gosi_allocation_acc = fields.Many2one('account.account', string='gosi expenses Account',
#                                                config_parameter='hr_vacation_ticket.gosi_allocation_acc')
#
#     gosi_expenses_acc = fields.Many2one('account.account', string='gosi expenses Account',
#                                           config_parameter='hr_vacation_ticket.gosi_expenses_acc')
#
#     journal_allocation_id = fields.Many2one('account.journal', string="Journal",
#                                  config_parameter='hr_vacation_ticket.journal_allocation_id')
#
#     posted_entry = fields.Boolean(string='Posted Entry', config_parameter='hr_vacation_ticket.posted_entry')
#
#     loan_acc = fields.Many2one('account.account', string='Loan Account',
#                                config_parameter='hr_vacation_ticket.loan_acc')
#
#
#
#     # @api.model
#     # def get_values(self):
#     #     res = super(ClearanceLeaveSettings, self).get_values()
#     #     res.update(
#     #         loan_approve=self.env['ir.config_parameter'].sudo().get_param('account.loan_approve')
#     #     )
#     #     return res
#     #
#     # def set_values(self):
#     #     super(ClearanceLeaveSettings, self).set_values()
#     #     self.env['ir.config_parameter'].sudo().set_param('account.loan_approve', self.loan_approve)
#
#
#
#
#
#     def set_values(self):
#         res = super(ClearanceLeaveSettings, self).set_values()
#         self.env['ir.config_parameter'].sudo().set_param('leave_allocation_acc1', self.leave_allocation_acc1.id)
#         self.env['ir.config_parameter'].sudo().set_param('ticket_allocation_acc1', self.ticket_allocation_acc1.id)
#         self.env['ir.config_parameter'].sudo().set_param('end_service_allocation_acc1', self.end_service_allocation_acc1.id)
#         self.env['ir.config_parameter'].sudo().set_param('gosi_allocation_acc1', self.gosi_allocation_acc1.id)
#
#         self.env['ir.config_parameter'].sudo().set_param('leave_expenses_acc1', self.leave_expenses_acc1.id)
#         self.env['ir.config_parameter'].sudo().set_param('ticket_expenses_acc1', self.ticket_expenses_acc1.id)
#         self.env['ir.config_parameter'].sudo().set_param('end_service_expenses_acc1', self.end_service_expenses_acc1.id)
#         self.env['ir.config_parameter'].sudo().set_param('gosi_expenses_acc1', self.gosi_expenses_acc1.id)
#
#         # self.env['ir.config_parameter'].sudo().set_param('payment_account', self.payment_account.id)
#         self.env['ir.config_parameter'].sudo().set_param('journal_id', self.journal_id.id)
#         self.env['ir.config_parameter'].sudo().set_param('leave_allocation_acc', self.leave_allocation_acc.id)
#         self.env['ir.config_parameter'].sudo().set_param('leave_expenses_acc', self.leave_expenses_acc.id)
#         self.env['ir.config_parameter'].sudo().set_param('end_service_expenses_acc', self.end_service_expenses_acc.id)
#         self.env['ir.config_parameter'].sudo().set_param('end_service_allocation_acc', self.end_service_allocation_acc.id)
#         self.env['ir.config_parameter'].sudo().set_param('ticket_expenses_acc', self.ticket_expenses_acc.id)
#         self.env['ir.config_parameter'].sudo().set_param('ticket_allocation_acc', self.ticket_allocation_acc.id)
#         self.env['ir.config_parameter'].sudo().set_param('journal_allocation_id', self.journal_allocation_id.id)
#         self.env['ir.config_parameter'].sudo().set_param('gosi_allocation_acc', self.gosi_allocation_acc.id)
#         self.env['ir.config_parameter'].sudo().set_param('gosi_expenses_acc', self.gosi_expenses_acc.id)
#         self.env['ir.config_parameter'].sudo().set_param('loan_acc', self.loan_acc.id)
#         self.env['ir.config_parameter'].sudo().set_param('posted_entry', self.posted_entry)
#
#         return res

