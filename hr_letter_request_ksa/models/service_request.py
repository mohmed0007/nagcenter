# -*- coding: utf-8 -*-
try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html_translate
from odoo.http import request


class LetterRequest(models.Model):
    _name = "letter.request"
    _inherit = 'mail.thread'
    _description = "Letter Request"

    STATE = [
        ('draft', 'Draft'),
        ('waiting_approval', 'Submitted'),
        ('waiting_approval_2', 'Waiting Finance Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ]

    SERVICE_TYPE = [
        ('salary_introduction', 'Salary Introduction Letter'),
        ('salary_transfer', 'Salary Transfer Letter'),
        ('letter_of_authority', 'Letter of Authority'),
        ('experience_certificate', 'Experience Certificate'),
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
    last_working_date = fields.Date(string="Last Working Date", default=fields.Date.today(), tracking=True)
    service_type = fields.Selection(SERVICE_TYPE, default='salary_introduction', string='Service Type', tracking=True)
    service_to = fields.Char(string="Service To")
    salary_intro_report_template = fields.Many2one('mail.template',
                                                   related="company_id.salary_intro_report_template",
                                                   string='Salary Introduction Report')
    salary_intro_report_body = fields.Html('Body Template', sanitize_attributes=False,
                                           translate=html_translate, compute="get_salary_intro_report_template",
                                           store=True)
    salary_transfer_report_template = fields.Many2one('mail.template',
                                                      related="company_id.salary_transfer_report_template",
                                                      string='Salary Transfer Report')
    salary_transfer_report_body = fields.Html('Body Template', sanitize_attributes=False,
                                              translate=html_translate, compute="get_salary_transfer_report_template",
                                              store=True)
    letter_of_authority_report_template = fields.Many2one('mail.template',
                                                          related="company_id.letter_of_authority_report_template",
                                                          string='Letter of Authority Report')
    letter_of_authority_report_body = fields.Html('Body Template', sanitize_attributes=False,
                                                  translate=html_translate,
                                                  compute="get_letter_of_authority_report_template",
                                                  store=True)
    experience_certificate_report_template = fields.Many2one('mail.template',
                                                             related="company_id.experience_certificate_report_template",
                                                             string='Experience Certificate Report')
    experience_certificate_report_body = fields.Html('Body Template', sanitize_attributes=False,
                                                     translate=html_translate,
                                                     compute="get_experience_certificate_report_template",
                                                     store=True)
    reason = fields.Text(string="Reason")
    qr_code = fields.Binary('QRcode', compute="_generate_qr")
    user_lang = fields.Char(string="User Lang", compute="get_user_lang")

    def _generate_qr(self):
        # A method to generate QR code
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            if qrcode and base64:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=3,
                    border=4,
                )
                qr.add_data(base_url + "/letters/get_letter/" + str(rec.id))

                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'qr_code': qr_image})

    def get_user_lang(self):
        self.user_lang = ""
        if self.env.user.lang == "en_US":
            self.user_lang = "en_US"
        self.get_salary_intro_report_template()
        self.get_salary_transfer_report_template()
        self.get_letter_of_authority_report_template()
        self.get_experience_certificate_report_template()

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('letter.request.sequence') or 'New'
        return super(LetterRequest, self).create(vals)

    def action_submit(self):
        self.state = 'waiting_approval'

    def action_double_approve(self):
        self.state = 'waiting_approval_2'

    def action_approve(self):
        self.state = 'approve'

    def action_refuse(self):
        self.state = 'refuse'

    def action_cancel(self):
        self.state = 'cancel'

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete a letter which is not in draft or cancelled state'))
        return super(LetterRequest, self).unlink()

    @api.depends('salary_intro_report_template', 'salary_intro_report_template.body_html', 'service_type', 'service_to',
                 'last_working_date', 'employee_id', 'user_lang')
    def get_salary_intro_report_template(self):
        """
        A method to create salary introduction report template
        """
        for rec in self:
            if rec.salary_intro_report_template and rec.id:
                fields = ['body_html']
                template_values = rec.salary_intro_report_template.generate_email([rec.id], fields=fields)
                rec.salary_intro_report_body = template_values[rec.id].get('body_html')

    @api.depends('salary_transfer_report_template', 'salary_transfer_report_template.body_html', 'service_type',
                 'service_to', 'last_working_date', 'employee_id', 'user_lang')
    def get_salary_transfer_report_template(self):
        """
        A method to create salary transfer report template
        """
        for rec in self:
            if rec.salary_transfer_report_template and rec.id:
                fields = ['body_html']
                template_values = rec.salary_transfer_report_template.generate_email([rec.id], fields=fields)
                rec.salary_transfer_report_body = template_values[rec.id].get('body_html')

    @api.depends('letter_of_authority_report_template', 'letter_of_authority_report_template.body_html', 'service_type',
                 'service_to', 'last_working_date', 'employee_id', 'user_lang')
    def get_letter_of_authority_report_template(self):
        """
        A method to create letter of authority report template
        """
        for rec in self:
            if rec.letter_of_authority_report_template and rec.id:
                fields = ['body_html']
                template_values = rec.letter_of_authority_report_template.generate_email([rec.id], fields=fields)
                rec.letter_of_authority_report_body = template_values[rec.id].get('body_html')

    @api.depends('experience_certificate_report_template', 'experience_certificate_report_template.body_html',
                 'service_type', 'service_to', 'last_working_date', 'employee_id', 'user_lang')
    def get_experience_certificate_report_template(self):
        """
        A method to create experience certificate report template
        """
        for rec in self:
            if rec.experience_certificate_report_template and rec.id:
                fields = ['body_html']
                template_values = rec.experience_certificate_report_template.generate_email([rec.id], fields=fields)
                rec.experience_certificate_report_body = template_values[rec.id].get('body_html')


class ConfigSettings(models.TransientModel):
    """"""
    _inherit = 'res.config.settings'

    salary_intro_report_template = fields.Many2one('mail.template',
                                                   related="company_id.salary_intro_report_template",
                                                   string='Salary Introduction Report', readonly=False)
    salary_transfer_report_template = fields.Many2one('mail.template',
                                                      related="company_id.salary_transfer_report_template",
                                                      string='Salary Transfer Report', readonly=False)
    letter_of_authority_report_template = fields.Many2one('mail.template',
                                                          related="company_id.letter_of_authority_report_template",
                                                          string='Letter of Authority Report', readonly=False)
    experience_certificate_report_template = fields.Many2one('mail.template',
                                                             related="company_id.experience_certificate_report_template",
                                                             string='Experience Certificate Report', readonly=False)


class ResCompany(models.Model):
    """"""
    _inherit = 'res.company'

    salary_intro_report_template = fields.Many2one('mail.template', string='Salary Introduction Report',
                                                   domain=lambda self: [('model_id', '=', self.env.ref(
                                                       'hr_letter_request_ksa.model_letter_request').id)])
    salary_transfer_report_template = fields.Many2one('mail.template', string='Salary Transfer Report',
                                                      domain=lambda self: [('model_id', '=', self.env.ref(
                                                          'hr_letter_request_ksa.model_letter_request').id)])
    letter_of_authority_report_template = fields.Many2one('mail.template', string='Letter of Authority Report',
                                                          domain=lambda self: [('model_id', '=', self.env.ref(
                                                              'hr_letter_request_ksa.model_letter_request').id)])
    experience_certificate_report_template = fields.Many2one('mail.template', string='Experience Certificate Report',
                                                             domain=lambda self: [('model_id', '=', self.env.ref(
                                                                 'hr_letter_request_ksa.model_letter_request').id)])
    company_stamp = fields.Binary(string="Company Stamp")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    english_name = fields.Char(string="English Name")
