# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import fields, models, api, _
from io import BytesIO
import xlsxwriter
import base64
import io
from io import BytesIO
from PIL import Image


class WPSReport(models.TransientModel):
    _name = "wps.report"
    _description = "WPS Report"

    filename = fields.Char(string='File Name', size=64)
    excel_file = fields.Binary(string='Excel File')
    file_path = fields.Char('File Path', default=r"\\10.10.10.235\\finance\رواتب مجموعة النفيعى للاستثمار\BSF PAYROLL")
    value_date = fields.Date('Value Date', default=fields.Date.today())
    payment_details = fields.Char('Payment Details', default="Salary")

    def print_reports(self):
        values = {}
        report = self
        filename = 'WPSReport.xlsx'
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('WPS Report')
        head_dict = {
            'bold': 0,'border': 0,'bottom': 0,
            'top': 0,'left': 0,'right': 0,
            'font_size': 8,'num_format': '#,##0.00',
            'font_name': 'Arial',
            'align': 'center',
        }
        head_section = workbook.add_format(head_dict)
        head_section_right = workbook.add_format({'border': 0, 'align': 'right', 'font_size': 8,'font_name': 'Arial'})
        head_section_center = workbook.add_format(head_dict)
        detail_head = workbook.add_format({
            'bold': 1,'border': 1,
            'align': 'center','valign': 'vcenter',
            'font_size': 10,
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
            'bg_color': '#25a3cc','font_color': '#0c476b',
            'text_wrap': True,
        })
        details_format = workbook.add_format({
            'font_size': 10, 'border': 1, 'num_format': '#,##0.00', 
            'font_name': 'Arial', 'align': 'center','text_wrap': True
        })
        merge_format = workbook.add_format({
            'bold': 0,'border': 0,
            'align': 'center','valign': 'vcenter',
            'font_name': 'Arial','font_size': 8,
        })
        head_format = workbook.add_format({
            'bold': 0,'border': 1,
            'align': 'left','font_size': 8,
            'num_format': '#,##0.00',
        })
        head_format_center = workbook.add_format({
            'bold': 0,'border': 1,
            'align': 'center','font_size': 8,
        })
        batch_id = False
        if self._context.get('active_id'):
            batch_id = self.env['hr.payslip.run'].search([('id', '=', self._context.get('active_id'))])
            employees = batch_id.slip_ids.filtered(lambda l: l.state in ['done', 'verify'])

        for i in range(0, 22):
            worksheet.set_row(i, 10, head_section)
        worksheet.merge_range('A1:M9', '', merge_format)
        if self.env.user.company_id.payroll_logo:
            im = Image.open(io.BytesIO(base64.b64decode(self.env.user.company_id.payroll_logo))).convert("RGB")
            im.save('/tmp/image.jpg', quality=180)
            worksheet.insert_image('B2:K8', '/tmp/image.jpg', {'x_scale': 0.9, 'y_scale': 1.1, 'x_offset': 20})

        worksheet.write(11, 1, 'Company Name', head_section_right)
        worksheet.merge_range('C12:E12', 'ALNEFAIE INVESTMENT GROUP CO', head_format)
        worksheet.write(12, 5, 'Payroll Code', head_section_center)
        worksheet.write(12, 6, '200507', head_format_center)
        
        worksheet.write(13, 1, 'Account Number', head_section_right)
        worksheet.write(13, 2, '98609900173', head_format)
        worksheet.write(13, 5, 'Company MOL Number', head_section_center)
        worksheet.write(13, 6, '9-117350', head_format_center)
        
        worksheet.write(15, 1, '(‫رقم بدايه السطر‬) Start Row :', head_section_right)
        worksheet.write(15, 2, '25', head_format)
        worksheet.write(15, 4, 'Value Date', head_section_center)
        worksheet.write(15, 5, self.value_date and self.value_date.strftime('%Y%m%d') or '', head_format_center)
        worksheet.write(15, 6, 'YYYYMMDD', merge_format)
        
        worksheet.write(23, 0, 'Emp. ID. No.', detail_head)
        worksheet.write(23, 1, 'Employee Name', detail_head)
        worksheet.write(23, 2, 'Emp. Bank Code', detail_head)
        worksheet.write(23, 3, 'Emp. Acc. No.', detail_head)
        worksheet.write(23, 4, 'Salary Amount', detail_head)
        worksheet.write(23, 5, 'Basic Salary', detail_head)
        worksheet.write(23, 6, 'Housing Allowance', detail_head)
        worksheet.write(23, 7, 'Other Earnings', detail_head)
        worksheet.write(23, 8, 'Deduction', detail_head)
        worksheet.write(23, 9, 'Payment Description', detail_head)
        worksheet.write(23, 10, 'Employee Address1', detail_head)
        worksheet.write(23, 11, 'Employee Address2', detail_head)
        worksheet.write(23, 12, 'Employee Address3', detail_head)
        
        first_row = 24
        
        all_col_dict = {'nid': 0, 'employee_name': 1, 'employee_bank': 2, 'employee_acc': 3, 'net': 4, 
        'basic': 5, 'housing': 6, 'others': 7, 'deduction': 8, 'payment_desc': 9, 'emp_add_1': 10, 'emp_add_2': 11, 'emp_add_3': 12}
        
        worksheet.set_row(23, 30)
        worksheet.set_column(0, 0, 8)
        worksheet.set_column(1, 1, 25)
        worksheet.set_column(2, 2, 9)
        worksheet.set_column(3, 3, 21)
        worksheet.set_column(4, 4, 7)
        worksheet.set_column(5, 5, 12)
        worksheet.set_column(6, 7, 8)
        worksheet.set_column(8, 8, 6)
        worksheet.set_column(9, 9, 8)
        worksheet.set_column(10, 14, 15)
        actual_data_row = 24
        no_of_entry = 0
        net_total = 0.0
        payment_detail = self.payment_details or ''
        for slip in employees:
            total_deduction = []
            total_others = []
            deduction_ids = slip.line_ids.filtered(lambda l: l.category_id.code == 'DED' or l.category_id.parent_id.code == 'DED')
            for deduction in deduction_ids:
                total_deduction.append(abs(deduction.total))
            others_allowance = sum(slip.line_ids.filtered(lambda l: l.category_id.code == 'ALW' or l.category_id.parent_id.code == 'ALW').mapped('total'))
            if slip.line_ids.filtered(lambda l: l.code == 'HRA'):
                others_allowance = others_allowance - slip.line_ids.filtered(lambda l: l.code == 'HRA').mapped('total')[0]
            address = slip.employee_id.address_home_id.city or '' if slip.employee_id.address_home_id else ''
            net = slip.line_ids.filtered(lambda l: l.code == 'NET').total or 0.0
            net_total += net
            values.update({
                'employee_name': slip.employee_id.name or '',
                'employee_bank': slip.employee_id.bank_account_id.bank_id.name if slip.employee_id.bank_account_id.bank_id else '',
                'employee_acc': slip.employee_id.bank_account_id.acc_number or '' ,
                'net': net,
                'basic': slip.line_ids.filtered(lambda l: l.code == 'BASIC').total or '',
                'housing': slip.line_ids.filtered(lambda l: l.code == 'HRA').total or '',
                'others': others_allowance,
                'deduction': sum(total_deduction),
                'payment_desc': payment_detail,
                'emp_add_1': address,
                'emp_add_2': address,
                'emp_add_3': address,
                'nid': slip.employee_id.identification_id or '',
            })
            for line_dict in values:
                worksheet.write(actual_data_row, all_col_dict[line_dict], values[line_dict], details_format)
            no_of_entry += 1 
            actual_data_row += 1

        worksheet.write(17, 1, '(‫عدد الموظفين‬) Number of Entries :', head_section_right)
        worksheet.write(17, 2, str(no_of_entry), head_format)
        worksheet.write(17, 4, '(‫مكان حفظ الملف‬) File Path :', head_section_right)
        worksheet.merge_range('F18:H18', self.file_path or '', head_format)

        worksheet.write(19, 1, 'Total Salary', head_section_right)
        worksheet.write(19, 2, net_total, head_format_center)

        workbook.close()
        report.write({'excel_file': base64.encodebytes(fp.getvalue()), 'filename': filename})
        fp.close()

        return self.return_wiz_action(report.id)

    def return_wiz_action(self, res_id, context=None):
        return {
            'name': 'WPS Report',
            'view_mode': 'form',
            'res_id': res_id,
            'res_model': 'wps.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
        }
