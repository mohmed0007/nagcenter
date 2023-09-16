from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning
from datetime import date, datetime
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


# from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

class LoanReportWizard(models.TransientModel):
    _name = "loan.report.wizard"

    _description = "Loan Report Wizard"

    date_from = fields.Date("From")
    date_to = fields.Date("To")
    date = fields.Date(string='Date',default= datetime.now())
    department_id = fields.Many2one('hr.department',string='Department')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    emp_rel = fields.Many2one('hr.employee', string='Employee')


    def get_report1(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,

            'form': {
                'date': self.date,
                'date_start': self.date_from,
                'date_end': self.date_to,
                'department_id': self.department_id.id,
                'company' : self.company.id,
                'company_name' : self.company.name,
                'emp_rel' : self.emp_rel.id,
            },
        }


        return self.env.ref('hr_report_ksa.recap_loan_report').report_action(self, data=data)



class ReportLoan(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.hr_report_ksa.recap_loan_report_view'

    def _get_report_values(self, docids, data=None):

        docs = []
        department_id = data['form']['department_id']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        company = data['form']['company']
        company_name = data['form']['company_name']
        emp_rel = data['form']['emp_rel']


        department_name = ''
        if emp_rel:
            loan_ids = self.env['hr.loan'].search([('state', '=','approve'),('employee_id.id','=' ,emp_rel)], order='date asc')
            
        elif company:
            loan_ids = self.env['hr.loan'].search([('state', '=','approve')], order='date asc')
        #    print(loan_ids.name)

        else:
            loan_ids = self.env['hr.loan'].search([('state', '=', 'approve'), ('company_id.id', '=', company)],
                                                  order='date asc')

        if department_id or date_start or date_end:
            print(date_start, loan_ids)
            if date_start and date_end :
               date_time_start = datetime.strptime(date_start, '%Y-%m-%d')
               date_time_end = datetime.strptime(date_end, '%Y-%m-%d')

               loan_ids = loan_ids.filtered(lambda x: x.date >= date_time_start.date() <= date_time_end.date())
            # employees = self.env['hr.employee'].search([('department_id', '=', department_id)],
            #                                            order='registration_number asc')
        if department_id:
            loan_ids = loan_ids.filtered(lambda x: x.department_id.id == department_id)
            department_name = self.env['hr.department'].search([('id', '=', department_id)], order='name asc').name
            # employees.filtered(lambda x: x.department_id.id == department_id or )
        # else:
        #     employees = self.env['hr.employee'].search([], order='registration_number asc')
        print(loan_ids, "employ")
        for loan in loan_ids:
            # if emp.contract_id.state == 'open':
            register = loan.employee_id.registration_number
            emp_name = loan.employee_id.name
            department = loan.employee_id.department_id.name
            date = loan.date
            loan_total_amount = loan.total_amount
            installment_no = loan.installment
            installment_amount = loan_total_amount / installment_no
            loan_line = self.env['hr.loan.line'].search([('loan_id', '=', loan.id)], order='date asc',limit=1)
            loan_line = loan_line.filtered(lambda x: x.paid != False)
            month = loan_line.date.month if loan_line else '-'
            year = loan_line.date.year if loan_line else '-'
            amount = loan_line.amount if loan_line else 0
            total_paid = loan.total_paid_amount
            total_remain = loan.balance_amount


            docs.append({
                'register': register,
                'emp_name': emp_name,
                'department': department,
                'date': date,
                'loan_total_amount': loan_total_amount,
                'installment_no': installment_no,
                'installment_amount': installment_amount,
                'month': month,
                'year': year,
                'amount': amount,
                'total_paid': total_paid,
                'total_remain': total_remain,

            })
            # for rec in docs:
            #     print("line" * 10, rec)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            # 'date_start': date_start,
            'date': data['form']['date'],
            'department_name': department_name,
            'company_name' : company_name ,
            'docs': docs,

        }