# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class AppointmentPurpose(models.Model):
    _name = 'appointment.purpose'
    _description = "Appointment Purpose"

    name = fields.Char(string='Appointment Purpose', required=True, translate=True)

class AppointmentType(models.Model):
    _name = 'appointment.type'
    _description = "Appointment Type"

    name = fields.Char(string='Appointment Purpose', required=True, translate=True)



class AppointmentCabin(models.Model):
    _name = 'appointment.cabin'
    _description = "Appointment Cabin"

    name = fields.Char(string='Appointment Cabin', required=True, translate=True)


class Appointment(models.Model):
    _name = 'hms.appointment'
    _description = "Appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'acs.hms.mixin', 'acs.documnt.mixin']
    _order = "id desc"

    @api.model
    def _get_service_id(self):
        consultation = False
        if self.env.user.company_id.consultation_product_id:
            consultation = self.env.user.company_id.consultation_product_id.id
        return consultation

    @api.depends('medical_alert_ids')
    def _get_alert_count(self):
        for rec in self:
            rec.alert_count = len(rec.medical_alert_ids)

    @api.depends('patient_id', 'patient_id.birthday', 'date')
    def get_patient_age(self):
        for rec in self:
            age = ''
            if rec.patient_id.birthday:
                end_data = rec.date or fields.Datetime.now()
                delta = relativedelta(end_data, rec.patient_id.birthday)
                if delta.years <= 2:
                    age = str(delta.years) + _(" Year") + str(delta.months) + _(" Month ") + str(delta.days) + _(" Days")
                else:
                    age = str(delta.years) + _(" Year")
            rec.age = age

    def _get_evaluation(self):
        for rec in self:
            rec.evaluation_id = rec.evaluation_ids[0].id if rec.evaluation_ids else False

    def _acs_get_invoice_count(self):
        AccountMove = self.env['account.move']
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    READONLY_STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}
    READONLY_STATES_all = {'cancel': [('readonly', True)], 'done': [('readonly', True)],'waiting': [('readonly', True)],'in_consultation': [('readonly', True)],'vitality': [('readonly', True)]}
    name = fields.Char(string='Appointment Id', readonly=True, copy=False, tracking=True, states=READONLY_STATES)
    patient_id = fields.Many2one('hms.patient', ondelete='restrict',  string='Patient',
        required=True, index=True, help='Patient Name', states=READONLY_STATES_all, tracking=True)
    image_128 = fields.Binary(related='patient_id.image_128',string='Image', readonly=True)
    physician_id = fields.Many2one('hms.physician', ondelete='restrict', string='Physician', 
        index=True, help='Physician\'s Name', states=READONLY_STATES_all, tracking=True)
    department_id = fields.Many2one('hr.department', ondelete='restrict', 
        domain=[('patient_department', '=', True)], string='Department', tracking=True, states=READONLY_STATES_all)
    no_invoice = fields.Boolean(string='Invoice Exempt', states=READONLY_STATES)
    follow_date = fields.Datetime(string="Follow Up Date", states=READONLY_STATES, copy=False)
    
    evaluation_ids = fields.One2many('acs.patient.evaluation', 'appointment_id', 'Evaluations')
    evaluation_id = fields.Many2one('acs.patient.evaluation', ondelete='restrict', compute=_get_evaluation,
        string='Evaluation', states=READONLY_STATES)

    weight = fields.Float(related="evaluation_id.weight", string='Weight', help="Weight in KG", states=READONLY_STATES)
    crt = fields.Float(related="evaluation_id.crt", string='Capillary Refilling Time', help="Capillary Refilling Time", states=READONLY_STATES)
    height = fields.Float(related="evaluation_id.height", string='Height', help="Height in cm", states=READONLY_STATES)
    temp = fields.Float(related="evaluation_id.temp", string='Temp', states=READONLY_STATES)
    hr = fields.Integer(related="evaluation_id.hr", string='HR', help="Heart Rate", states=READONLY_STATES)
    rr = fields.Integer(related="evaluation_id.rr", string='RR', states=READONLY_STATES, help='Respiratory Rate')
    systolic_bp = fields.Integer(related="evaluation_id.systolic_bp", string="Systolic BP", states=READONLY_STATES)
    diastolic_bp = fields.Integer(related="evaluation_id.diastolic_bp", string="Diastolic BP", states=READONLY_STATES)
    spo2 = fields.Integer(related="evaluation_id.spo2", string='SpO2', states=READONLY_STATES, 
        help='Oxygen Saturation, percentage of oxygen bound to hemoglobin')
    rbs = fields.Integer(related="evaluation_id.rbs", string='RBS', states=READONLY_STATES, 
        help="Random blood sugar measures blood glucose regardless of when you last ate.")
    bmi = fields.Float(related="evaluation_id.bmi", string='Body Mass Index')
    bmi_state = fields.Selection(related="evaluation_id.bmi_state", string='BMI State')
    acs_weight_name = fields.Char(related="evaluation_id.acs_weight_name", string='Patient Weight unit of measure label')
    acs_height_name = fields.Char(related="evaluation_id.acs_height_name", string='Patient Height unit of measure label')
    acs_temp_name = fields.Char(related="evaluation_id.acs_temp_name", string='Patient Temp unit of measure label')
    acs_spo2_name = fields.Char(related="evaluation_id.acs_spo2_name", string='Patient SpO2 unit of measure label')
    acs_rbs_name = fields.Char(related="evaluation_id.acs_rbs_name", string='Patient RBS unit of measure label')
    
    pain_level = fields.Selection(related="evaluation_id.pain_level", string="Pain Level")
    pain = fields.Selection(related="evaluation_id.pain", string="Pain")

    differencial_diagnosis = fields.Text(string='Differential Diagnosis', states=READONLY_STATES, help="The process of weighing the probability of one disease versus that of other diseases possibly accounting for a patient's illness.")
    medical_advice = fields.Text(string='Medical Advice', states=READONLY_STATES, help="The provision of a formal professional opinion regarding what a specific individual should or should not do to restore or preserve health.")
    chief_complain = fields.Text(string='Chief Complaints', states=READONLY_STATES, help="The concise statement describing the symptom, problem, condition, diagnosis, physician-recommended return, or other reason for a medical encounter.")
    present_illness = fields.Text(string='History of Present Illness', states=READONLY_STATES)
    lab_report = fields.Text(string='Lab Report', states=READONLY_STATES, help="Details of the lab report.")
    
    physice = fields.Text(string='physice', help="Details of the physice")
    diagnestic_antcome = fields.Text(string='Diagnestic Antcome', help="Details of the Diagnestic Antcome")
    ddx = fields.Text(string='dxx', help="Details of the ddx")
    vitzlity= fields.Text(string='vitzlity', help="Details of the vitzlity")
    lab = fields.Text(string='Lab', help="Details of the Lab")
    imaging = fields.Text(string='imaging', help="Details of the imaging")
    swpect = fields.Text(string='swpect', help="Details of the swpect")
    radiological_report = fields.Text(string='Radiological Report', states=READONLY_STATES, help="Details of the Radiological Report")
    notes = fields.Text(string='Notes', states=READONLY_STATES)
    past_history = fields.Text(string='Past History', states=READONLY_STATES, help="Past history of any diseases.")
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)
    payment_state = fields.Selection(related="invoice_id.payment_state", store=True, string="Payment Status")
    urgency = fields.Selection([
            ('normal', 'Normal'),
            ('urgent', 'Urgent'),
            ('medical_emergency', 'Medical Emergency'),
        ], string='Urgency Level', default='normal', states=READONLY_STATES_all)
    state = fields.Selection([
            ('draft', 'Draft'),
            # ('confirm', 'Confirm'),
            ('waiting', 'Waiting'),
            ('vitality', 'Vitality'),
            ('in_consultation', 'In consultation'),
            ('pause', 'Pause'),
            ('to_invoice', 'To Invoice'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], string='State',default='draft', required=True, copy=False, tracking=True,
        states=READONLY_STATES)
    product_id = fields.Many2one('product.product', ondelete='restrict', 
        string='Consultation Service', help="Consultation Services", 
        domain=[('hospital_product_type', '=', "consultation")], required=True, 
        default=_get_service_id, states=READONLY_STATES)
    age = fields.Char(compute="get_patient_age", string='Age', store=True,
        help="Computed patient age at the moment of the evaluation")
    company_id = fields.Many2one('res.company', ondelete='restrict', states=READONLY_STATES,
        string='Hospital', default=lambda self: self.env.company)
    appointment_invoice_policy = fields.Selection(related="company_id.appointment_invoice_policy")
    no_invoice = fields.Boolean('Invoice Exempt', states=READONLY_STATES)
    consultation_type = fields.Selection([
        ('consultation','Consultation'),
        ('followup','Follow Up')],'Consultation Type', states=READONLY_STATES, copy=False)

    diseases_ids = fields.Many2many('hms.diseases', 'diseases_appointment_rel', 'diseas_id', 'appointment_id', 'Diseases', states=READONLY_STATES)
    medical_history = fields.Text(related='patient_id.medical_history', 
        string="Past Medical History", readonly=True)
    patient_diseases_ids = fields.One2many('hms.patient.disease', readonly=True, 
        related='patient_id.patient_diseases_ids', string='Disease History')

    date = fields.Datetime(string='Date', default=fields.Datetime.now, states=READONLY_STATES_all, tracking=True, copy=False)
    date_to = fields.Datetime(string='Date To', default=fields.datetime.now() + timedelta(minutes=15), states=READONLY_STATES, copy=False)

    #ACS: odoo15 make default duration configurable on general setting.
    planned_duration = fields.Float('Duration', default=0.25, states=READONLY_STATES)

    waiting_date_start = fields.Datetime('Waiting Start Date', states=READONLY_STATES, copy=False)
    waiting_date_end = fields.Datetime('Waiting end Date', states=READONLY_STATES, copy=False)
    waiting_duration = fields.Float('Wait Time', readonly=True, copy=False)
    waiting_duration_timer = fields.Float('Wait Timer', readonly=True, default="0.1", copy=False)

    date_start = fields.Datetime(string='Start Date', states=READONLY_STATES, copy=False)
    date_end = fields.Datetime(string='End Date', states=READONLY_STATES, copy=False)
    appointment_duration = fields.Float('Consultation Time', readonly=True, copy=False)
    appointment_duration_timer = fields.Float('Consultation Timer', readonly=True, default="0.1", copy=False)

    purpose_id = fields.Many2one('appointment.purpose', ondelete='cascade', 
        string='The Reason', help="Appointment Purpose",required=True)
    cabin_id = fields.Many2one('appointment.cabin', ondelete='cascade', 
        string='Consultation Room (Cabin)', help="Appointment Cabin", states=READONLY_STATES, copy=False)
    treatment_id = fields.Many2one('hms.treatment', ondelete='cascade', 
        string='Treatment', help="Treatment Id", states=READONLY_STATES_all, tracking=True)

    ref_physician_id = fields.Many2one('res.partner', ondelete='restrict', string='Referring Physician', 
        index=True, help='Referring Physician', states=READONLY_STATES)
    responsible_id = fields.Many2one('hms.physician', "Responsible Jr. Doctor", states=READONLY_STATES)
    medical_alert_ids = fields.Many2many('acs.medical.alert', 'appointment_medical_alert_rel','appointment_id', 'alert_id',
        string='Medical Alerts', related='patient_id.medical_alert_ids')
    alert_count = fields.Integer(compute='_get_alert_count', default=0)
    consumable_line_ids = fields.One2many('hms.consumable.line', 'appointment_id',
        string='Consumable Line', states=READONLY_STATES, copy=False)
    #Only used in case of advance invoice
    consumable_invoice_id = fields.Many2one('account.move', string="Consumables Invoice", copy=False)

    pause_date_start = fields.Datetime('Pause Start Date', states=READONLY_STATES, copy=False)
    pause_date_end = fields.Datetime('Pause end Date', states=READONLY_STATES, copy=False)
    pause_duration = fields.Float('Paused Time', readonly=True, copy=False)
    prescription_ids = fields.One2many('prescription.order', 'appointment_id', 'Prescriptions', copy=False)
    prescription_trouble_ids = fields.One2many('prescription.trouble.order', 'appointment_trouble_id', 'Prescriptions', copy=False)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', check_company=True, 
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If you change the pricelist, related invoice will be affected.")
    location = fields.Char(string="Appointment Location", states=READONLY_STATES)
    outside_appointment = fields.Boolean(string="Outside Appointment", states=READONLY_STATES)
    cancel_reason = fields.Text(string="Cancel Reason", states=READONLY_STATES, copy=False)
    user_id = fields.Many2one('res.users',string='Responsible', states=READONLY_STATES,
        ondelete='cascade', help='Responsible User for appointment validation And further Followup.')
    acs_kit_id = fields.Many2one('acs.product.kit', string='Kit', states=READONLY_STATES)
    acs_kit_qty = fields.Integer("Kit Qty", states=READONLY_STATES, default=1)
    invoice_ids = fields.One2many("account.move", "appointment_id", string="Invoices", groups="account.group_account_invoice")
    invoice_count = fields.Integer(compute="_acs_get_invoice_count", string="#Invoices", groups="account.group_account_invoice")
    app_type = fields.Many2one('appointment.type',  string='Appointment Type ', 
        index=True, help='Referring Physician')
    #ACS NOTE: Because of error for portal appointment creation added _compute_field_value method.
    department_type = fields.Selection(related='department_id.department_type', string="Appointment Department", store=True)

    #Just to make object selectable in selction field this is required: Waiting Screen
    acs_show_in_wc = fields.Boolean(default=True)

    cbc = fields.Boolean(default=False)

    chemistry_profile = fields.Boolean(default=False)

    hormons = fields.Boolean(default=False)
    
    x_ray = fields.Boolean(default=False)

    abdominal = fields.Boolean(default=False)

    eco_cardiography = fields.Boolean(default=False)

    ecg = fields.Boolean(default=False)

    blood_pressure = fields.Boolean(default=False)

    pulse_oximetry = fields.Boolean(default=False)
    
    urine_analysis = fields.Boolean(default=False)
    
    blood_smear = fields.Boolean(default=False)

    skin_scarp = fields.Boolean(default=False)
    ear_swab = fields.Boolean(default=False)
    vaginal_swab = fields.Boolean(default=False)
    
    snaptests = fields.Boolean(default=False)
    stooltests = fields.Boolean(default=False)
    digostic_endoscope = fields.Boolean(default=False)
    diagstic_comment = fields.Text(string='Diagstic Comment')

    diagnosis_differencial = fields.Text(string='Differencial Diagnosis')
    

    suspect_or_diagnosis = fields.Text(string='Suspect or Diagnosis')
    
    subjective = fields.Text(string='Subjective')

    objective = fields.Text(string='Objective') 

    assessment = fields.Text(string='Assessment')

    # mucous_membrane = fields.Selection(related="evaluation_id.mucous_membrane", string='Mucous Membrane')
    mucous_membrane = fields.Selection([
            ('color_fcff33', 'Icteric'),
            ('color_fdfdfd', 'Pale'),
            ('color_fa56e4', 'Pink'),
            ('color_6556fa', 'Cysnosid'),
            ('color_f91b05', 'Red'),
        ], string='Mucous Membrane', default='color_fcff33')
    
    hoi_month = fields.Boolean(string='Months',default=False)
    hoi_day = fields.Boolean(string='Days', default=False)
    hoi_hourse = fields.Boolean(string='hours', default=False)
    hoi_month_field = fields.Integer(help="Month Of Illness")
    hoi_day_field = fields.Integer(help="Days Of Illness")
    hoi_hourse_field = fields.Integer(help="hours Of Illness")
    # mucous_membrane = fields.Selection([
    #         ('normal', 'Normal'),
    #         ('urgent', 'Urgent'),
    #         ('medical_emergency', 'Medical Emergency'),
    #     ], string='Urgency Level', default='normal', states=READONLY_STATES_all)
    
    cbc_upload = fields.Binary("cbc file")

    cbc_upload_test = fields.Many2one('ir.attachment', string='Upload')

    mark_all_normal = fields.Boolean(string='Mark All Normal',default=False)
    
    one_q = fields.Selection([
            ('normal', 'Normal'),
            ('poor', 'Poor'),
            ('polyphagia', 'Polyphagia'),
        ], string='How is Your Pets Appetite?', default='normal')

    two_q = fields.Selection([
            ('dry', 'Dry'),
            ('home_made', 'Home Made'),
            ('wet', 'Wet'),
            ('raw', 'Raw'),
        ], string='What does your pet food?', default='dry')

    three_q = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Has then been any symptoms?', default='no')
    three_q_comment = fields.Text(string="Comment")
    four_q = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Is your pet ithing?Hair loss?', default='no')
    five_q = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Are then other animals in your house hold?', default='no')
    six_q = fields.Selection([
            ('with_in_last2months', 'With in Last 2 Months'),
            ('last6months', 'Last 6 Months'),
        ], string='If female and not spayed,when was your pet last cycle:', default='with_in_last2months')
    seven_q = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Is your pet on any medication?', default='no')
    seven_q_comment = fields.Text(string="Comment") 
    eight_q = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
             ('n/a', 'N/A'),
        ], string='Does your pet receive vaccination periodically?', default='no')
    ninth_q = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
             ('n/a', 'N/A'),
        ], string='Is your pet suffering from any allergy?', default='no')
    ninth_q_comment = fields.Text(string="Comment")
    tenth_q = fields.Selection([
            ('normal', 'Normal'),
            ('lethargic', 'Lethargic'),
             ('hyper_active', 'Hyper Active'),
        ], string='How is your pet activity?', default='normal')
    history_form_all_comment = fields.Text(string="Comment Of All")
    
    
    #-------------------------------------General appearance----------------------
    q1_op1 = fields.Boolean(string="Normal")
    q1_op2 = fields.Boolean(string="Lethargic")
    q1_op3 = fields.Boolean(string="Senior Pet")
    q1_op4 = fields.Boolean(string="BCS 215")
    q1_op5 = fields.Boolean(string="BCS 315")
    q1_op6 = fields.Boolean(string="BCS 415")
    q1_op7 = fields.Boolean(string="BCS 515")
    #-------------------------------------Mucous Membranes ------------------------
    q2_op1 = fields.Boolean(string="Normal")
    q2_op2 = fields.Boolean(string="Pale")
    q2_op3 = fields.Boolean(string="Cyanosid")
    q2_op4 = fields.Boolean(string="Petechial Hemorrhage")
    q2_op5 = fields.Boolean(string="Joundice")
    #-------------------------------------Ears -------------------------------------
    q3_op1 = fields.Boolean(string="Normal")
    q3_op2 = fields.Boolean(string="Mites")
    q3_op3 = fields.Boolean(string="Bactenial")
    q3_op4 = fields.Boolean(string="Yeast")
    q3_op5 = fields.Boolean(string="Exudate")
    q3_op6 = fields.Boolean(string="Puritic")
    q3_op7 = fields.Boolean(string="Ear Hematoma")
    #------------------------------------Eyes--------------------------------------
    q4_op1 = fields.Boolean(string="Normal")
    q4_op2 = fields.Boolean(string="Cornealalcen")
    q4_op3 = fields.Boolean(string="Corneal Edema")
    q4_op4 = fields.Boolean(string="Clucoma")
    q4_op5 = fields.Boolean(string="Cataract")
    q4_op6 = fields.Boolean(string="Rupture eye")
    q4_op7 = fields.Boolean(string="Nicitating membrare prolapsed")
    #----------------------------------Oral Cavity---------------------------------
    q5_op1 = fields.Boolean(string="Normal")
    q5_op2 = fields.Boolean(string="Ulcen")
    q5_op3 = fields.Boolean(string="Gingivites")
    q5_op4 = fields.Boolean(string="Periodenities")
    q5_op5 = fields.Boolean(string="Dental Disease")
    q5_op6 = fields.Boolean(string="EGC")
    #--------------------------------Respiratory-----------------------------------
    q6_op1 = fields.Boolean(string="Normal")
    q6_op2 = fields.Boolean(string="Cough")
    q6_op3 = fields.Boolean(string="sneezing")
    q6_op4 = fields.Boolean(string="Nasal Discharge")
    q6_op5 = fields.Boolean(string="Pyspenic")
    #-------------------------------Abdomen----------------------------------------
    q7_op1 = fields.Boolean(string="Normal")
    q7_op2 = fields.Boolean(string="Cranial Abdomeiral Pain")
    q7_op3 = fields.Boolean(string="Caudal Abdominal Pain")
    q7_op4 = fields.Boolean(string="Bloated")
    q7_op5 = fields.Boolean(string="Ascites")
    q7_op6 = fields.Boolean(string="Splenn Omegally")
    q7_op7 = fields.Boolean(string="Hepatomegally")
    #--------------------------------Lymph Node------------------------------------
    q8_op1 = fields.Boolean(string="Normal")
    q8_op2 = fields.Boolean(string="Sub Madibular")
    q8_op3 = fields.Boolean(string="Prescapular")
    q8_op4 = fields.Boolean(string="Axillary")
    q8_op5 = fields.Boolean(string="Inguinal")
    q8_op6 = fields.Boolean(string="Popliteal")
    q8_op7 = fields.Boolean(string="Enlarged")
    q8_op8 = fields.Boolean(string="Painful")
    #-------------------------------Musculoskeletal--------------------------------
    q9_op1 = fields.Boolean(string="Normal")
    q9_op2 = fields.Boolean(string="Lame Front")
    q9_op3 = fields.Boolean(string="Lame Rear")
    q9_op4 = fields.Boolean(string="Hipcrepitus")
    q9_op5 = fields.Boolean(string="Medial Pattelar Luxation")
    q9_op6 = fields.Boolean(string="Stifle Cranial Drawen")
    q9_op7 = fields.Boolean(string="Fracture")
    #------------------------------Skin--------------------------------------------
    q10_op1 = fields.Boolean(string="Normal")
    q10_op2 = fields.Boolean(string="Fleas")
    q10_op3 = fields.Boolean(string="Ticks")
    q10_op4 = fields.Boolean(string="Woods Lamp Positive")
    q10_op5 = fields.Boolean(string="Praritic")
    q10_op6 = fields.Boolean(string="Hair Loss")
    q10_op7 = fields.Boolean(string="Hypopigmentation")
    q10_op8 = fields.Boolean(string="Hyperpigmentation")
    q10_op9 = fields.Boolean(string="Hotspot")
    q10_op10 = fields.Boolean(string="Greasy Skin")
    q10_op11 = fields.Boolean(string="Yeast Odour")
    q10_op12 = fields.Boolean(string="Pyodelma")
    #-------------------------------Genitourinary---------------------------------
    q11_op1 = fields.Boolean(string="Normal")
    q11_op2 = fields.Boolean(string="Dsyuria")
    q11_op3 = fields.Boolean(string="Hematooria")
    q11_op4 = fields.Boolean(string="Vaginal Discharge")
    q11_op5 = fields.Boolean(string="Poly Dygsia")
    pe_mark_pe = fields.Boolean(string='Mark All Normal',default=False)
    q1_comment = fields.Text()
    q2_comment = fields.Text()
    q3_comment = fields.Text()
    q4_comment = fields.Text()
    q5_comment = fields.Text()
    q6_comment = fields.Text()
    q7_comment = fields.Text()
    q8_comment = fields.Text()
    q9_comment = fields.Text()
    q10_comment = fields.Text()
    q11_comment = fields.Text()
    @api.onchange('mark_all_normal')
    def onchange_history_mark(self):
        if self.mark_all_normal == True:
            self.one_q = 'normal'

    @api.onchange('pe_mark_pe')
    def onchange_pe_mark(self):
        if self.pe_mark_pe == True:
            self.q1_op1 = True
            self.q2_op1 = True
            self.q3_op1 = True
            self.q4_op1 = True
            self.q5_op1 = True
            self.q6_op1 = True
            self.q7_op1 = True
            self.q8_op1 = True
            self.q9_op1 = True
            self.q10_op1 = True
            self.q11_op1 = True



    


    @api.model
    def default_get(self, fields):
        res = super(Appointment, self).default_get(fields)
        # if self.treatment_id:
        #     self.purpose_id = self.treatment_id.reason_treatment_id.id

        if self._context.get('acs_department_type'):
            department = self.env['hr.department'].search([('department_type','=',self._context.get('acs_department_type'))], limit=1)
            if department:
                res['department_id'] = department.id
        return res

    def _compute_field_value(self, field):
        if field.name == 'department_type':
            for rec in self:
                if rec.department_id and rec.department_id.id:
                    department = self.env['hr.department'].sudo().search([('id','=',rec.department_id.id)])
                    rec.write({
                        'department_type': department.department_type
                    })
        else:
            super()._compute_field_value(field)

    @api.onchange('department_id')
    def onchange_department(self):
        res = {}
        if self.department_id:
            physicians = self.env['hms.physician'].search([('department_ids', 'in', self.department_id.id)])
            res['domain'] = {'physician_id':[('id','in',physicians.ids)]}
            self.department_type = self.department_id.department_type
        return res

    @api.onchange('date', 'planned_duration')
    def onchange_date_duration(self):
        if self.date:
            if self.planned_duration:
                self.date_to = self.date + timedelta(hours=self.planned_duration)
            else:
                self.date_to = self.date

    @api.onchange('date_to')
    def onchange_date_to(self):
        if self.date and self.date_to:
            diff = self.date_to - self.date
            planned_duration = (diff.days * 24) + (diff.seconds/3600)
            if self.planned_duration != planned_duration:
                self.planned_duration = planned_duration

    @api.model
    def create(self, values):
        if values.get('name', 'New Appointment') == 'New Appointment':
            values['name'] = self.env['ir.sequence'].next_by_code('hms.appointment') or 'New Appointment'
        return super(Appointment, self).create(values)

    def unlink(self):
        for data in self:
            if data.state in ['done']:
                raise UserError(_('You can not delete record in done state'))
        return super(Appointment, self).unlink()

    def print_report(self):
        return self.env.ref('acs_hms.action_appointment_report').report_action(self)

    def action_appointment_send(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        template_id = self.env['ir.model.data']._xmlid_to_res_id('acs_hms.acs_appointment_email', raise_if_not_found=False)

        ctx = {
            'default_model': 'hms.appointment',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def create_invoice(self):
        product_id = self.product_id
        if not product_id:
            raise UserError(_("Please Set Consultation Service first."))
        product_data = [{'product_id': product_id}]
        for consumable in self.consumable_line_ids:
            product_data.append({
                'product_id': consumable.product_id,
                'quantity': consumable.qty,
            })
        inv_data = {
            'ref_physician_id': self.ref_physician_id and self.ref_physician_id.id or False,
            'physician_id': self.physician_id and self.physician_id.id or False,
            'appointment_id': self.id,
            'hospital_invoice_type': 'appointment',
        }

        pricelist_context = {}
        if self.pricelist_id:
            pricelist_context = {'acs_pricelist_id': self.pricelist_id.id}
        invoice = self.with_context(pricelist_context).acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data=inv_data)
        self.invoice_id = invoice.id
        if self.state == 'to_invoice':
            self.appointment_done()

        # if self.state == 'waiting' and not self._context.get('avoid_confirmation'):
        #     if self.invoice_id and not self.company_id.acs_check_appo_payment:
        #         self.appointment_confirm()

    def create_consumed_prod_invoice(self):
        product_data = []
        if not self.consumable_line_ids:
            raise UserError(_("There is no consumed product to invoice."))

        for consumable in self.consumable_line_ids:
            product_data.append({
                'product_id': consumable.product_id,
                'quantity': consumable.qty,
            })
        inv_data = {
            'ref_physician_id': self.ref_physician_id and self.ref_physician_id.id or False,
            'physician_id': self.physician_id and self.physician_id.id or False,
            'appointment_id': self.id,
            'hospital_invoice_type': 'appointment',
        }

        pricelist_context = {}
        if self.pricelist_id:
            pricelist_context = {'acs_pricelist_id': self.pricelist_id.id}
        invoice = self.with_context(pricelist_context).acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data=inv_data)
        self.consumable_invoice_id = invoice.id
        if self.state == 'to_invoice':
            self.appointment_done()

    def view_invoice(self):
        appointment_invoices = self.invoice_ids
        action = self.acs_action_view_invoice(appointment_invoices)
        action['context'].update({
            'default_partner_id': self.patient_id.partner_id.id,
            'default_patient_id': self.patient_id.id,
            'default_appointment_id': self.id,
            'default_ref_physician_id': self.ref_physician_id and self.ref_physician_id.id or False,
            'default_physician_id': self.physician_id and self.physician_id.id or False,
            'default_hospital_invoice_type': 'appointment',
            'default_ref': self.name,
        })
        return action

    def action_refer_doctor(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_appointment")
        action['domain'] = [('patient_id','=',self.id)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id}
        action['views'] = [(self.env.ref('acs_hms.view_hms_appointment_form').id, 'form')]
        return action

    def action_create_evaluation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_evaluation_popup")
        action['domain'] = [('patient_id','=',self.id)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_appointment_id': self.id}
        return action

    @api.onchange('patient_id', 'date')
    def onchange_patient_id(self):
        if self.patient_id:
            self.age = self.patient_id.age
            followup_days = self.env.user.company_id.followup_days
            followup_day_limit = (datetime.now() - timedelta(days=followup_days)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            appointment_id = self.search([('patient_id', '=', self.patient_id.id),('date','>=',followup_day_limit)])
            
            #Avoid setting physician if already there from treatment or manually selected.
            if not self.physician_id:
                self.physician_id = self.patient_id.primary_doctor and self.patient_id.primary_doctor.id
            if appointment_id:
                self.consultation_type = 'followup'
                if self.env.user.company_id.followup_product_id:
                    self.product_id = self.env.user.company_id.followup_product_id.id
            else:
                self.consultation_type = 'consultation'

    @api.onchange('physician_id', 'department_id', 'consultation_type')
    def onchange_physician(self):
        product_id = False
        #ACS: First check configuration on department.
        if self.department_id:
            if self.consultation_type=='followup':
                if self.department_id.followup_service_id:
                    product_id = self.department_id.followup_service_id.id

            elif self.department_id.consultaion_service_id:
                product_id = self.department_id.consultaion_service_id.id

        if self.physician_id:
            if self.consultation_type=='followup':
                if self.physician_id.followup_service_id:
                    product_id = self.physician_id.followup_service_id.id

            elif self.physician_id.consultaion_service_id:
                product_id = self.physician_id.consultaion_service_id.id

            if self.physician_id.appointment_duration:
                self.planned_duration = self.physician_id.appointment_duration

            
        if product_id:
            self.product_id = product_id

    def appointment_confirm(self):
        if self.company_id.appointment_invoice_policy=='advance' and not self.invoice_id:
            raise UserError(_('Invoice is not created yet'))

        elif self.invoice_id and self.company_id.acs_check_appo_payment and self.payment_state not in ['in_payment','paid']:
            raise UserError(_('Invoice is not Paid yet.'))

        if not self.user_id:
            self.user_id = self.env.user.id
        # self.state = 'confirm'

    def appointment_waiting(self):
        self.state = 'waiting'
        self.waiting_date_start = datetime.now()
        self.waiting_duration = 0.1

    def appointment_vitality(self):
        self.state = 'vitality'
        

    def appointment_consultation(self):
        if not self.waiting_date_start:
            raise UserError(('No waiting start time defined.'))
        datetime_diff = datetime.now() - self.waiting_date_start
        m, s = divmod(datetime_diff.total_seconds(), 60)
        h, m = divmod(m, 60)
        self.waiting_duration = float(('%0*d')%(2,h) + '.' + ('%0*d')%(2,m*1.677966102))
        self.state = 'in_consultation'
        self.waiting_date_end = datetime.now()
        self.date_start = datetime.now()

    def action_pause(self):
        self.state = 'pause'
        self.pause_date_start = datetime.now()

        if self.date_start:
            datetime_diff = datetime.now() - self.date_start
            m, s = divmod(datetime_diff.total_seconds(), 60)
            h, m = divmod(m, 60)
            self.appointment_duration = float(('%0*d')%(2,h) + '.' + ('%0*d')%(2,m*1.677966102)) - self.pause_duration
        self.date_end = datetime.now()

    def action_start_paused(self):
        self.state = 'in_consultation'
        self.pause_date_end = datetime.now()
        self.date_end = False
        datetime_diff = datetime.now() - self.pause_date_start
        m, s = divmod(datetime_diff.total_seconds(), 60)
        h, m = divmod(m, 60)
        self.pause_duration += float(('%0*d')%(2,h) + '.' + ('%0*d')%(2,m*1.677966102))

    def consultation_done(self):
        if self.date_start:
            datetime_diff = datetime.now() - self.date_start
            m, s = divmod(datetime_diff.total_seconds(), 60)
            h, m = divmod(m, 60)
            self.appointment_duration = float(('%0*d')%(2,h) + '.' + ('%0*d')%(2,m*1.677966102)) - self.pause_duration
        self.date_end = datetime.now()
        if (self.no_invoice or self.invoice_id) and not (self.consumable_line_ids and self.appointment_invoice_policy=='advance' and not self.no_invoice and not self.consumable_invoice_id):
            self.appointment_done()
        else:
            self.state = 'done'
        if self.consumable_line_ids:
            self.consume_appointment_material() 

    def appointment_done(self):
        self.state = 'done'
        if self.company_id.sudo().auto_followup_days:
            self.follow_date = self.date + timedelta(days=self.company_id.sudo().auto_followup_days)

    def appointment_cancel(self):
        self.state = 'cancel'
        self.waiting_date_start = False
        self.waiting_date_end = False

        if self.sudo().invoice_id and self.sudo().invoice_id.state=='waiting':
            self.sudo().invoice_id.unlink()

    # def appointment_draft(self):
    #     self.state = 'draft'

    def action_prescription(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_hms_prescription_order_view")
        action['domain'] = [('appointment_id', '=', self.id)]
        action['context'] = {
                'default_patient_id': self.patient_id.id,
                'default_physician_id': self.physician_id.id,
                'default_diseases_ids': [(6,0,self.diseases_ids.ids)],
                'default_treatment_id': self.treatment_id and self.treatment_id.id or False,
                'default_appointment_id': self.id}
        return action

    def action_prescription_trouble(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_hms_prescription_order_trouble_view")
        action['domain'] = [('appointment_trouble_id', '=', self.id)]
        action['context'] = {
                'default_patient_id': self.patient_id.id,
                'default_physician_id': self.physician_id.id,
                'default_diseases_ids': [(6,0,self.diseases_ids.ids)],
                'default_treatment_id': self.treatment_id and self.treatment_id.id or False,
                'default_appointment_trouble_id': self.id}
        return action

    # def prescription_appointment_prescription(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_Prescription_appointment_Prescription")
        #action['domain'] = [('appointment_id', '=', self.id)]
        
        # return action

    def button_pres_req(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.act_open_hms_prescription_order_view")        
        action['domain'] = [('appointment_id', '=', self.id)]
        action['views'] = [(self.env.ref('acs_hms.view_hms_prescription_order_form').id, 'form')]
        action['context'] = {
                'default_patient_id': self.patient_id.id,
                'default_physician_id':self.physician_id.id,
                'default_diseases_ids': [(6,0,self.diseases_ids.ids)],
                'default_treatment_id': self.treatment_id and self.treatment_id.id or False,
                'default_appointment_id': self.id}
        return action
                
    def consume_appointment_material(self):
        for rec in self:
            if not rec.company_id.appointment_usage_location_id:
                raise UserError(_('Please define a appointment location where the consumables will be used.'))
            if not rec.company_id.appointment_stock_location_id:
                raise UserError(_('Please define a appointment location from where the consumables will be taken.'))

            dest_location_id  = rec.company_id.appointment_usage_location_id.id
            source_location_id  = rec.company_id.appointment_stock_location_id.id
            for line in rec.consumable_line_ids.filtered(lambda s: not s.move_id):
                if line.product_id.is_kit_product:
                    move_ids = []
                    for kit_line in line.product_id.acs_kit_line_ids:
                        move = self.consume_material(source_location_id, dest_location_id,
                            {'product': kit_line.product_id, 'qty': kit_line.product_qty * line.qty})
                        move.appointment_id = rec.id
                        move_ids.append(move.id)
                    #Set move_id on line also to avoid 
                    line.move_id = move.id
                    line.move_ids = [(6,0,move_ids)]
                else:
                    move = self.consume_material(source_location_id, dest_location_id,
                        {'product': line.product_id, 'qty': line.qty})
                    move.appointment_id = rec.id
                    line.move_id = move.id

    def write(self, values):
        res = super(Appointment, self).write(values)
        if 'follow_date' in values:
            self.sudo()._create_edit_followup_reminder()
        return res

    def action_view_patient_procedures(self):
        action = self.env["ir.actions.actions"]._for_xml_id("acs_hms.action_acs_patient_procedure")
        domain = [('appointment_ids', 'in', self.id)]
        if self.treatment_id:
            domain = ['|',('treatment_id', '=', self.treatment_id.id)] + domain
        action['domain'] = domain
        action['context'] = {
            'default_treatment_id': self.treatment_id and self.treatment_id.id or False,
            'default_appointment_ids': [(6,0,[self.id])],
            'default_patient_id': self.patient_id.id,
            'default_physician_id': self.physician_id.id,
            'default_department_id': self.department_id.id
        }
        return action

    def get_acs_kit_lines(self):
        if not self.acs_kit_id:
            raise UserError("Please Select Kit first.")

        lines = []
        for line in self.acs_kit_id.acs_kit_line_ids:
            lines.append((0,0,{
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'qty': line.product_qty * self.acs_kit_qty,
            }))
        self.consumable_line_ids = lines

    # Create/Edit Followup activity if needed
    def _create_edit_followup_reminder(self):
        Activity = self.env['mail.activity']
        default_activity_type = self.env['mail.activity.type'].search([],limit=1)
        res_model = self.env['ir.model'].sudo().search([('model', '=', self._name)])
        for rec in self:
            if rec.follow_date:
                company = rec.company_id.sudo() or self.env.company.sudo()
                activity_type = company.acs_followup_activity_type or default_activity_type
                if not activity_type:
                    raise UserError(_("Please Set Followup activity Type on Configiration."))
                
                followup_date = rec.follow_date - timedelta(days=1)
                if not rec.user_id:
                    rec.user_id = self.env.user.id
                user_id = rec.user_id

                existing_activity = Activity.search([('res_id', '=', rec.id),('res_model_id','=',self._name),
                    ('activity_type_id','=',activity_type.id),('user_id','=',user_id.id)])
                if existing_activity:
                    existing_activity.date_deadline = followup_date
                else:
                    activity_vals = {
                        'res_id': rec.id,
                        'res_model_id': res_model.id,
                        'activity_type_id': activity_type.id,
                        'summary': _('Appointment Followup'),
                        'date_deadline': followup_date,
                        'automated': True,
                        'user_id': user_id.id
                    }
                    self.env['mail.activity'].with_context(mail_activity_quick_update=True).create(activity_vals)


class StockMove(models.Model):
    _inherit = "stock.move"

    appointment_id = fields.Many2one('hms.appointment', string="Appointment", ondelete="restrict")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


class PrescriptionAppointmentPrescription(models.Model):
    _name = 'appointment.prescription'
    _description = "Prescription Appointment"
    notes = fields.Text(string='Notes')






# class Attachment(models.Model):
#     _inherit = "ir.attachment"
#     _rec_name = 'dates'