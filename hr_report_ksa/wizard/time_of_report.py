from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning
from datetime import date, datetime
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


# from datetime import date, datetime, timedelta
# from dateutil.relativedelta import relativedelta


class ReportTimeOF(models.TransientModel):
    _name = "report.approval.wizard"

    _description = "Employees Time Of Report Wizard"

    date_from = fields.Date("From", default= datetime.now().date())
    date_to = fields.Date("To", default= datetime.now().replace(month=12,))
    date = fields.Date(string='Date', default= datetime.now())
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    category_id = fields.Many2one('approval.category', string='Approval Type', required=True)
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
                'category_id': self.category_id.id,
                'company' : self.company.id
                

            },
        }


        return self.env.ref('hr_report_ksa.approval_report').report_action(self, data=data)





class ReportApprovalRecap(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.employees_approval_report_view'

    def _get_report_values(self, docids, data=None):

        docs = []
        department_id = data['form']['department_id']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        category_id = data['form']['category_id']
        company = data['form']['company']

        department_name = ''
        if company :
          employees = self.env['hr.employee'].search([('joining_date', '!=', False),('company_id','=',company)], order='registration_number')
        else:
            employees = self.env['hr.employee'].search([('joining_date', '!=', False)],order='registration_number')

        approval_record = self.env['approval.request'].search([('request_status', '=', 'approved')], order='registration_number')
        category_name = self.env['approval.category'].search([('id', '=', category_id)]).name
        if date_start and date_end:
            print(date_start, employees, approval_record)
            date_time_start = datetime.strptime(date_start, '%Y-%m-%d')
            date_time_end = datetime.strptime(date_end, '%Y-%m-%d')
            # employees = employees.filtered(lambda x: x.joining_date >= date_time_start.date() and x.joining_date <= date_time_end.date())
            approval_record = approval_record.filtered(
                lambda x: x.date >= date_time_start.date()
                          and x.date <= date_time_end.date())

        if from_no and to_no:
            approval_record = approval_record.filtered(
                lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))

        if department_id:
            approval_record = approval_record.filtered(lambda x: x.department_id.id == department_id)
            department_name = self.env['hr.department'].search([('id', '=', department_id)], order='name asc').name
        arabian = 0
        non_arabian = 0
        print(employees, approval_record, "employ")
        for approve in approval_record:
            print(approve.registration_number)
            register = approve.registration_number
            emp_name = approve.request_owner_id.name
            department = approve.department_id.name
            data_start1 = approve.date_start
            date_end1 = approve.date_end
            date = approve.date
            state = approve.request_status

            docs.append({
                'register': register,
                'emp_name': emp_name,
                'department': department,
                'data_start1': data_start1,
                'date_end1': date_end1,
                'date_start': date_start,
                'date_end': date_end,
                'date': date,
                'state': state,

            })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date': data['form']['date'],
            'department_name': department_name,
            'docs': docs,
            'from_no': from_no,
            'to_no': to_no,
            'date_start': date_start,
            'date_end': date_end,
            'category_name':category_name

        }







class ReportTimeOF(models.TransientModel):
    _name = "report.leave.wizard"

    _description = "Employees Time Of Report Wizard"

    date_from = fields.Date("From", )
    date_to = fields.Date("To", )
    date = fields.Date(string='Until date', )
    from_no = fields.Char(string='From Employee No')
    to_no = fields.Char(string='To Employee No')
    department_id = fields.Many2one('hr.department',string='Department')
    leave_type = fields.Many2one('hr.leave.type', string='Leave type',required=True)
    company = fields.Many2one('res.company', string='Company',default=lambda self: self.env.company.id)
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
                'leave_type':self.leave_type.id,
                'company' : self.company.id,
                'emp_rel' : self.emp_rel.name,
            },
        }


        return self.env.ref('hr_report_ksa.leave_report').report_action(self, data=data)




class ReportleaveRecap(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.employees_leave_report_view'




    def _get_remaining_leaves(self, data=None):
        """ Helper to compute the remaining leaves for the current employees
            :returns dict where the key is the employee id, and the value is the remain leaves
        """
        employees = self.env['hr.employee'].search([], order='name asc')
        print(employees)
        leave_type = data['form']['leave_type']
        print(leave_type,'leave_type'*10)
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
                (s.requires_allocation='yes' ) AND
                h.employee_id in %s AND h.holiday_status_id = %s
            GROUP BY h.employee_id""", (tuple(employees.ids),4))
        return dict((row['employee_id'], row['days']) for row in self._cr.dictfetchall())


    def _get_report_values(self, docids, data=None):
        docs = []


        department_id = data['form']['department_id']
        from_no = data['form']['from_no']
        to_no = data['form']['to_no']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        leave_type = data['form']['leave_type']
        company = data['form']['company']
        emp_rel = data['form']['emp_rel']
        if emp_rel:
            employees_re = self.env['hr.employee'].search([('name','=',emp_rel)], order='name asc')
        elif company :
           employees_re = self.env['hr.employee'].search([('company_id','=',company)], order='name asc')
        elif company and emp_rel:
           employees_re = self.env['hr.employee'].search([('company_id','=',company),('name','=',emp_rel)], order='name asc')
        else:
            employees_re = self.env['hr.employee'].search([], order='name asc')
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
                        (s.requires_allocation='yes') AND
                        h.employee_id in %s AND h.holiday_status_id = %s
                    GROUP BY h.employee_id""", (tuple(employees_re.ids), leave_type))
        remaining = dict((row['employee_id'], row['days']) for row in self._cr.dictfetchall())
        # remaining = self._get_remaining_leaves()
        print(remaining, data['form']['date'])
        department_name = ''
        if emp_rel:
            employees = self.env['hr.employee'].search([('name','=',emp_rel)], order='registration_number')
        elif emp_rel and company:
            employees = self.env['hr.employee'].search([('company_id','=',company),('name','=',emp_rel)], order='registration_number')
        elif company:
           employees = self.env['hr.employee'].search([('company_id','=',company)], order='registration_number')
        else:
            employees = self.env['hr.employee'].search([], order='registration_number')

        hr_leave_type = self.env['hr.leave.type'].search([('id', '=', leave_type)], order='name asc').name
        if department_id:
            if company :
               department_name = self.env['hr.department'].search([('id', '=', department_id),('company_id','=',company)], order='name asc').name
            else:
                department_name = self.env['hr.department'].search(
                    [('id', '=', department_id)], order='name asc').name


        if department_id :
            if emp_rel:
                employees = self.env['hr.employee'].search([('department_id','=',department_id),('company_id','=',company),('name','=',emp_rel)], order='registration_number')
            if company:
               employees = self.env['hr.employee'].search([('department_id','=',department_id),('company_id','=',company)], order='registration_number')
            else:
                employees = self.env['hr.employee'].search(
                    [('department_id', '=', department_id)], order='registration_number')



        if from_no and to_no:
            employees = employees.filtered(
                lambda x: int(x.registration_number) >= int(from_no) and int(x.registration_number) <= int(to_no))



        department_id = self.env['hr.department'].search([('id', '=', department_id)], order='name asc')
        alldata = self.env['hr.leave.allocation'].read_group([
            ('employee_id', 'in', employees.ids),
            ('holiday_status_id.active', '=', True),
            ('holiday_status_id', '=', leave_type),
            ('state', '=', 'validate'),
        ], ['number_of_days:sum', 'employee_id'], ['employee_id'])

        alldata1 = self.env['hr.leave'].read_group([
            ('employee_id', 'in', employees.ids),
            ('holiday_status_id.active', '=', True),
            ('holiday_status_id', '=', leave_type),
            ('state', '=', 'validate'),
        ], ['number_of_days:sum', 'employee_id'], ['employee_id'])

        rg_results = dict((d['employee_id'][0], d['number_of_days']) for d in alldata)
        rg_results1 = dict((d['employee_id'][0], d['number_of_days']) for d in alldata1)
        print(alldata)
        for emp in employees:
            if emp.contract_id.state == 'open':
                register = emp.registration_number
                emp_name = emp.name
                country = emp.country_id.name
                job_id = emp.job_id
                first_contract_date = emp.first_contract_date
                allocation_leave_total = rg_results.get(emp.id, 0.0)
                time_of_leave_total = rg_results1.get(emp.id, 0.0)
                remain = 0.0
                for key in remaining.keys():
                    print(key)
                    if key == emp.id:
                       remain = remaining[key]
                       print(remain,'remain'*10)

                docs.append({
                    'register': register,
                    'emp_name': emp_name,
                    'nationality': country,
                    'department_id': emp.department_id.name,
                    'job_id': job_id.name,
                    'first_contract_date': first_contract_date,
                    'allocation_leave_total' : allocation_leave_total,
                    'time_of_leave_total': time_of_leave_total,
                    'remain': remain,

                })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'from_no': from_no,
            'to_no' : to_no,
            'date_start': date_start,
            'date_end':date_end,
            'date' : data['form']['date'],
            'department_name': department_name,
            'hr_leave_type':hr_leave_type,
            'docs': docs,

        }

