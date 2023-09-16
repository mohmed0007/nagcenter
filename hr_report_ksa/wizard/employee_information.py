
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning
from datetime import date, datetime
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class EmployeeContractInformation(models.TransientModel):
    _name = "employee.contract.information.report.wizard"

    _description = "employee time off Report Wizard"


    department_id = fields.Many2one('hr.department',string='Department')
    company = fields.Many2one('res.company', default=lambda self: self.env.company.id,string='Company')
    employee_ids = fields.Many2many('hr.employee' , string='Employee' , required=True)


    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {
                'employee': self.employee_ids.ids,
                'department_id': self.department_id.id,
                'company' : self.company.id
                # 'employee_ids' : self.employee_ids
            },
        }


        return self.env.ref('hr_report_ksa.employee_contract_information_report').report_action(self, data=data)





class ReportEmployeeleaveRecap(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.employee_contract_information_report_view'





    def _get_report_values(self, docids, data=None):
        docs = []

        employee = data['form']['employee']
        department = data['form']['department_id']
        # from_no = data['form']['from_no']
        # to_no = data['form']['to_no']
        company = data['form']['company']
        emp_info = self.env['hr.employee'].sudo().search([])

        department_name = ''
        # if department:
        #     emp_info = self.env['hr.employee'].search([('department_id', '=', department)], order='registration_number')

        if employee:

            contract_info = self.env['hr.contract'].search([('employee_id', 'in', employee)])

        # if from_no and to_no:
        #     emp_info = emp_info.filtered(
        #         lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))

        if department :
            contract_info = contract_info.filtered(lambda x: x.department_id.id == department)

        if company:
            contract_info = contract_info.filtered(lambda x: x.company_id.id == company)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'contract_info': contract_info,

        }






class ReportEmployeeTimeOF(models.TransientModel):
    _name = "employee.time.off.report.wizard"

    _description = "employee time off Report Wizard"

    date_from = fields.Date("From", )
    date_to = fields.Date("To", )
    department_id = fields.Many2one('hr.department',string='Department')
    company = fields.Many2one('res.company', string='Company')
    # employee_ids = fields.Many2many('hr.employee', string='Employee')


    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {

                'date_start': self.date_from,
                'date_end': self.date_to,
                'department_id': self.department_id.id,
                'company' : self.company.id
            },
        }


        return self.env.ref('hr_report_ksa.employee_time_off_report').report_action(self, data=data)




class ReportEmployeeleaveRecap(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.employee_time_off_report_view'





    def _get_report_values(self, docids, data=None):
        docs = []


        department_id = data['form']['department_id']
        # from_no = data['form']['from_no']
        # to_no = data['form']['to_no']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        # leave_type = data['form']['leave_type']
        company = data['form']['company']

        department_name = ''
        if company:
            leave_ids = self.env['hr.leave'].search([('state', '=', 'validate')], order='request_date_from asc')

        else:
            leave_ids = self.env['hr.leave'].search([('state', '=', 'validate')],
                                                  order='request_date_from asc')

        if department_id or date_start or date_end:
            print(date_start, leave_ids)
            if date_start and date_end:
                date_time_start = datetime.strptime(date_start, '%Y-%m-%d')
                date_time_end = datetime.strptime(date_end, '%Y-%m-%d')

                leave_ids = leave_ids.filtered(lambda x: x.request_date_from >= date_time_start.date() and x.request_date_to <= date_time_end.date())
            # employees = self.env['hr.employee'].search([('department_id', '=', department_id)],
                print(leave_ids.request_date_from, leave_ids.date_time_start)
            #                                            order='registration_number asc')

        if department_id:
            leave_ids = leave_ids.filtered(lambda x: x.department_id.id == department_id)
            department_name = self.env['hr.department'].search([('id', '=', department_id)], order='name asc').name
            # employees.filtered(lambda x: x.department_id.id == department_id or )
        # else:
        #     employees = self.env['hr.employee'].search([], order='registration_number asc')
        print(leave_ids, "employ * 5")
        for rec in leave_ids:
            # if emp.contract_id.state == 'open':
            register = rec.employee_id.registration_number
            emp_name = rec.employee_id.name
            department = rec.employee_id.department_id.name
            date_from = rec.request_date_from
            date_to = rec.request_date_to
            duration = rec.number_of_days
            holiday_status_id = rec.holiday_status_id.name

            docs.append({
                'register': register,
                'emp_name': emp_name,
                'emp_name': emp_name,
                'department': department,
                'date_from': date_from,
                'date_to': date_to,
                'duration': duration,
                'holiday_status_id': holiday_status_id ,


            })


        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end' : date_end ,
            'department_name': department_name,
            # 'company_name': company_name,
            'docs': docs,

        }
