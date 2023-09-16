from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
# from datetime import date, datetime, timedelta
from datetime import datetime
from dateutil import relativedelta

class RecruitAndResignation(models.TransientModel):
    _name = "recruit.resignation.report.wizard"
    _description = "employee recruit report wizard"

    date_from = fields.Date("From date")
    date_to = fields.Date("To date")
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    date = fields.Date(string='Date', default=datetime.now())
    department_id = fields.Many2one('hr.department', string='Department')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    def get_report1(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {
                'from_no': self.from_no,
                'to_no': self.to_no,
                'date': self.date,
                'date_start': self.date_from,
                'date_end': self.date_to,
                'department_id': self.department_id.id,
                'company': self.company.id

            },

        }


        return self.env.ref('hr_report_ksa.recap_recruit_resignation_report').report_action(self, data=data)




class ReportRecruitResignation(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.employee_recruit_resignation_report_view'

    def _get_report_values(self, docids, data=None):

        docs = []
        department_id = data['form']['department_id']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        company = data['form']['company']


        department_name = ''
        if company :
           employees = self.env['hr.employee'].search([('joining_date', '!=', False),('company_id', '=', company)], order='employee_number')
        else:
            employees = self.env['hr.employee'].search([('joining_date', '!=', False)],order='employee_number')

        employees_resignation = self.env['hr.resignation'].search([], order='employee_number')
        if date_start and date_end:
            print(date_start, employees,employees_resignation)
            date_time_start = datetime.strptime(date_start, '%Y-%m-%d')
            date_time_end = datetime.strptime(date_end, '%Y-%m-%d')
            # employees = employees.filtered(lambda x: x.joining_date >= date_time_start.date() and x.joining_date <= date_time_end.date())
            employees_resignation = employees_resignation.filtered(lambda x: x.approved_revealing_date >= date_time_start.date()
                                                                             and x.approved_revealing_date <= date_time_end.date())

        if from_no and to_no:
            employees = employees.filtered(lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))

        if department_id:
           employees = employees.filtered(lambda x: x.department_id.id == department_id)
           department_name = self.env['hr.department'].search([('id', '=', department_id)], order='name asc').name
        arabian = 0
        non_arabian = 0
        print(employees,employees_resignation,"employ")
        for res in employees_resignation:
            print(res.employee_number)
            register = res.employee_id.registration_number
            emp_name = res.employee_id.name
            department = res.employee_id.department_id.name
            education = res.employee_id.certificate
            joining_date = res.employee_id.joining_date
            resignation_date = res.approved_revealing_date
            reason = res.description1


            if res.employee_id.country_id.code == 'SA' :
               arabian += 1

            else:
               non_arabian += 1



            docs.append({
                    'register': register,
                    'emp_name': emp_name,
                    'department': department,
                    'education': education,
                    'joining_date': joining_date ,
                    'resignation_date': resignation_date,
                    'reason' : reason,
                    # 'job_position':job_position,
                    # 'work_location': work_location



                })


        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            # 'date_start': date_start,
            'date': data['form']['date'],
            'department_name': department_name,
            'docs': docs,
            'arabian' : arabian,
            'non_arabian' : non_arabian

        }






class EmployeeRecruit(models.TransientModel):
    _name = "employee.recruit.report.wizard"
    _description = "employee recruit report wizard"

    date_from = fields.Date("From date")
    date_to = fields.Date("To date")
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    date = fields.Date(string='Date', default=datetime.now())
    department_id = fields.Many2one('hr.department', string='Department')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    def get_report1(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {
                'from_no': self.from_no,
                'to_no': self.to_no,
                'date': self.date,
                'date_start': self.date_from,
                'date_end': self.date_to,
                'department_id': self.department_id.id,
                'company' : self.company.id

            },

        }


        return self.env.ref('hr_report_ksa.recap_recruit_report').report_action(self, data=data)




class ReportServiceDuration(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.employee_recruit_report_view'

    def _get_report_values(self, docids, data=None):

        docs = []
        department_id = data['form']['department_id']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        company = data['form']['company']


        department_name = ''
        if company :
           employees = self.env['hr.employee'].search([('joining_date', '!=', False),('company_id','=',company)], order='employee_number')
        else:
            employees = self.env['hr.employee'].search([('joining_date', '!=', False)],
                                                       order='employee_number')

        if date_start and date_end:
            print(date_start, employees)
            date_time_start = datetime.strptime(date_start, '%Y-%m-%d')
            date_time_end = datetime.strptime(date_end, '%Y-%m-%d')

            employees = employees.filtered(lambda x: x.joining_date >= date_time_start.date() and x.joining_date <= date_time_end.date())


        if from_no and to_no:
            employees = employees.filtered(lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))

        if department_id:
           employees = employees.filtered(lambda x: x.department_id.id == department_id)
           department_name = self.env['hr.department'].search([('id', '=', department_id)], order='name asc').name
        arabian = 0
        non_arabian = 0
        print(employees,"employ")
        for emp in employees:
                print(emp.employee_number)
                register = emp.registration_number
                emp_name = emp.name
                department = emp.department_id.name
                work_location = emp.work_location
                job_position = emp.job_title
                nationality = emp.country_id.nationality_name
                wage = emp.contract_id.wage
                first_contract_date = emp.first_contract_date
                date_end = emp.contract_id.date_end
                project_task = self.env['project.task'].search([('user_id', '=', emp.user_id.id) ],limit=1)
                hr_loan = self.env['hr.loan'].search([('employee_id', '=', emp.id), ('state', '=', 'approve')])
                if emp.country_id.code == 'SA' :
                    arabian += 1

                else:
                    non_arabian += 1



                docs.append({
                    'register': register,
                    'wage': wage,
                    'emp_name': emp_name,
                    'department': department,
                    'nationality': nationality,
                    'insurance_no': 124 ,
                    'job_position': job_position,
                    'recruit_date' : first_contract_date,



                })


        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            # 'date_start': date_start,
            'date': data['form']['date'],
            'from_no': from_no,
            'to_no': to_no,
            'date_start': date_start,
            'date_end': date_end,
            'department_name': department_name,
            'docs': docs,
            'arabian' : arabian,
            'non_arabian' : non_arabian

        }






class ServiceDuration(models.TransientModel):
    _name = "service.duration.report.wizard"

    _description = "mandate report wizard"

    date_from = fields.Date("From date")
    date_to = fields.Date("To date" , default= datetime.now())
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    date = fields.Date(string='Date',default= datetime.now())
    department_id = fields.Many2one('hr.department',string='Department')
    company = fields.Many2one('res.company', string= 'Company',default=lambda self: self.env.company.id )



    def get_report1(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {
                'from_no': self.from_no,
                'to_no': self.to_no,
                'date': self.date,
                'date_start': self.date_from,
                'date_end': self.date_to,
                'department_id': self.department_id.id,
                'company' : self.company.id

            },

        }


        return self.env.ref('hr_report_ksa.recap_service_duration_report').report_action(self, data=data)



class ReportServiceDuration(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.recap_service_duration__view'

    def _get_report_values(self, docids, data=None):

        docs = []
        department_id = data['form']['department_id']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        company = data['form']['company']
        # employees = self.env['hr.employee'].search([('department_id','=',department_id)], order='name asc')
        # department_id = self.env['hr.department'].search([('id', '=', department_id)], order='name asc')

        department_name = ''
        if company :
           employees = self.env['hr.employee'].search([('joining_date', '!=', False), ('company_id', '=', company)], order='employee_number')
        else:
           employees = self.env['hr.employee'].search([('joining_date', '!=', False)],
                                                   order='employee_number')
        if date_start and date_end:
            print(date_start, employees)
            date_time_start = datetime.strptime(date_start, '%Y-%m-%d')
            date_time_end = datetime.strptime(date_end, '%Y-%m-%d')

            employees = employees.filtered(lambda x: x.joining_date >= date_time_start.date() and x.joining_date <= date_time_end.date())
            # employees = self.env['hr.employee'].search([('department_id', '=', department_id)],
            #                                            order='registration_number asc')

        if from_no and to_no:
            employees = employees.filtered(lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))
            # print("Osman", mandate_records, )
        if department_id:
           employees = employees.filtered(lambda x: x.department_id.id == department_id)
           department_name = self.env['hr.department'].search([('id', '=', department_id)], order='name asc').name
            # employees.filtered(lambda x: x.department_id.id == department_id or )
        # else:
        #     employees = self.env['hr.employee'].search([], order='registration_number asc')
        print(employees,"employ")
        for emp in employees:
            # if emp.contract_id.state == 'open':
                print(emp.employee_number)
                register = emp.registration_number
                emp_name = emp.name
                department = emp.department_id.name
                work_location = emp.work_location
                job_position = emp.job_title
                nationality = emp.country_id.nationality_name
                wage = emp.contract_id.wage
                first_contract_date = emp.first_contract_date
                date_end = emp.contract_id.date_end
                project_task = self.env['project.task'].search([('user_id', '=', emp.user_id.id) ],limit=1)
                hr_loan = self.env['hr.loan'].search([('employee_id', '=', emp.id), ('state', '=', 'approve')])

                # date1 = datetime(str(first_contract_date))
                # date2 = datetime(str(date.today()))
                diff = relativedelta.relativedelta( date_time_end if date_time_end else date.today(), first_contract_date)


                years = diff.years
                months = diff.months
                days = diff.days


                total_late = 0.0
                # total_salary = wage + allowance
                # loan = 0.0
                # net_salary = total_salary - loan_amount
                docs.append({
                    'register': register,
                    'wage': wage,
                    'emp_name': emp_name,
                    'department': department,
                    'work_location': work_location,
                    'project' : project_task.project_id.name,
                    'job_position': job_position,
                    'nationality': nationality,
                    'wage': wage,
                    'first_contract_date': first_contract_date,
                    'date_end': date_end,
                    'years': years,
                    'months' : months,
                    'days' : days


                })
                # for rec in docs:
                #     print("line" * 10, rec)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            # 'date_start': date_start,
            'from_no': from_no,
            'to_no': to_no,
            'date_start': date_start,
            'date_end': date_end,
            'date': data['form']['date'],
            'department_name': department_name,
            'docs': docs,

        }





class MandateReport(models.TransientModel):
    _name = "mandate.report.wizard"

    _description = "mandate report wizard"

    date_from = fields.Date("From date")
    date_to = fields.Date("To date")
    date = fields.Date(string='Date',default= datetime.now())
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    department_id = fields.Many2one('hr.department',string='Department')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {
                'from_no' : self.from_no,
                'to_no' : self.to_no,
                'date': self.date,
                'date_start': self.date_from,
                'date_end': self.date_to,
                'department_id': self.department_id.id,
                'company' : self.company.id
            },
        }


        return self.env.ref('hr_report_ksa.recap_mandate_report').report_action(self, data=data)




class ReportMandate(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.mandate_recap_report_view'

    def _get_report_values(self, docids, data=None):

        docs = []
        department_id = data['form']['department_id']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        company = data['form']['company']
        department_name = ''
        if company :
           mandate_records = self.env['hr.mandate'].search([('company_id', '=', company)], order='employee_number ')
        else:
            mandate_records = self.env['hr.mandate'].search([], order='employee_number ')
        if date_start and date_end:
            print(date_start,mandate_records)
            date_time_start = datetime.strptime(date_start, '%Y-%m-%d')
            date_time_end = datetime.strptime(date_end, '%Y-%m-%d')
            mandate_records = mandate_records.filtered(lambda x: x.date_from >= date_time_start <= date_time_end )
            # mandate_records = self.env['hr.mandate'].search(
            #     [('date_from', '>=', date_start),('date_from', '<=', date_end)])

            print("Osman",mandate_records,date_start,date_end)
        if from_no and to_no:
            mandate_records = mandate_records.filtered(lambda x: int(x.employee_id.registration_number) >= int(from_no) and
                                                                 int(x.employee_id.registration_number) <= int(to_no))

            print("Osman", mandate_records,)
        if department_id:
            mandate_records = mandate_records.filtered(lambda x: x.department_id.id == department_id)
            department_name = self.env['hr.department'].search([('id', '=', department_id)], order='name asc').name
            employees = self.env['hr.employee'].search([('department_id', '=', department_id)], order='employee_number ')
        # else:
        #     employees = self.env['hr.employee'].search([], order='registration_number asc')
        #     # mandate_records = self.env['hr.mandate'].search([], order='registration_number asc')


        for mandate in mandate_records:
            # if emp.contract_id.state == 'open':
                register = mandate.employee_id.registration_number
                emp_name = mandate.employee_id.name
                date_from = mandate.date_from.date()
                date_to = mandate.date_to.date()
                days_no = mandate.days_no
                mandate_to = mandate.mandate_to
                mandate_per_day = mandate.mandate_per_day
                transportation_allowance = mandate.transportation_allowance
                other_expanse = mandate.other_expanse
                total_amount = mandate.total_amount

                docs.append({
                    'register': register,
                    'emp_name': emp_name,
                    'date_from': date_from,
                    'date_to': date_to,
                    'mandate_to': mandate_to,
                    'days_no': days_no,
                    'mandate_per_day': mandate_per_day,
                    'transportation_allowance': transportation_allowance,
                    'other_expanse': other_expanse,
                    'total_amount': total_amount,

                })






        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            # 'date_start': date_start,
            'from_no': from_no,
            'to_no': to_no,
            'date_start': date_start,
            'date_end': date_end,
            'date': data['form']['date'],
            'department_name': department_name,
            'docs': docs,

        }

 # wizard of employee EndOfService  report

class EndOfSevice(models.TransientModel):
    _name = "end.of.service.wizard"

    _description = "end of service report wizard"

    date_from = fields.Date("From date")
    date_to = fields.Date("To date")
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    date = fields.Date(string='Date',default= datetime.now())
    department_id = fields.Many2one('hr.department',string='Department')
    company = fields.Many2one('res.company', string= 'Company',default=lambda self: self.env.company.id )



    def get_report1(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {
                'from_no': self.from_no,
                'to_no': self.to_no,
                'date': self.date,
                'date_start': self.date_from,
                'date_end': self.date_to,
                'department_id': self.department_id.id,
                'company_id' : self.company.id

            },

        }


        return self.env.ref('hr_report_ksa.recap_end_of_service_report').report_action(self, data=data)




class EndOfService(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.end_of_service_view'

    def _get_report_values(self, docids, data=None):

        docs = []
        department_id = data['form']['department_id']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        company_id = data['form']['company_id']
        department_name = ''
        department_name = ''
        employees = self.env['hr.employee'].search([],order='employee_number')
        department_name = ''
        if department_id:
            department_name = self.env['hr.department'].search([('id', '=', department_id)], order='name asc').name
        if department_id:
            # employees = self.env['hr.employee'].search([('department_id', '=', department_id)],
            #                                            order='registration_number asc')
            employees = employees.filtered(lambda x : x.department_id.id == department_id )
        if company_id :
            employees = employees.filtered(lambda x: x.company_id.id == company_id)
        if from_no and to_no:
            employees = employees.filtered(
                lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))

        for emp in employees:
            if emp.contract_id.state == 'open':
                register = emp.registration_number
                emp_name = emp.name
                emp_nationality = emp.country_id
                emp_join_date = emp.first_contract_date
                # salary = ( emp.contract_id.wage + emp.contract_id.hra + emp.contract_id.da +
                #            emp.contract_id.fix_allowance + emp.contract_id.other_allowance +
                #            emp.contract_id.transport_allowance)
                Insurance = emp.contract_id.deduced_company_per_month
                Insurance_deduction = emp.contract_id.deduced_employee_per_month

                hr_loan = self.env['hr.loan'].search([('employee_id', '=', emp.id), ('state', '=', 'approve')])
                loan_amount = hr_loan.mapped('balance_amount')
                loan_amount = sum(loan_amount)
                difference = relativedelta.relativedelta(to_no if to_no else date.today(), emp_join_date)
                years = difference.years
                months = difference.months
                days = difference.days
                print('{} years {} months {} days'.format(years, months, days))
                total_late = 0.0
                # end of service benefit calculation code
                total_days = difference.years * 360 + difference.months * 30 + difference.days
                compensation = (emp.contract_id.wage + emp.contract_id.hra + \
                               emp.contract_id.da + emp.contract_id.meal_allowance + emp.contract_id.fix_allowance + emp.contract_id.other_allowance )
                result = 0
                if total_days <= 360 :
                    result = 0
                elif 360 < total_days <= 5 * 360:
                    result = compensation / 2 * total_days / 360
                else:
                    result = (compensation / 2 * 5 * 360 + compensation * (total_days - 5 * 360)) / 360

                docs.append({
                    'register': register,
                    'emp_name': emp_name,
                    'nationality' : emp_nationality.name ,
                    'join_date' : emp_join_date,
                    'salary': compensation,
                    'year' : years ,
                    'month': months ,
                    'day' : days,
                    'duration_in_days' : total_days ,
                    'Benefit' : "{:.2f}".format(result)  ,
                    'loan_amount': "{:.2f}".format(loan_amount) ,
                    'net' :"{:.2f}".format(result - loan_amount) ,


                })
                for rec in docs:
                    print("line" * 10, rec)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end' : date_end ,
            'from_no' : from_no ,
            'to_no' : to_no ,
            'date': data['form']['date'],
            'department_name': department_name,
            'docs': docs,

        }

#
# class EndOfSevice(models.TransientModel):
#     _name = "end.of.service.wizard"
#
#     _description = "end of service report wizard"
#
#     date_from = fields.Date("From date")
#     date_to = fields.Date("To date")
#     from_no = fields.Char(string='From Employee No')
#     to_no = fields.Char(string='To Employee No')
#     date = fields.Date(string='Date',default= datetime.now())
#     department_id = fields.Many2one('hr.department',string='Department')
#     company_id = fields.Many2many('res.company')
#
#
#
#     def get_report1(self):
#         """Call when button 'Get Report' clicked.
#         """
#         data = {
#             'ids': self.ids,
#             'model': self._name,
#
#             'form': {
#                 'from_no': self.from_no,
#                 'to_no': self.to_no,
#                 'date': self.date,
#                 'date_start': self.date_from,
#                 'date_end': self.date_to,
#                 'department_id': self.department_id.id,
#
#             },
#
#         }
#
#
#         return self.env.ref('hr_report_ksa.recap_end_of_service_report').report_action(self, data=data)
#
#

