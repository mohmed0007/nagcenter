from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

from datetime import datetime, date


class EmployeeReportDetail(models.TransientModel):
    _name = 'employee.report.details'

    employee = fields.Many2many('hr.employee')
    department = fields.Many2one('hr.department')

    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'employee': self.employee.ids,
                'department': self.department.id,
                'from_no': self.from_no,
                'to_no': self.to_no,
                'company' : self.company.id
            },
        }
        return self.env.ref('hr_report_ksa.hr_report_emp_details_19').report_action(self, data=data)


class ComplexReports(models.AbstractModel):
    _name = 'report.hr_report_ksa.template_hr_report_emp_details_19'

    @api.model
    def _get_report_values(self, docids, data=None):
        employee = data['form']['employee']
        department = data['form']['department']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        company = data['form']['company']
        emp_info = self.env['hr.employee'].sudo().search([])

        if department:
            emp_info = self.env['hr.employee'].search([('department_id', '=', department)], order='registration_number')

        if employee:
            emp_info = self.env['hr.employee'].search([('id', 'in', employee)], order='registration_number')

        if from_no and to_no:
            emp_info = emp_info.filtered(
                lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))

        if  company :
            emp_info = emp_info.filtered(lambda x: x.company_id.id == company)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'emps_info': emp_info,

        }


class EmployeeDepartment(models.TransientModel):
    _name = 'employee.report.department'

    department = fields.Many2one('hr.department')
    employee = fields.Many2many('hr.employee')

    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'employee': self.employee.ids,
                'department': self.department.id,
                'from_no': self.from_no,
                'to_no': self.to_no,
            },
        }
        return self.env.ref('hr_report_ksa.emp_report_info').report_action(self, data=data)


class ComplexReportsDepartment(models.AbstractModel):
    _name = 'report.hr_report_ksa.template_emp_report_info'

    @api.model
    def _get_report_values(self, docids, data=None):
        employee = data['form']['employee']
        department = data['form']['department']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        docs = []
        emps_total = self.env['hr.employee'].sudo().search_count([])
        emp_info = self.env['hr.employee'].sudo().search([])

        if department:
            emp_info = self.env['hr.employee'].search([('department_id', '=', department)], order='registration_number')

        if employee:
            emp_info = self.env['hr.employee'].search([('id', 'in', employee)], order='registration_number')

        if from_no and to_no:
            emp_info = emp_info.filtered(
                lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))

        contract_id = emp_info.contract_id
        department_info = self.env['hr.department'].sudo().search([('id', '=', department)])

        for rec in emp_info:
            contract = self.env['hr.contract'].sudo().search([('employee_id', '=', rec.id), ('state', '=', 'open')])
            docs.append({
                'registration_number': rec.registration_number,
                'name': rec.name,
                'country_id': rec.country_id.name,
                'joining_date': rec.joining_date,
                'insr_date': contract.insr_date,
                'insr_place': contract.insr_place,
                'insr_salary': contract.insr_salary,
                'insurance_employee': contract.insurance_employee,
                'insurance_company': contract.insurance_company,
                'total': contract.insurance_company + contract.insurance_employee,
            })
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'emps_info': emp_info,
            'department_info': department_info,
            'contract_id': contract_id,
            'emps_total': emps_total,
            'docs': docs,
        }


class Leaves(models.TransientModel):
    _name = 'employee.leave.tic'

    department = fields.Many2one('hr.department')
    employee = fields.Many2many('hr.employee')
    leave_type = fields.Many2one('hr.leave.type', string='Leave type')
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'employee': self.employee.ids,
                'department': self.department.id,
                'leave_type': self.leave_type.id,
                'from_no': self.from_no,
                'to_no': self.to_no,
                'company': self.company.id,
            },
        }
        return self.env.ref('hr_report_ksa.leaves_and_tic_emp_report_info').report_action(self, data=data)


class LeavesReport(models.AbstractModel):
    _name = 'report.hr_report_ksa.template_leaves_and_tic_emp'

    @api.model
    def _get_report_values(self, docids, data=None):
        employee = data['form']['employee']
        department = data['form']['department']
        leave_type = data['form']['leave_type']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        company = data['form']['company']

        docs = []
        leave_type_info = self.env['hr.leave.type'].sudo().browse(int(leave_type))
        employees_re = self.env['hr.employee'].sudo().search([('contract_id.state', '=', 'open')], order='registration_number')
        print("test"*5,employees_re )

        if department:
            employees_re = self.env['hr.employee'].sudo().search([('department_id', '=', department),('contract_id.state', '=', 'open')], order='registration_number')

        if employee:
            employees_re = self.env['hr.employee'].sudo().search([('id', 'in', employee),('contract_id.state', '=', 'open')], order='registration_number')

        if from_no and to_no:
            employees_re = employees_re.filtered(
                lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))
            print("osman"*4,employees_re)
        if employees_re :
           self._cr.execute("""
                            SELECT
                                sum(h.number_of_days) AS days,
                                h.employee_id
                            FROM
                                (
                                    SELECT holiday_status_id, number_of_days,
                                        state, employee_id
                                    FROM hr_leave_allocation
                                    UNION ALL
                                    SELECT holiday_status_id, (number_of_days * -1) as number_of_days,
                                        state, employee_id
                                    FROM hr_leave
                                ) h
                                join hr_leave_type s ON (s.id=h.holiday_status_id)
                            WHERE
                                s.active = true AND h.state='validate' AND
                                (s.allocation_type='fixed' OR s.allocation_type='fixed_allocation') AND
                                h.employee_id in %s AND h.holiday_status_id = %s
                            GROUP BY h.employee_id""", (tuple(employees_re.ids), leave_type))

           remaining = dict((row['employee_id'], row['days']) for row in self._cr.dictfetchall())
        alldata = self.env['hr.leave.allocation'].read_group([
            ('employee_id', 'in', employees_re.ids),
            ('holiday_status_id.active', '=', True),
            ('holiday_status_id', '=', leave_type),
            ('state', '=', 'validate'),
        ], ['number_of_days:sum', 'employee_id'], ['employee_id'])

        alldata1 = self.env['hr.leave'].read_group([
            ('employee_id', 'in', employees_re.ids),
            ('holiday_status_id.active', '=', True),
            ('holiday_status_id', '=', leave_type),
            ('state', '=', 'validate'),
        ], ['number_of_days:sum', 'employee_id'], ['employee_id'])
        rg_results = dict((d['employee_id'][0], d['number_of_days']) for d in alldata)
        rg_results1 = dict((d['employee_id'][0], d['number_of_days']) for d in alldata1)

        for emp in employees_re:
            # if emp.id in list(employee):
            register = emp.registration_number
            emp_name = emp
            country = emp.country_id.nationality_name
            job_id = emp.job_id
            first_contract_date = emp.first_contract_date
            allocation_leave_total = rg_results.get(emp.id, 0.0)
            time_of_leave_total = rg_results1.get(emp.id, 0.0)

            difference = relativedelta(date.today(), emp.contract_id.first_contract_date)
            tickets_value = self.env['flight.ticket.allocation'].sudo().search([('employee_id', '=', emp.id)])
            balance = tickets_value.mapped('balance')
            balance_taken = tickets_value.mapped('balance_taken')
            remain = 0.0
            for key in remaining.keys():
                print(key)
                if key == emp.id:
                    remain = remaining[key]
            docs.append({
                'register': register,
                'emp_name': emp_name,
                'emp_contract': self.env['hr.contract'].sudo().search(
                    [('employee_id', '=', emp_name.id), ('state', '=', 'open')]),
                'nationality': country,
                'department_id': emp.department_id.name,
                'job_id': job_id.name,
                'first_contract_date': first_contract_date,
                'allocation_leave_total': allocation_leave_total,
                'time_of_leave_total': time_of_leave_total,
                'remain': remain,
                'net_service_days': difference.days,
                'net_service_months': difference.months,
                'net_service_years': difference.years,
                'balance': sum(balance),
                'balance_taken': sum(balance) - sum(balance_taken),

            })

        emp_info = self.env['hr.employee'].sudo().search([('id', 'in', employee)])
        contract_id = emp_info.contract_id
        department_info = self.env['hr.department'].sudo().search(
            [('id', '=', department if department else self.env['hr.department'].sudo().search([]).ids)])

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'emps_info': emp_info,
            'department_info': department_info,
            'contract_id': contract_id,
            'leave_type': leave_type_info,
            'docs': docs,
        }
