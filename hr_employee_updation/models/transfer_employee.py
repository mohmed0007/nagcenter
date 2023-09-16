# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import time


class TransferEmployee(models.Model):
    _name = 'transfer.employee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Staff Action"

    name = fields.Char('Reference', size=64, required=True, default=_('New'))
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=lambda self: self.env['hr.employee'].get_employee())
    hr_contract_id = fields.Many2one('hr.contract', 'Contract', required=True, domain="[('employee_id', '=', employee_id)]")
    job_id = fields.Many2one('hr.job', 'From Job', readonly=True)
    department_id = fields.Many2one('hr.department', 'From Department', readonly=True)
    branch_id = fields.Many2one('hr.branch', string='Branch', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    effective_date = fields.Date('Effective Date', default=time.strftime('%Y-%m-%d'))
    grade_id = fields.Many2one('hr.grade', 'From Grade', readonly=True)
    new_grade_id = fields.Many2one('hr.grade', 'To Grade')
    new_department_id = fields.Many2one('hr.department', 'To Department')
    new_job_id = fields.Many2one('hr.job', 'To Job')
    new_branch_id = fields.Many2one('hr.branch', 'To Branch')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Waiting Approval'),
        ('validate', 'Waiting HR Department Approval'),
        ('approve', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancel')], 'State', default='draft', tracking=True)
    description = fields.Text('Description')
    
    #Type of action(Boolean)
    confirmation = fields.Boolean('Confirmation')
    promotion = fields.Boolean('Promotion')
    title_change = fields.Boolean('Title Change')
    salary_revision = fields.Boolean('Salary Revision')
    grade_revision = fields.Boolean('Grade Revision')
    branch_revision = fields.Boolean('Branch Revision')
    other = fields.Boolean('Other')
    extension = fields.Boolean('Extension')
    extension_period = fields.Date('Extension Period')

    basic = fields.Monetary('Basic', tracking=True, help='Basic Salary of Employee')
    HRA = fields.Monetary(string='Housing Allowance', help="HRA of employee", tracking=True)
    TA = fields.Monetary(string='Transport Allowance', help="Transport Allowance of employee", tracking=True)
    other_amt = fields.Monetary('Management Allowance', tracking=True)
    other_amt2 = fields.Monetary('Fixed/OT Amount', tracking=True)
    gross_amt = fields.Monetary('Gross Salary', store=True)
    
    new_basic = fields.Monetary('New Basic', tracking=True, help='Basic Salary of Employee')
    new_HRA = fields.Monetary(string='New Housing Allowance', help="HRA of employee", tracking=True)
    new_TA = fields.Monetary(string='New Transport Allowance', help="Transport Allowance of employee", tracking=True)
    new_other_amt = fields.Monetary('New Management Allowance', tracking=True)
    new_other_amt2 = fields.Monetary('New Fixed/OT Allowance', tracking=True)
    new_gross_amt = fields.Monetary('New Gross Salary', compute='_get_new_amount', store=True)
    
    approved_date = fields.Datetime('Approved Date', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', 'Approved by', readonly=True, copy=False)
    validated_by = fields.Many2one('res.users', 'Validated by', readonly=True, copy=False)
    validated_date = fields.Datetime('Validated Date', readonly=True, copy=False)

    @api.onchange('hr_contract_id','salary_revision','employee_id')
    def _onchange_contract_amount(self):
        for rec in self:
            rec.basic = 0.0
            rec.HRA = 0.0
            rec.TA = 0.0
            if rec.hr_contract_id:
                rec.basic = rec.hr_contract_id.wage 
                rec.HRA = rec.hr_contract_id.HRA
                rec.TA = rec.hr_contract_id.TA
                rec.other_amt = rec.hr_contract_id.other_amt 
                rec.other_amt2 = rec.hr_contract_id.other_amt2
                rec.gross_amt = rec.hr_contract_id.gross_amt


    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            effective_date = time.strftime('%Y-%m-%d')
            payslip_obj = self.env['hr.payslip']
            contract_ids = self.employee_id._get_contracts(effective_date, effective_date, states=['open'])
            if not contract_ids:
                self.employee_id = False
                self.hr_contract_id = False
                raise UserError(_('Please define contract for selected Employee!'))
            contract = payslip_obj.browse(contract_ids)
            self.department_id = self.employee_id.department_id.id or False
            self.job_id = self.employee_id.job_id.id or False
            self.branch_id = self.employee_id.branch_id.id or False
            self.hr_contract_id = contract and contract[0].id or False
            self.grade_id = self.employee_id.grade_id.id or False
            
    @api.onchange('new_department_id')
    def onchange_department(self):
        self.new_job_id = False

    @api.depends('new_basic', 'new_HRA', 'new_TA', 'new_other_amt', 'new_other_amt2')
    def _get_new_amount(self):
        for contract in self:
            contract.gross_amt = 0.0
            if contract.new_basic > 0:
                contract.new_gross_amt = contract.new_basic + contract.new_HRA + contract.new_TA + \
                                     contract.new_other_amt + contract.new_other_amt2

    @api.model
    def create(self, values):
        if values.get('company_id'):
            values['name'] = self.env['ir.sequence'].with_context(company=values['company_id']).next_by_code(
                'transfer.employee') or _('New')
        else:
            values['name'] = self.env['ir.sequence'].next_by_code('transfer.employee') or _('New')
        return super(TransferEmployee, self).create(values)

    def unlink(self):
        for objects in self:
            if objects.state in ['confirm', 'validate', 'approve', 'done', 'cancel']:
                raise UserError(_('You cannot remove the record which is in %s state!') % objects.state)
        return super(TransferEmployee, self).unlink()

    def _add_followers(self):
        partner_ids = []
        if self.employee_id.user_id:
            partner_ids.append(self.employee_id.user_id.partner_id.id)
        if self.employee_id.parent_id.user_id:
            partner_ids.append(self.employee_id.parent_id.user_id.partner_id.id)
        self.message_subscribe(partner_ids=partner_ids)

    def transfer_confirm(self):
        self.ensure_one()
        self.state = 'confirm'

    def transfer_validate(self):
        self.ensure_one()
        today = datetime.today()
        user = self.env.user
        self.write({'state': 'validate',
                    'validated_by': user.id,
                    'validated_date': today})

    def transfer_approve(self):
        self.ensure_one()
        today = datetime.today()
        user = self.env.user
        self.write({'state': 'approve',
                    'approved_by': user.id,
                    'approved_date': today})

    def get_employee_data(self, employee_id, contract=False):
        if contract:
            employee_id.write({'department_id': contract.new_department_id.id or False,
                               'grade_id': contract.new_grade_id.id or False,
                               'job_id': contract.new_job_id.id or False,
                               'branch_id': self.new_branch_id.id or False
                               })
        else:
            employee_id.write({'department_id': self.new_department_id.id or False,
                               'grade_id': self.new_grade_id.id or False,
                               'job_id': self.new_job_id.id or False,
                               'branch_id': self.new_branch_id.id or False
                               })

    def transfer_done(self):
        self.ensure_one()
        if self.effective_date <= datetime.today().date():
            if self.employee_id:
                self.employee_id.department_id = (self.new_department_id and self.new_department_id.id) or (self.employee_id.department_id and self.employee_id.department_id.id)
                self.employee_id.grade_id = (self.new_grade_id and self.new_grade_id.id) or (self.employee_id.grade_id and self.employee_id.grade_id.id)
                self.employee_id.job_id = (self.new_job_id and self.new_job_id.id) or (self.employee_id.job_id and self.employee_id.job_id.id)
                self.employee_id.branch_id = (self.new_branch_id and self.new_branch_id.id) or (self.employee_id.branch_id and self.employee_id.branch_id.id)
                

            if self.hr_contract_id.date_end and self.effective_date >= self.hr_contract_id.date_end:
                structure_ids = self.env['hr.payroll.structure.type'].search([])
                vals = {'name': self.employee_id.name,
                        'department_id': self.new_department_id.id or False,
                        'job_id': self.new_job_id.id or False,
                        'employee_id': self.employee_id.id,
                        'date_start': self.effective_date,
                        'structure_type_id': structure_ids[0] if structure_ids else False, 
                        'wage': 0.0
                        }
                self.env['hr.contract'].create(vals)
            else:
                self.hr_contract_id.write({'department_id': self.new_department_id.id or False,
                                           'job_id': self.new_job_id.id or False,
                                            })
                if self.salary_revision:
                    self.hr_contract_id.write({
                        'wage': self.new_basic,
                        'HRA': self.new_HRA,
                        'TA': self.new_TA,
                        'other_amt': self.new_other_amt,
                        'other_amt2': self.new_other_amt2,
                        })
            self.get_employee_data(self.employee_id)
            self.state = 'done'
        else:
            raise ValidationError(_('You Can not Done the Contract Amendment Because Effective Date is %s.') % self.effective_date)

    def check_staff_action_effective_date(self):
        contract_amendment = self.search([('effective_date', '=', datetime.today()), ('state', '=', 'approve')])
        for contract in contract_amendment:
            if contract.hr_contract_id and contract.hr_contract_id.date_end and contract.effective_date >= contract.hr_contract_id.date_end:
                structure_ids = self.env['hr.payroll.structure.type'].search([])
                vals = {'name': contract.employee_id.name,
                        'department_id': contract.new_department_id.id or False,
                        'job_id': contract.new_job_id.id or False,
                        'employee_id': contract.employee_id.id,
                        'date_start': contract.effective_date,
                        'structure_type_id': structure_ids[0] if structure_ids else False, 
                        'wage': 0.0
                        }
                self.env['hr.contract'].create(vals)
            else:
                contract.hr_contract_id.write({'department_id': contract.new_department_id.id or False,
                                               'job_id': contract.new_job_id.id or False,
                                               })
                if self.salary_revision:
                    contract.hr_contract_id.write({
                        'wage': contract.new_basic,
                        'HRA': contract.new_HRA,
                        'TA': contract.new_TA,
                        'other_amt': contract.new_other_amt,
                        'other_amt2': contract.new_other_amt2,
                        })
            if contract.employee_id:
                self.get_employee_data(contract.employee_id, contract)
                contract.state = 'done'

    def transfer_cancel(self):
        self.ensure_one()
        self.state = 'cancel'

    def set_to_draft(self):
        self.ensure_one()
        self.employee_id.department_id = self.department_id.id or False
        self.employee_id.grade_id = self.grade_id.id or False
        self.employee_id.job_id = self.job_id.id or False
        self.employee_id.branch_id = self.branch_id.id or False
        
        self.write({'state': 'draft',
                    'approved_by': False,
                    'approved_date': False,
                    'validated_by': False,
                    'validated_date': False})
