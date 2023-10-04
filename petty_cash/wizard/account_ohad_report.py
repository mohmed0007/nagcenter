from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

class AccountohadCash(models.TransientModel):
  _name = 'account.ohad.cash.wizard'

  date_from = fields.Datetime(string='From')
  date_to = fields.Datetime(string='To')
  employee_id =fields.Many2one('res.partner', string='Employee')
     #   department_id = fields.Many2one('hr.department', string='Department')
    #   @api.multi
  def get_report(self):  
    data = {
          'ids': self.ids,
          'model': self._name,
          'form': {
              'date_from': self.date_from,
              'date_to': self.date_to,
              'employee_id': self.employee_id.name,
            #   'department_id': self.department_id.name
          },
      }
    # print(data['form']['department_id'])

    return self.env.ref('petty_cash.report_ohad_cash_open').report_action(self,data=data)


class AccountOhadPettyAbs(models.AbstractModel):
  _name = 'report.financial_dependents.petty_ohad_report_template'

  @api.model
  def _get_report_values(self, docids, data=None):
    date_from = data['form']['date_from']
    date_to = data['form']['date_to']
    employee_id = data['form']['employee_id']
    # department_id = data['form']['department_id']
    if date_from and date_to:
      docs = self.env['financial.dependents'].search([('dep_date','>=',date_from),('dep_date','<=',date_to)])
    # if date_from and date_to and department_id:
    #   docs = self.env['account.petty.cash'].search([('date','>=',date_from),('date','<=',date_to),('department_id','in',department_id)])
    if date_from and date_to and employee_id:
      docs = self.env['financial.dependents'].search([('dep_date','>=',date_from),('dep_date','<=',date_to),('emp_partner_id','in',employee_id)]) 
    # elif date_from and date_to and employee_id and department_id:
    #   docs = self.env['account.petty.cash'].search([('date','>=',date_from),('date','<=',date_to),('employee_id','in',employee_id),('department_id','in',department_id)]) 

    return{
       'doc_model':'financial.dependents',
       'date_from':date_from ,
       'date_to': date_to,
       'docs': docs
    }