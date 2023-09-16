from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning
from datetime import date, datetime
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


# from datetime import date, datetime, timedelta
# from dateutil.relativedelta import relativedelta

class CompleteSalary(models.TransientModel):
    _name = "complete.salary.report.wizard"

    _description = "Complete Salary Report Wizard"

    date_from = fields.Date("From")
    date_to = fields.Date("To")
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    date = fields.Date(string='Date',default= datetime.now())
    department_id = fields.Many2one('hr.department',string='Department', invisible=True)
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    emp_rel = fields.Many2one('hr.employee', string='Employee')

    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {
                'date': self.date,
                'date_start': self.date_from,
                'from_no': self.from_no,
                'to_no': self.to_no,
                'date_end': self.date_to,
                'department_id': self.department_id.id,
                'company' : self.company.id,
                'emp_rel' : self.emp_rel.id,
            },
        }


        return self.env.ref('hr_report_ksa.complete_salary_report').report_action(self, data=data)




class ReportCompleteSalary(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.complete_salary_report_view'

    def _get_report_values(self, docids, data=None):

        docs = []
        department_id = data['form']['department_id']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        company = data['form']['company']
        emp_rel = data['form']['emp_rel']

        dept_cont = self.env['hr.department'].search([],)
        department_name = ''
        if emp_rel:
            employees = self.env['hr.employee'].search([('employee_type', '=', 'employee'),('id', '=', emp_rel )], order='registration_number')
            print("ok")
        elif company and emp_rel:
            employees = self.env['hr.employee'].search([('company_id', '=', company),('employee_type', '=', 'employee'),('id', '=', emp_rel )], order='registration_number')
            print("ok")
        elif company:
            employees = self.env['hr.employee'].search([('company_id', '=', company),('employee_type', '=', 'employee')], order='registration_number')
            print("ok")
           
        else:
            employees = self.env['hr.employee'].search([('employee_type', '=', 'employee')], order='registration_number')

        if department_id:
            employees = employees.filtered(
                lambda x: int(x.department_id) == department_id )
            # employees = self.env['hr.employee'].search([('department_id', '=', department_id)], order='registration_number asc')
        if from_no and to_no :
            employees = employees.filtered(
                lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))

        for emp in employees:
            # if emp.contract_id.state == 'open':
                register = emp.registration_number
                emp_name = emp.name
                wage = emp.contract_id.wage
                hra = emp.contract_id.HRA
                meal_allowance = 0
                transport = emp.contract_id.TA

                gross = transport + meal_allowance + hra + wage

                docs.append({
                    'register': register,
                    'emp_name': emp_name,
                    'dept': emp.department_id,
                    'nationality': emp.country_id.name,
                    'position': emp.job_id.name,
                    'wage': wage,
                    'transport':transport,
                    'meal_allowance' : meal_allowance,
                    'hra': hra,
                    'gross' : gross,
                    'first_contract_date': emp.first_contract_date,
                    'contract_end': emp.contract_id.date_end,
                    # 'deduction': Insurance_deduction,


                })
                for rec in docs:
                    print("line" * 10, rec)





        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'from_no': from_no,
            'to_no': to_no,
            # 'date_start': date_start,
            'date': data['form']['date'],
            'department_name': department_name,
            'dept_cont' : dept_cont,
            'docs': docs,

        }





class fleet_payment(models.TransientModel):
    _name = "employees.report.wizard"

    _description = "Employees Report Wizard"

    date_from = fields.Date("From")
    date_to = fields.Date("To")
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    date = fields.Date(string='Date',default= datetime.now())
    department_id = fields.Many2one('hr.department',string='Department')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    


    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {
                'date': self.date,
                'date_start': self.date_from,
                'from_no': self.from_no,
                'to_no': self.to_no,
                'date_end': self.date_to,
                'department_id': self.department_id.id,
                'company' : self.company.id
            },
        }


        return self.env.ref('hr_report_ksa.recap_report').report_action(self, data=data)




class ReportAttendanceRecap(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.employees_recap_report_view'

    def _get_report_values(self, docids, data=None):

        docs = []
        department_id = data['form']['department_id'] 
        emp_rel = data['form']['mp_rel']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        company = data['form']['company']
        # employees = self.env['hr.employee'].search([('department_id','=',department_id)], order='name asc')
        # department_id = self.env['hr.department'].search([('id', '=', department_id)], order='name asc')
        employees = self.env['hr.employee'].search([('company_id', '=', company)], order='registration_number')

        print("")
        department_name = ''
        if department_id:
            department_name = self.env['hr.department'].search([('id', '=', department_id)], order='name asc').name
        if department_id:
            # employees = self.env['hr.employee'].search([('department_id', '=', department_id)], order='registration_number asc')
            employees = employees.filtered(
                lambda x: int(x.department_id) == department_id)
        if from_no and to_no :
            employees = employees.filtered(
                lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))

        for emp in employees:
            if emp.contract_id.state == 'open':
                register = emp.registration_number
                emp_name = emp.name
                # emp_rel = emp.address_home_id.id
                wage = emp.contract_id.wage
                hra = emp.contract_id.HRA
                da =  0
                transport = emp.contract_id.TA
                Insurance   = ( emp.contract_id.wage + emp.contract_id.HRA + emp.contract_id.TA )  * 0.12
                Insurance_deduction =  ( emp.contract_id.wage + emp.contract_id.HRA + emp.contract_id.TA )   * 0.10
                fix = 0
                other = 0

                hr_attendance = self.env['hr.attendance'].search([('employee_id', '=', emp.id)])
                hr_loan = self.env['hr.loan'].search([('employee_id', '=', emp.id),('state', '=','approve')])
                late_amount = 0
                loan_amount = hr_loan.mapped('balance_amount')
                # late_amount = sum(late_amount)
                loan_amount = sum(loan_amount)

                total_late = 0.0
                print(">>>>>>>>>>>>>>>>>>>>>>",docs)

                docs.append({
                    'register': register,
                    'wage': wage,
                    'emp_name': emp_name,
                    # 'emp_rel':emp_rel,
                    'hra': hra,
                    'transport': transport,
                    'da': da,
                    'fix': fix,
                    'other' : other,
                    # 'total_late': late_amount,
                    'Insurance': Insurance,
                    'deduction': Insurance_deduction,


                })
                for rec in docs:
                    print("line" * 10, rec)





        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            # 'date_start': date_start,
            'date': data['form']['date'],
            'department_name': department_name,
            'docs': docs,

        }

