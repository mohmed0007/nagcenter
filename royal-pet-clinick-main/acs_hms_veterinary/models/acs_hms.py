#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import date, datetime, timedelta as td

class ACSPatient(models.Model):
    _inherit = 'hms.patient'
    _description = "Pet"

    name = fields.Char(string="Pet Name", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner",string="Owner Name")
    pet_type_id = fields.Many2one("acs.pet.type", string="Pet Type")
    pet_breed_id = fields.Many2one("acs.pet.breed", string="Pet Breed")
    pet_color_id = fields.Many2one("acs.pet.color", string="Pet Color")

    #ACS: keep it here as multiple pet can cause issue if field is in core partner object only.
    api.depends('birthday', 'date_of_death')
    def _get_age(self):
        for rec in self:
            age = ''
            if rec.birthday:
                end_data = rec.date_of_death or fields.Datetime.now()
                delta = relativedelta(end_data, rec.birthday)
                if delta.years <= 2:
                    age = str(delta.years) + _(" Year") + str(delta.months) + _(" Month ") + str(delta.days) + _(" Days")
                else:
                    age = str(delta.years) + _(" Year")
            rec.age = age

    code = fields.Char(string='Identification Code', default='/',
        help='Identifier provided by the Health Center.', copy=False, tracking=True)
    gender = fields.Selection([
        ('male', 'Male'), 
        ('female', 'Female'), 
        ('other', 'Other')], string='Gender', default='male', tracking=True)
    birthday = fields.Date(string='Date of Birth', tracking=True)
    date_of_death = fields.Date(string='Date of Death')
    age = fields.Char(string='Age', compute='_get_age')
    blood_group = fields.Selection([
        ('A+', 'A+'),('A-', 'A-'),
        ('B+', 'B+'),('B-', 'B-'),
        ('AB+', 'AB+'),('AB-', 'AB-'),
        ('O+', 'O+'),('O-', 'O-')], string='Blood Group')
    # Update all images.
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    # resized fields stored (as attachment) for performance
    image_1024 = fields.Image("Image 1024", related="image_1920", max_width=1024, max_height=1024, store=True)
    image_512 = fields.Image("Image 512", related="image_1920", max_width=512, max_height=512, store=True)
    image_256 = fields.Image("Image 256", related="image_1920", max_width=256, max_height=256, store=True)
    image_128 = fields.Image("Image 128", related="image_1920", max_width=128, max_height=128, store=True)

    def action_treatment(self):
        action = super(ACSPatient, self).action_treatment()
        action['context']['default_partner_id'] = self.partner_id.id
        return action

    def action_appointment(self):
        action = super(ACSPatient, self).action_appointment()
        action['context']['default_partner_id'] = self.partner_id.id
        return action

    def action_view_patient_procedures(self):
        action = super(ACSPatient, self).action_view_patient_procedures()
        action['context']['default_partner_id'] = self.partner_id.id
        return action

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name or '-'
            if rec.partner_id:
                name += ' [' + rec.partner_id.name + ']'
            result.append((rec.id, name))
        return result


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _rec_vat_count(self):
        for rec in self:
            rec.partner_procedure_count = len(rec.partner_procedure_ids)

    pet_ids = fields.One2many("hms.patient", "partner_id", "Pets")

    partner_procedure_ids = fields.One2many('acs.patient.procedure', 'partner_id', 'Pet Procedures')
    partner_procedure_count = fields.Integer(compute='_rec_vat_count', string='# Pet Procedures')

    def action_partner_procedures(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_procedure")
        action['domain'] = [('id', 'in', self.partner_procedure_ids.ids)]
        action['context'] = {'default_patient_id': self.id}
        return action


class ACSAppointment(models.Model):
    _inherit = 'hms.appointment'

    READONLY_STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}
    READONLY_STATES_all = {'cancel': [('readonly', True)], 'done': [('readonly', True)],'waiting': [('readonly', True)],'in_consultation': [('readonly', True)]}
    partner_id = fields.Many2one("res.partner", required=True, string="Owner Name", states=READONLY_STATES_all)

    def action_view_patient_procedures(self):
        action = super(ACSAppointment, self).action_view_patient_procedures()
        action['context']['default_partner_id'] = self.partner_id.id
        return action

    def action_view_vaccinations(self):
        action = super(ACSAppointment, self).action_view_vaccinations()
        action['context']['default_partner_id'] = self.partner_id.id
        return action

    def create_invoice_line(self, procedure, invoice):
        inv_line_obj = self.env['account.move.line']
        product_id = procedure.product_id
        account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (product_id.name,))

        inv_line_obj.with_context(check_move_validity=False).create({
            'move_id': invoice.id,
            'name': product_id.name,
            'account_id': account_id.id,
            'price_unit': procedure.price_unit,
            'quantity': 1,
            'discount': 0.0,
            'product_uom_id': product_id.uom_id.id,
            'product_id': product_id.id,
            'tax_ids': [(6, 0, product_id.taxes_id and product_id.taxes_id.ids or [])],
        })
        procedure.write({'invoice_id': invoice.id})

    def action_create_veterinary_invoice(self):
        Moveline = self.env['account.move.line']
        Procedure = self.env['acs.patient.procedure']
        res = super(ACSAppointment, self).create_invoice()

        procedure_ids = Procedure.search([('appointment_ids', 'in', self.id), ('invoice_id','=', False)])
        invoice = self.invoice_id
        if invoice and procedure_ids:
            product_data = []
            for procedure in procedure_ids:
                invoice_lines = self.create_invoice_line(procedure, invoice)
        return res


class HmsTreatment(models.Model):
    _inherit = 'hms.treatment'

    READONLY_STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}

    partner_id = fields.Many2one("res.partner", required=True, string="Owner Name", states=READONLY_STATES)

    def action_appointment(self):
        action = super(HmsTreatment, self).action_appointment()
        action['context']['default_partner_id'] = self.partner_id.id
        return action

    def action_view_patient_procedures(self):
        action = super(HmsTreatment, self).action_view_patient_procedures()
        action['context']['default_partner_id'] = self.partner_id.id
        return action


class AcsVaccination(models.Model):
    _inherit = 'acs.vaccination'

    STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}
    partner_id = fields.Many2one("res.partner", required=True, string="Owner Name", states=STATES)


class AcsCreateVaccinations(models.TransientModel):
    _inherit = "acs.plan.vaccinations"

    #Updated code for partner_id.
    def create_vaccinations(self):
        Vaccination = self.env['acs.vaccination']
        base_date = fields.Date.from_string(fields.Date.today())
        if self.vaccination_on_birthday:
            if not self.patient_id.birthday:
                raise UserError(_('Please set Date Of Birth first.'))
            base_date = fields.Date.from_string(self.patient_id.birthday)

        for line in self.vaccination_group_id.group_line:
            days = line.date_due_day
            Vaccination.create({
                'product_id': line.product_id.id,
                'patient_id': self.patient_id.id, 
                'partner_id': self.patient_id.partner_id.id, 
                'due_date': (base_date+ td(days=days)),
                'state': 'scheduled',
            })
        return {'type': 'ir.actions.act_window_close'}


class HrDepartment(models.Model):
    _inherit = "hr.department"

    department_type = fields.Selection(selection_add=[('veterinary','Veterinary')])
    

class ACSProduct(models.Model):
    _inherit = 'product.template'

    hospital_product_type = fields.Selection(selection_add=[('veterinary_procedure','Veterinary Process')])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: