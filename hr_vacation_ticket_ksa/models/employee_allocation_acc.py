import time
from odoo import models, api, fields
from odoo.exceptions import UserError
from datetime import datetime, date
from odoo.exceptions import Warning, UserError
# from dateutil import relativedelta
from dateutil.relativedelta import relativedelta

class HrEmployee(models.Model):
    _inherit = 'hr.department'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",required=True, help='Select corresponding analytic account')

    # def write(self, val):
    #     print(val)
    #     super(HrEmployee, self).write(val)


class HrContractAcc(models.TransientModel):
    """
        Employee contract based on the visa, work permits
        allows to configure different Ticket Price
        """
    _name = 'hr.account.sync'

    date = fields.Date(string="Date")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)
    configuration_id = fields.Many2one('hr.allocation.accounting.configuration' , string='Configuration' , required=True)

    @api.onchange('date')
    def get_late_entitlement_date(self):
        for rec in self :
            print("Osman"*5)
            move_object = self.env['account.move'].search([('is_entitlements', '=', True)])
            dates = []  # Declaring empty array
            for line in move_object :
                if line.date:  # if the date is set
                    dates.append(line.date)  # Add it to the array
            if dates :
               max_date = max(dates)
               rec.last_entitlement = max_date
        # if max_date :
        #    # print(move_object.date,"OIO"*3)
        #    rec.last_entitlement = max_date



    last_entitlement = fields.Date(string="Last Entitlement Date",store=True)





    @api.model
    def _get_employee_service_year(self, recor_class):
        timenow = time.strftime('%Y-%m-%d')

        date_time_obj = datetime.strptime(timenow, '%Y-%m-%d')
        date1 = date_time_obj
        date2 = recor_class.first_contract_date
        print(type(date1), type(date2))
        time_difference = relativedelta(date1, date2)
        difference_in_years = time_difference.years
        return difference_in_years

    def employee_allocation(self):
        """This create account move for employee ticket , leave , end of service allocation.
            """
        leave_allocation_acc = self.configuration_id.leave_allocation_acc_id.id
        # leave_allocation_acc = self.env['account.account'].sudo().search([('id', '=', leave_allocation_acc)])
        # print(leave_allocation_acc.sub_code)
        # leave_allocation_acc = self.env['account.account'].sudo().search([('sub_code', '=', leave_allocation_acc.sub_code),('company_id', '=', self.company_id.id),('company_id', '=', self.company_id.id)])
        print(leave_allocation_acc)
        leave_expenses_acc = self.configuration_id.leave_expenses_acc_id.id
        # leave_expenses_acc = self.env['account.account'].sudo().search([('id', '=', leave_expenses_acc)])
        # leave_expenses_acc = self.env['account.account'].sudo().search([('sub_code', '=', leave_expenses_acc.sub_code),('company_id', '=', self.company_id.id)])
        ticket_allocation_acc = self.configuration_id.ticket_allocation_acc_id.id
        # ticket_allocation_acc = self.env['account.account'].sudo().search([('id', '=', int(ticket_allocation_acc))])
        # ticket_allocation_acc = self.env['account.account'].sudo().search([('sub_code', '=', ticket_allocation_acc.sub_code),('company_id', '=', self.company_id.id)])
        ticket_expenses_acc = self.configuration_id.ticket_expenses_acc_id.id
        # ticket_expenses_acc = self.env['account.account'].sudo().search([('id', '=', int(ticket_expenses_acc))])
        # ticket_expenses_acc = self.env['account.account'].sudo().search([('sub_code', '=', ticket_expenses_acc.sub_code),('company_id', '=', self.company_id.id)])
        end_service_allocation_acc = self.configuration_id.end_service_allocation_acc_id.id
        # end_service_allocation_acc = self.env['account.account'].sudo().search(
        #     [('id', '=', int(end_service_allocation_acc))])
        # end_service_allocation_acc = self.env['account.account'].sudo().search([('sub_code', '=', end_service_allocation_acc.sub_code),('company_id', '=', self.company_id.id)])
        end_service_expenses_acc = self.configuration_id.end_service_expenses_acc_id.id
        # end_service_expenses_acc = self.env['account.account'].sudo().search(
        #     [('id', '=', int(end_service_expenses_acc))])
        # end_service_expenses_acc = self.env['account.account'].sudo().search(
        #     [('sub_code', '=', end_service_expenses_acc.sub_code),('company_id', '=', self.company_id.id)])
        gosi_allocation_acc = self.configuration_id.gosi_allocation_acc_id.id
        # gosi_allocation_acc = self.env['account.account'].sudo().search(
        #     [('id', '=', int(gosi_allocation_acc))])
        # gosi_allocation_acc = self.env['account.account'].sudo().search([('sub_code', '=', gosi_allocation_acc.sub_code),('company_id', '=', self.company_id.id)])
        gosi_expenses_acc = self.configuration_id.gosi_expenses_acc_id.id
        # gosi_expenses_acc = self.env['account.account'].sudo().search(
        #     [('id', '=', int(gosi_expenses_acc))])
        # gosi_expenses_acc = self.env['account.account'].sudo().search([('sub_code', '=', gosi_expenses_acc.sub_code),('company_id', '=', self.company_id.id)])
        journal_allocation_id = self.configuration_id.journal_id.id

        # journal_allocation_id = self.env['account.journal'].sudo().search([('id', '=', int(journal_allocation_id))])
        # journal_allocation_id = self.env['account.journal'].sudo().search([('type', '=', 'general'),('company_id', '=', self.company_id.id)] ,limit =1)
        # posted_entry = self.env['ir.config_parameter'].sudo().get_param('posted_entry')

        print(leave_allocation_acc, ticket_allocation_acc, leave_expenses_acc, end_service_allocation_acc
              , ticket_expenses_acc, end_service_expenses_acc, end_service_expenses_acc
              , journal_allocation_id, gosi_allocation_acc)
        if not leave_allocation_acc or not ticket_allocation_acc or not leave_expenses_acc or \
                not end_service_allocation_acc or not ticket_expenses_acc or not end_service_expenses_acc or \
                not journal_allocation_id or not gosi_allocation_acc or not gosi_expenses_acc:
            raise UserError("You must config account parameter in accounting setting")
        else:
            timenow = time.strftime('%Y-%m-%d')
            analytic_acc_obj = self.env['account.analytic.account'].search([])
            print("Name"*4, self.env.user.company_id.id)
            department_ids = self.env['hr.department'].sudo().search([('company_id', '=',  self.env.company.id)])
            line_ids = []
            for department in department_ids:
              print(department.name, "department" * 4)
              if department.analytic_account_id:
                print(department.analytic_account_id, "analytic_account_id" * 4)
                end_of_vals = 0
                leave_vals = 0
                ticket_vals = 0
                gois_vals = 0
                contract_obj = self.env['hr.contract'].sudo().search(
                    [('state', '=', 'open'), ('department_id', '=', department.id)])
                if not contract_obj:
                    pass
                else:
                    for contract in contract_obj:
                        # break
                        service_year = self._get_employee_service_year(contract)
                        print(service_year, "years" * 4)
                        name = contract.employee_id.name
                        debit_leave_account_id = int(leave_expenses_acc)
                        credit_leave_account_id = int(leave_allocation_acc)
                        debit_ticket_account_id = int(ticket_expenses_acc)
                        credit_ticket_account_id = int(ticket_allocation_acc)
                        debit_end_of_account_id = int(end_service_expenses_acc)
                        credit_end_of_account_id = int(end_service_allocation_acc)
                        debit_gois_account_id = int(gosi_expenses_acc)
                        credi_gois_account_id = int(gosi_allocation_acc)
                        journal_allocation_id = int(journal_allocation_id)
                        sum = (contract.wage + contract.HRA + contract.TA + contract.other_amt + contract.other_amt2)
                        if service_year >= 5:
                            end_of_vals += sum / 12
                        else:
                            end_of_vals += (sum / 2) / 12
                        print('analytic', department.analytic_account_id.name, leave_vals)
                        leave_vals += contract.monthly_leave_salary
                        ticket_vals += contract.amount_per_month
                        gois_vals += contract.deduced_company_per_month

                    debit_end_of_vals = {
                        'name': "End of Service",
                        'account_id': debit_end_of_account_id,
                        'analytic_account_id': department.analytic_account_id.id,
                        'journal_id': journal_allocation_id,
                        'date': timenow,
                        'debit': end_of_vals > 0.0 and end_of_vals or 0.0,
                        'credit': end_of_vals < 0.0 and -end_of_vals or 0.0,

                    }
                    credit_end_of_vals = {
                        'name': "End of Service",
                        'account_id': credit_end_of_account_id,
                        'analytic_account_id': department.analytic_account_id.id,
                        'journal_id': journal_allocation_id,
                        'date': timenow,
                        'debit': end_of_vals < 0.0 and -end_of_vals or 0.0,
                        'credit': end_of_vals > 0.0 and end_of_vals or 0.0,

                    }

                    debit_leave_vals = {
                        'name': "Leave",
                        'account_id': debit_leave_account_id,
                        'analytic_account_id': department.analytic_account_id.id,
                        'journal_id': journal_allocation_id,
                        'date': timenow,
                        'debit': leave_vals > 0.0 and leave_vals or 0.0,
                        'credit': leave_vals < 0.0 and -leave_vals or 0.0,
                    }
                    credit_leave_vals = {
                        'name': "Leave",
                        'account_id': credit_leave_account_id,
                        'analytic_account_id': department.analytic_account_id.id,
                        'journal_id': journal_allocation_id,
                        'date': timenow,
                        'debit': leave_vals < 0.0 and -leave_vals or 0.0,
                        'credit': leave_vals > 0.0 and leave_vals or 0.0,
                    }
                    debit_ticket_vals = {
                        'name': "Ticket",
                        'account_id': debit_ticket_account_id,
                        'analytic_account_id': department.analytic_account_id.id,
                        'journal_id': journal_allocation_id,
                        'date': timenow,
                        'debit': ticket_vals > 0.0 and ticket_vals or 0.0,
                        'credit': ticket_vals < 0.0 and - ticket_vals or 0.0,

                    }
                    credit_ticket_vals = {
                        'name': "Ticket",
                        'account_id': credit_ticket_account_id,
                        'analytic_account_id': department.analytic_account_id.id,
                        'journal_id': journal_allocation_id,
                        'date': timenow,
                        'debit': ticket_vals < 0.0 and -ticket_vals or 0.0,
                        'credit': ticket_vals > 0.0 and ticket_vals or 0.0,

                    }

                    debit_gois_vals = {
                        'name': "gosi",
                        'account_id': debit_gois_account_id,
                        'analytic_account_id': department.analytic_account_id.id,
                        'journal_id': journal_allocation_id,
                        'date': timenow,
                        'debit': gois_vals > 0.0 and gois_vals or 0.0,
                        'credit': gois_vals < 0.0 and -gois_vals or 0.0,

                    }
                    credit_gois_vals = {
                        'name': "gosi",
                        'account_id': credi_gois_account_id,
                        'analytic_account_id': department.analytic_account_id.id,
                        'journal_id': journal_allocation_id,
                        'date': timenow,
                        'debit': gois_vals < 0.0 and -gois_vals or 0.0,
                        'credit': gois_vals > 0.0 and gois_vals or 0.0,

                    }
                    line_ids.append((0, 0, debit_leave_vals))
                    line_ids.append((0, 0, credit_leave_vals))
                    line_ids.append((0, 0, debit_ticket_vals))
                    line_ids.append((0, 0, credit_ticket_vals))
                    line_ids.append((0, 0, debit_gois_vals))
                    line_ids.append((0, 0, credit_gois_vals))
                    line_ids.append((0, 0, debit_end_of_vals))
                    line_ids.append((0, 0, credit_end_of_vals))

            vals = {
                # 'name': 'مستحقات الموظفين',
                'narration': 'مستحقات الموظفين',
                'is_entitlements' : True,
                'ref': 'مستحقات الموظفين',
                'journal_id': journal_allocation_id,
                'date': self.date,
                'line_ids': line_ids

            }

            move = self.env['account.move'].create(vals)
            print(vals, )
            # print(posted_entry)
            # if posted_entry == True:
            #    pass


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_entitlements = fields.Boolean(string="Entitlements", default=False)
