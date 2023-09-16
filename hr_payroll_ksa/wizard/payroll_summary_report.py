# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import io
from io import BytesIO
import xlsxwriter
from num2words import num2words

from PIL import Image
import base64


class PayrollSummaryReport(models.TransientModel):
    _name = "payroll.summary.report"
    _description = "Payroll Summary Report"

    filename = fields.Char(string='File')
    file_name = fields.Char(string="File Name", size=64)
    excel_file = fields.Binary(string='Excel File')
    batch_ids = fields.Many2many('hr.payslip.run', string="Payroll Batches")
    status = fields.Selection([('all', 'All'), ('all_not_cancel', 'All But Not Cancel'), ('done', 'Done')], 
        string='Payslip Status', default='all')

    def print_reports(self):
        values = {}
        report = self
        filename = '%s.xlsx' % (self.file_name)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('PayslipSummaryReport')
        border_head = workbook.add_format({
            'bold': 1,
            'border': 1,
            'font_size': 10, 
            })
        merge_head = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            })
        branch_head = ({
            'bold': 1,
            'border': 1,
            'bg_color': '#D3D3D3',
            })
        dept_head = workbook.add_format({
            'bold': 1, 
            'border': 1, 
            #'align': 'center', 
            #'valign': 'vcenter', 
            'font_size': 10, 
            'bg_color': '#FFFF00',
            #'text_wrap': True,
            })
        bank_head = workbook.add_format({
            'bold': 1, 
            'border': 1, 
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 10, 
            'bg_color': '#D3D3D3',
            'text_wrap': True,
            })
        total_head = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            })
        detail_head = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 15,
        })
        
        worksheet.right_to_left()
        
        if not self.batch_ids:
            raise ValidationError(_("Kindly select the payslip batches."))
        payslip_domain = [('payslip_run_id', 'in', self.batch_ids.ids)]
        if self.status == 'all_not_cancel':
            payslip_domain.append(('state', '!=', 'cancel'))
        elif self.status == 'done':
            payslip_domain.append(('state', '=', 'close'))

        payslip_ids = self.env['hr.payslip'].search(payslip_domain)
        #print ("payslips:::", payslip_ids)
        
        worksheet.set_column(0, 0, 2)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 14, 10)
        worksheet.freeze_panes(3, 0)
        
        ## Company details:
        worksheet.set_row(0, 35)
        
        worksheet.merge_range(0, 1, 1, 1, '', detail_head)
        
        if self.env.user.company_id.logo:
            im = Image.open(io.BytesIO(base64.b64decode(self.env.user.company_id.logo))).convert("RGB")
            im = im.resize((140, 90))
            im.save('/tmp/image.jpg', quality=90)
            worksheet.insert_image('B1:B2', '/tmp/image.jpg')
        
        worksheet.merge_range(0, 2, 0, 14, self.env.company.name, detail_head)

        worksheet.set_row(1, 35)
        worksheet.merge_range(1, 2, 1, 14, self.file_name, detail_head)

        worksheet.merge_range('C4:E4', '‫اﻻستحقاقات‬', merge_head)
        worksheet.merge_range('A4:B4', '')
        worksheet.merge_range('F4:I4', '')
        worksheet.merge_range('J4:L4', 'اﻻستقطاعات', merge_head)
        worksheet.merge_range('M4:O4', '')
        

        # Header
        worksheet.set_row(4, 30)
        worksheet.write(4, 0, '', bank_head)
        worksheet.write(4, 1, '‫اسم الموظف‬', bank_head)
        worksheet.write(4, 2, 'راتب أساسي‬', bank_head)
        worksheet.write(4, 3, '‫بدل السكن‬', bank_head)
        worksheet.write(4, 4, '‫بدل مواصلات‬', bank_head)
        worksheet.write(4, 5, '‫بدل ادارة‬', bank_head)
        worksheet.write(4, 6, '‫بدلات اخري‬', bank_head)
        worksheet.write(4, 7, '‫‫اضافي‬', bank_head)
        worksheet.write(4, 8, '‫مجموع الاستحقاقات‬', bank_head)
        worksheet.write(4, 9, '‫‫سلفة‬‬', bank_head)
        worksheet.write(4, 10, '‫‫خصم‬‬', bank_head)
        worksheet.write(4, 11, '‫تامينات اجتماعية', bank_head)
        worksheet.write(4, 12, '‫مجموع الاستقطاعات‬', bank_head)
        worksheet.write(4, 13, '‫صافي الراتب‬', bank_head)
        worksheet.write(4, 14, '‫ملاحظات‬', bank_head)
        
        department_ids = self.env['hr.department'].search([])
        branch_ids = self.env['hr.branch'].search([])

        all_branch_data = {}
        for branch in branch_ids:
            all_branch_data.update({branch.name: {}})
        
        row = 5
        total_basic = total_gross = total_net = total_hra = total_ta = 0.0
        total_other_allowance = total_other_allowance2 = total_loan = total_gosi = total_other_deduction = total_deduction = 0.0 
        for department in department_ids:
            payslip_list_ids = payslip_ids.filtered(lambda p: p.employee_id.department_id.id == department.id)
            dept_basic = dept_gross = dept_net = dept_hra = dept_ta = dept_other_allowance = dept_other_allowance2 = dept_loan = dept_gosi = dept_other_deduction = dept_total_deduction = 0.0 
            if payslip_list_ids:

                worksheet.merge_range(row, 0, row, 8, department.name, dept_head)
                worksheet.merge_range(row, 9, row, 14, '')
                row += 1
                sr_no = 1
                for payslip in payslip_list_ids:
                    t_deduction = 0.0
                    basic = gross = net = hra = ta = other_allowance = other_allowance2 = loan = gosi = other_deduction = 0.0 
                    for line in payslip.line_ids:
                        if line.code == 'BASIC':
                            basic = line.total or 0.0
                            dept_basic += basic
                            total_basic += basic 
                        if line.code == 'GROSS':
                            gross = line.total or 0.0
                            dept_gross += gross
                            total_gross += gross
                        if line.code == 'NET':
                            net = line.total or 0.0
                            dept_net += net
                            total_net += net
                        if line.category_id.code == 'ALW':
                            if line.code == 'HRA':
                                hra = line.total or 0.0
                                dept_hra += hra
                                total_hra += hra
                            elif line.code == 'TA':
                                ta = line.total or 0.0
                                dept_ta += ta
                                total_ta += ta
                            elif line.code == 'OTHER':
                                other_allowance += line.total or 0.0
                                dept_other_allowance += other_allowance
                                total_other_allowance += other_allowance
                            else:
                                other_allowance2 += line.total or 0.0
                                dept_other_allowance2 += other_allowance2
                                total_other_allowance2 += other_allowance2
                        elif line.category_id.code == 'DED':
                            if line.code == 'LR':
                                loan = abs(line.total) or 0.0
                                dept_loan += loan
                                total_loan += loan
                            elif line.code == 'GOSI':
                                gosi = abs(line.total) or 0.0
                                dept_gosi += gosi
                                total_gosi += gosi
                            else:
                                other_deduction = abs(line.total) or 0.0
                                dept_other_deduction += other_deduction
                                total_other_deduction += other_deduction
                            t_deduction += abs(line.total)
                            dept_total_deduction += t_deduction
                            total_deduction += t_deduction
                    
                    worksheet.write(row, 0, sr_no, border_head)
                    worksheet.write(row, 1, payslip.employee_id.name, border_head)
                    worksheet.write(row, 2, basic, border_head)
                    worksheet.write(row, 3, hra, border_head)
                    worksheet.write(row, 4, ta, border_head) 
                    worksheet.write(row, 5, other_allowance, border_head)
                    worksheet.write(row, 6, other_allowance2, border_head)
                    worksheet.write(row, 7, '', border_head)
                    worksheet.write(row, 8, gross, border_head)
                    worksheet.write(row, 9, loan, border_head) 
                    worksheet.write(row, 10, other_deduction, border_head)
                    worksheet.write(row, 11, gosi, border_head)
                    worksheet.write(row, 12, t_deduction, border_head)
                    worksheet.write(row, 13, net, border_head)
                    worksheet.write(row, 14, '', border_head)
                    row += 1
                    sr_no += 1
                    if payslip.employee_id.branch_id:
                        if payslip.employee_id.branch_id.name in all_branch_data:
                            branch_values = all_branch_data[payslip.employee_id.branch_id.name]
                            all_branch_data[payslip.employee_id.branch_id.name].update({
                                'basic': branch_values.get('basic', 0.0) + basic,
                                'hra': branch_values.get('hra', 0.0) + hra,
                                'ta': branch_values.get('ta', 0.0) + ta,
                                'other_allowance': branch_values.get('other_allowance', 0.0) + other_allowance,
                                'other_allowance2': branch_values.get('other_allowance2', 0.0) + other_allowance2,
                                'gross': branch_values.get('gross', 0.0) + gross,
                                'loan': branch_values.get('loan', 0.0) + loan,
                                'gosi': branch_values.get('gosi', 0.0) + gosi,
                                'other_deduction': branch_values.get('other_deduction', 0.0) + other_deduction,
                                'total_deduction': branch_values.get('total_deduction', 0.0) + t_deduction,
                                'net': branch_values.get('net', 0.0) + net,
                            })
                # Department total
                worksheet.merge_range(row, 0, row, 1, 'Total %s' % (department.name), bank_head)
                worksheet.write(row, 2, dept_basic, bank_head)
                worksheet.write(row, 3, dept_hra, bank_head)
                worksheet.write(row, 4, dept_ta, bank_head) 
                worksheet.write(row, 5, dept_other_allowance, bank_head)
                worksheet.write(row, 6, dept_other_allowance2, bank_head)
                worksheet.write(row, 7, 0, bank_head)
                worksheet.write(row, 8, dept_gross, bank_head)
                worksheet.write(row, 9, dept_loan, bank_head) 
                worksheet.write(row, 10, dept_other_deduction, bank_head)
                worksheet.write(row, 11, dept_gosi, bank_head)
                worksheet.write(row, 12, dept_total_deduction, bank_head)
                worksheet.write(row, 13, dept_net, bank_head)
                worksheet.write(row, 14, '', bank_head)
                row += 1

        row += 1
        worksheet.merge_range(row, 0, row, 1, '‫والرياض‬ ‫جده‬ ‫لفرع‬ ‫العام‬‬', bank_head)
        worksheet.write(row, 2, total_basic, bank_head)
        worksheet.write(row, 3, total_hra, bank_head)
        worksheet.write(row, 4, total_ta, bank_head) 
        worksheet.write(row, 5, total_other_allowance, bank_head)
        worksheet.write(row, 6, total_other_allowance2, bank_head)
        worksheet.write(row, 7, 0, bank_head)
        worksheet.write(row, 8, total_gross, bank_head)
        worksheet.write(row, 9, total_loan, bank_head) 
        worksheet.write(row, 10, total_other_deduction, bank_head)
        worksheet.write(row, 11, total_gosi, bank_head)
        worksheet.write(row, 12, total_deduction, bank_head)
        worksheet.write(row, 13, total_net, bank_head)
        worksheet.write(row, 14, '', bank_head)

        row += 2
        # Brach Header:
        worksheet.merge_range(row, 2, row, 4, '‫اﻻستحقاقات‬', merge_head)
        worksheet.merge_range(row, 9, row, 11, '‫اﻻستقطاعات‬', merge_head)
        
        row+=1
        worksheet.set_row(row, 30)
        worksheet.write(row, 0, '', bank_head)
        worksheet.write(row, 1, 'اسم الموظف‬', bank_head)
        worksheet.write(row, 2, '‫راتب أساسي‬', bank_head)
        worksheet.write(row, 3, 'بدل السكن‬‬', bank_head)
        worksheet.write(row, 4, 'بدل مواصلات‬‬', bank_head)
        worksheet.write(row, 5, 'بدل ادارة‬', bank_head)
        worksheet.write(row, 6, 'بدلات اخري‬‬', bank_head)
        worksheet.write(row, 7, 'اضافي‬', bank_head)
        worksheet.write(row, 8, '‫مجموع الاستحقاقات‬', bank_head)
        worksheet.write(row, 9, '‫سلفة‬', bank_head)
        worksheet.write(row, 10, 'خصم‬', bank_head)
        worksheet.write(row, 11, '‫تامينات اجتماعية‬', bank_head)
        worksheet.write(row, 12, '‫مجموع الاستقطاعات‬', bank_head)
        worksheet.write(row, 13, 'صافي الراتب‬‬', bank_head)
        worksheet.write(row, 14, '‫ملاحظات‬‬', bank_head)

        row+=1
        sr_no = 1
        branch_basic = branch_gross = branch_net = branch_hra = branch_ta = 0.0
        branch_other_allowance = branch_other_allowance2 = branch_loan = branch_gosi = 0.0
        branch_other_deduction = branch_deduction = branch_total_deduction = 0.0 
        
        for branch_data in all_branch_data:
            worksheet.write(row, 0, sr_no)
            worksheet.write(row, 1, branch_data, merge_head)
            branch_basic += all_branch_data[branch_data].get('basic', 0.0)
            worksheet.write(row, 2, all_branch_data[branch_data].get('basic', 0.0), merge_head)
            branch_hra += all_branch_data[branch_data].get('hra', 0.0)
            worksheet.write(row, 3, all_branch_data[branch_data].get('hra', 0.0), merge_head)
            branch_ta += all_branch_data[branch_data].get('ta', 0.0)
            worksheet.write(row, 4, all_branch_data[branch_data].get('ta', 0.0), merge_head)
            branch_other_allowance += all_branch_data[branch_data].get('other_allowance', 0.0) 
            worksheet.write(row, 5, all_branch_data[branch_data].get('other_allowance', 0.0), merge_head)
            branch_other_allowance2 += all_branch_data[branch_data].get('other_allowance2', 0.0)
            worksheet.write(row, 6, all_branch_data[branch_data].get('other_allowance2', 0.0), merge_head)
            worksheet.write(row, 7, 0, merge_head)
            branch_gross += all_branch_data[branch_data].get('gross', 0.0)
            worksheet.write(row, 8, all_branch_data[branch_data].get('gross', 0.0), merge_head)
            branch_loan += all_branch_data[branch_data].get('loan', 0.0)
            worksheet.write(row, 9, all_branch_data[branch_data].get('loan', 0.0), merge_head) 
            branch_other_deduction += all_branch_data[branch_data].get('other_deduction', 0.0)
            worksheet.write(row, 10, all_branch_data[branch_data].get('other_deduction', 0.0), merge_head)
            branch_gosi += all_branch_data[branch_data].get('gosi', 0.0)
            worksheet.write(row, 11, all_branch_data[branch_data].get('gosi', 0.0), merge_head)
            branch_total_deduction += all_branch_data[branch_data].get('total_deduction', 0.0)
            worksheet.write(row, 12, all_branch_data[branch_data].get('total_deduction', 0.0), merge_head)
            branch_net += all_branch_data[branch_data].get('net', 0.0)
            worksheet.write(row, 13, all_branch_data[branch_data].get('net', 0.0), merge_head)
            worksheet.write(row, 14, '', merge_head)
            sr_no +=1
            row += 1

        worksheet.write(row, 1, '‫الرواتب‬ ‫اجمالي‬', merge_head)
        worksheet.write(row, 2, branch_basic, merge_head)
        worksheet.write(row, 3, branch_hra, merge_head)
        worksheet.write(row, 4, branch_ta, merge_head) 
        worksheet.write(row, 5, branch_other_allowance, merge_head)
        worksheet.write(row, 6, branch_other_allowance2, merge_head)
        worksheet.write(row, 7, 0, merge_head)
        worksheet.write(row, 8, branch_gross, merge_head)
        worksheet.write(row, 9, branch_loan, merge_head) 
        worksheet.write(row, 10, branch_other_deduction, merge_head)
        worksheet.write(row, 11, branch_gosi, merge_head)
        worksheet.write(row, 12, branch_total_deduction, merge_head)
        worksheet.write(row, 13, branch_net, merge_head)
        worksheet.write(row, 14, '', merge_head)
        
        row += 2
        worksheet.write(row, 1, '‫المجموع‬', bank_head)# ar_001 ar_SY
        amt_wrd = self.env.company.currency_id.with_context(lang='ar_001').amount_to_text(total_net)
        worksheet.merge_range(row, 2, row, 13, amt_wrd, bank_head)
        worksheet.write(row, 14, total_net, bank_head)

        row += 2
        worksheet.write(row, 1, '‫الموارد البشرية‬')
        worksheet.write(row, 4, '‫‫المحاسب‬‬')
        worksheet.write(row, 8, '‫المدير المالي‬')
        worksheet.write(row, 12, '‫الرئيس التنفيذي')

        workbook.close()
        report.write({'excel_file': base64.encodebytes(fp.getvalue()), 'filename': filename})
        fp.close()

        return self.return_wiz_action(report.id)

    def return_wiz_action(self, res_id, context=None):
        return {
            'name': 'Payslip Summary Report',
            'view_mode': 'form',
            'res_id': res_id,
            'res_model': 'payroll.summary.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
        }
