from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning
from datetime import date, datetime
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools import date_utils
import json
import datetime
import pytz
import io
from dateutil.relativedelta import relativedelta
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

# from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

class EOS(models.TransientModel):
    _name = "report.eos.wizard"
    _description = "End Of Service Report"

    
   
    department_id = fields.Many2one('hr.department',string='Department')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date()
    # emp_rel = fields.Many2one('hr.employee', string='Employee')


    def print_project_report_xls(self):


        employee = self.env['hr.employee'].search([])
        emp_list = []
        for emp in employee:
            days = 0
            month = 0 
            year = 0
            today = date.today()
            if emp.contract_id and emp.contract_id.date_start:
                # print("LLLLLLLLLLLLLLLLLLLLLLLLLLLL",emp.contract_id.date_end)
                # if emp.contract_id.date_end < today:
                    diff = relativedelta(self.date, emp.contract_id.date_start)
                    paid = self.env['hr.eos.pay'].search([('employee_id','=',emp.id)])
                    total_paid = 0
                    for p in paid :
                        print("****<<<<<<<<<<<<<<<<<",p)
                        total_paid = total_paid + p.amount

                    if diff.years > 2:
                        print("*****************",diff)
                        total_amount_2_5 = 0
                        total_amount_after_5 = 0
                        total_amount_after_10 = 0
                        if diff.years >= 2 and diff.years <=5:
                            total_amount = emp.contract_id.wage * 33/100 * diff.years 
                        if  diff.years > 5 and diff.years <=10:
                            total_amount_2_5 = emp.contract_id.wage * 33/100 * 3
                            total_amount_after_5  = emp.contract_id.wage * 66/100 * (diff.years - 5)
                        if  diff.years > 10 :
                            total_amount_2_5 = emp.contract_id.wage * 33/100 * 3
                            total_amount_after_5  = emp.contract_id.wage * 66/100 * 5
                            total_amount_after_10  = emp.contract_id.wage  * (diff.years  - 10)              
                        d= {
                        'name':emp.name,
                        'code':'',
                        'join_date':emp.contract_id.date_start ,
                        'report_date':today,
                        'period': str(diff.years) + " years and " + str(diff.month) + " month and " + str(diff.days) + " days" ,
                        '2_5': total_amount_2_5,
                        "more_5": total_amount_after_5,
                        "more_10":total_amount_after_10,
                        'amount' : total_amount_2_5 + total_amount_after_5 + total_amount_after_10,
                        'paid': total_paid,
                        'balance':((total_amount_2_5 + total_amount_after_5 + total_amount_after_10) - total_paid)
                        
                        }
                        emp_list.append(d)

        data = {'list':emp_list}


        
        # data = {
        #     'department': self.department_id,
        #     # 'model': self._name,
        #     # 'record': record.id,
        # }
        return self.env.ref('hr_report.report_xls').report_action(self, data=data)



class EOS(models.TransientModel):
    _name = "report.eos.wizard.2"
    _description = "End Of Service Report"

    
   
    department_id = fields.Many2one('hr.department',string='Department')
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date()
    # emp_rel = fields.Many2one('hr.employee', string='Employee')


    def print_project_report_xls(self):


        employee = self.env['hr.employee'].search([])
        emp_list = []
        for emp in employee:
            days = 0
            month = 0 
            year = 0
            today = date.today()
            if emp.contract_id and emp.contract_id.date_start:
                # print("LLLLLLLLLLLLLLLLLLLLLLLLLLLL",emp.contract_id.date_end)
                # if emp.contract_id.date_end < today:
                    diff = relativedelta(self.date, emp.contract_id.date_start)
                    paid = self.env['hr.eos.pay'].search([('employee_id','=',emp.id)])
                    total_paid = 0
                    for p in paid :
                        print("****<<<<<<<<<<<<<<<<<",p)
                        total_paid = total_paid + p.amount

                    if diff.years > 2:
                        print("*****************",diff)
                        total_amount_2_5 = 0
                        total_amount_after_5 = 0
                        total_amount_after_10 = 0
                        if diff.years >= 2 and diff.years <=5:
                            total_amount = emp.contract_id.wage * 33/100 * diff.years 
                        if  diff.years > 5 and diff.years <=10:
                            # total_amount_2_5 = emp.contract_id.wage * 33/100 * 3
                            total_amount_after_5  = emp.contract_id.wage * 66/100 * diff.years 
                        if  diff.years > 10 :
                            # total_amount_2_5 = emp.contract_id.wage * 33/100 * 3
                            # total_amount_after_5  = emp.contract_id.wage * 66/100 * 5
                            total_amount_after_10  = emp.contract_id.wage  * diff.years            
                        d= {
                        'name':emp.name,
                        'code':'',
                        'join_date':emp.contract_id.date_start ,
                        'report_date':today,
                        'period': str(diff.years) + " years and " + str(diff.month) + " month and " + str(diff.days) + " days" ,
                        '2_5': total_amount_2_5,
                        "more_5": total_amount_after_5,
                        "more_10":total_amount_after_10,
                        'amount' : total_amount_2_5 + total_amount_after_5 + total_amount_after_10,
                        'paid': total_paid,
                        'balance':((total_amount_2_5 + total_amount_after_5 + total_amount_after_10) - total_paid)
                        
                        }
                        emp_list.append(d)

        data = {'list':emp_list}


        
        # data = {
        #     'department': self.department_id,
        #     # 'model': self._name,
        #     # 'record': record.id,
        # }
        return self.env.ref('hr_report.report2_xls').report_action(self, data=data)


    