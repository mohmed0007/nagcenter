
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EffectiveRequest(models.Model):
    _name = "effective.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Leave Effective Request'

    STATE = [
        ('draft', 'Draft'),
        ('waiting_approval', 'Submitted'),
        ('waiting_approval_2', 'Waiting Finance Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ]

    def _get_logged_employee(self):
        return self.env["hr.employee"].search([('user_id', '=', self.env.user.id)])

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    state = fields.Selection(STATE, default='draft', string='State', tracking=True)
    name = fields.Char(string="Name", readonly=True, copy=False, default='New')
    another_employee = fields.Boolean(string="Another Employee", default=False)
    employee_id = fields.Many2one("hr.employee", default=_get_logged_employee, string="Employee", tracking=True)
    department_id = fields.Many2one("hr.department", related="employee_id.department_id", string="Department")
    manager_id = fields.Many2one("hr.employee", related="employee_id.parent_id", string="Manager")
    employee_job = fields.Many2one("hr.job", related="employee_id.job_id", string="Job Position")
    request_date = fields.Date(string="Request Date", default=fields.Date.today(), tracking=True)
    leave_id = fields.Many2one("hr.leave", string="Leave", tracking=True)
    leave_date_from = fields.Date(related="leave_id.request_date_from", string="Leave Form")
    leave_date_to = fields.Date(related="leave_id.request_date_to", string="Leave To")
    effective_date = fields.Date(string="Effective Date", tracking=True)
    note = fields.Text(string="Notes")

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('effective.request.sequence') or 'New'
        return super(EffectiveRequest, self).create(vals)

    def action_submit(self):
        if not self.leave_id.have_effective:
            self.leave_id.have_effective = True
        else:
            self.leave_id = False
        self.state = 'waiting_approval'

    def action_double_approve(self):
        self.state = 'waiting_approval_2'

    def action_approve(self):
        self.employee_id.suspend_salary = False
        self.employee_id.effective_date = self.effective_date
        self.state = 'approve'

    def action_refuse(self):
        self.leave_id.have_effective = False
        self.state = 'refuse'

    def action_cancel(self):
        self.leave_id.have_effective = False
        self.state = 'cancel'

    def unlink(self):
        for effective in self:
            if effective.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete request which is not in draft or cancelled state'))
        return super(EffectiveRequest, self).unlink()


class Employee(models.AbstractModel):
    _inherit = "hr.employee"

    effective_date = fields.Date(string="Effective Date", tracking=True)
    suspend_salary = fields.Boolean(string="Suspend Salary", tracking=True)


class Leave(models.AbstractModel):
    _inherit = "hr.leave"

    need_effective = fields.Boolean(string="Need Effective", tracking=True)
    suspend_salary = fields.Boolean(string="Suspend Salary", tracking=True)
    have_effective = fields.Boolean(string="Have Salary")

    def action_approve(self):
        res = super(Leave, self).action_approve()
        self.employee_id.suspend_salary = True
        return res
