
from datetime import datetime

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


# from datetime import date, datetime, timedelta
# from dateutil.relativedelta import relativedelta

class account_report_wizard(models.TransientModel):
    _name = "account.report.wizard"

    _description = "Report For account Wizard"

    @api.model
    def _get_default_ohad_conf_dep_account_1(self):
        param_obj = self.env['ir.config_parameter'].sudo()
        return int(param_obj.get_param('conf_dep_account_1')) or False
    date_from = fields.Date("From")
    date_to = fields.Date("To")
    enable_filter = fields.Boolean(string='Enable Comparison')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    # sett_account = fields.Many2one('res.config.settings', string='account')
    partner_ids = fields.Many2many('res.partner', string="Partner", requird=True,
                                   default=lambda self: self.env['res.partner'].search([('active', '=', True)]))

    label_filter = fields.Char(string='Column Label',
                               help="This label will be displayed on report to show the balance computed for the given comparison filter.")
    filter_cmp = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], string='Filter by',
                                  required=True, default='filter_no')
    date_from_cmp = fields.Date(string='Start Date')
    date_to_cmp = fields.Date(string='End Date')
    account_id = fields.Many2one('account.account', string="Account",readonly=1,default=_get_default_ohad_conf_dep_account_1,domain="[('company_id', '=', company_id)]")
    partner_id = fields.Many2one('res.partner', string="Partner")
    # dep_dibet_account = fields.Many2one('account.account', string='Debit Account',readonly=1,default=_get_default_conf_dep_account_1,domain="[('company_id', '=', company_id)]")

    
    
    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,
            'account_id': self.account_id.id,
            'account_code': self.account_id.code,
            'account_name': self.account_id.name,
            'partner_ids': self.partner_ids.ids,
            'partner_id' : self.partner_id.id,
            'date_start': self.date_from,
            'date_end': self.date_to,

        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `_get_report_values()` and pass `data` automatically.
        return self.env.ref('petty_cash.ohad_all_report').report_action(self, data=data)



class ReportAccountingOhad(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.petty_cash.accounting_ohad_all_report_view'

    @api.model
    def _get_report_values(self, docids, data):
        print("AQP" * 14, type(data['account_id']))
        date_start = data['date_start']
        date_end = data['date_end']
        x = data['account_id']
        code = data['account_code']
        name = data['account_name']
        partner_ids = data['partner_ids']
        partner_id = data['partner_id']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        date_diff = (date_end_obj - date_start_obj).days + 1

        docs = []
        print(partner_ids)

        # line_ids = self.env['account.move.line'].search([
        #     ('parent_state', '=', 'posted'), ('account_id', '=', x)])

        # print("QQ" * 12, line_ids.partner_id)
        partner_ids_loop = self.env['res.partner'].search([('id', '=', partner_id), ('active', '=', True)]) if partner_id else self.env['res.partner'].search([('id', 'in', partner_ids), ('active', '=', True)])

        for partner in partner_ids_loop:
            # print(type(partner))
            # return
            line_ids = self.env['account.move.line'].search([
                ('parent_state', '=', 'posted'), ('partner_id', '=', partner.id), ('account_id', '=', x)])
            if line_ids:
                amount_debit = 0.0
                amount_credit = 0.0
                amount_debit_full = 0.0
                amount_credit_full = 0.0
                amount_debit_open = 0.0
                amount_credit_open = 0.0
                for rec in self.env['account.move.line'].search([
                    ('parent_state', '=', 'posted'), ('partner_id', '=', partner.id), ('account_id', '=', x)]):
                    print("Faw" * 10, rec.account_id)
                    amount_debit_full += rec.debit
                    amount_credit_full += rec.credit
                if amount_debit_full > amount_credit_full :
                   amount_debit_full = abs(amount_debit_full - amount_credit_full)
                   amount_credit_full = 0
                elif amount_debit_full < amount_credit_full :
                    amount_credit_full = abs(amount_credit_full - amount_debit_full)
                    amount_debit_full = 0
                else:
                    amount_credit_open = 0
                    amount_debit_open = 0
                for record in self.env['account.move.line'].search([
                    ('parent_state', '=', 'posted'), ('partner_id', '=', partner.id),
                    ('date', '>=', data['date_start']), ('date', '<', data['date_end']), ('account_id', '=', x)]):
                    amount_debit += record.debit
                    print(record.debit,record.date,record.partner_id.name)
                    amount_credit += record.credit
                    print(record.credit,record.date,record.partner_id.name)
                print(amount_debit,amount_credit)
                for record1 in self.env['account.move.line'].search([
                    ('parent_state', '=', 'posted'), ('partner_id', '=', partner.id),
                    ('date', '<=', data['date_start']), ('account_id', '=', x)]):
                    amount_debit_open += record1.debit
                    amount_credit_open += record1.credit
                if amount_debit_open > amount_credit_open :
                   amount_debit_open = abs(amount_debit_open - amount_credit_open)
                   amount_credit_open = 0
                elif amount_debit_open <  amount_credit_open :
                    amount_credit_open = abs(amount_credit_open - amount_debit_open)
                    amount_debit_open = 0
                else:
                    amount_credit_open = 0
                    amount_debit_open = 0

                docs.append({
                    'account_name': name,
                    'account_code': code,
                    'partner': partner.name,
                    'debit': amount_debit,
                    'credit': amount_credit,
                    'debitstart': amount_debit_open,
                    'creditstart': amount_credit_open,
                    'debitcurr': amount_debit_full,
                    'creditcurr': amount_credit_full,

                })
        # print("Faw" * 10, docs)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'account_name': name,
             'account_code': code,
            # 'account_id': x,
            'docs': docs,
        }


