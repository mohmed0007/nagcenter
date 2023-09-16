
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
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

# from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class EOSXlsx(models.AbstractModel):
    _name = "report.hr_report_ksa.report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "EOS XLSX Report"

    def generate_xlsx_report(self, workbook, data,partners):
        bold = workbook.add_format({"bold": True})
        bold.set_bg_color("#808080")
        sheet = workbook.add_worksheet("Report")
        sheet.set_column(3, 1, 10)
        sheet.set_column(3, 2, 10)
        sheet.set_column(3, 3, 10)
        sheet.set_column(3, 4, 60)
        sheet.set_column(3, 5, 30)
        sheet.set_column(3, 6, 90)
        sheet.set_column(3, 7, 80)
        sheet.set_column(3, 8, 80)
        sheet.set_column(3, 9, 80)
        sheet.set_column(3, 10, 30)
        sheet.set_column(3, 11, 30)
        sheet.set_column(3, 12, 30)


        sheet.write(0, 4, "End of Service Report", bold)
        sheet.write(3, 1, "SN", bold)
        sheet.write(3, 2, "Employee Code", bold)
        sheet.write(3, 3, "Employee Name", bold)
        sheet.write(3, 4, "Joining Date", bold)
        sheet.write(3, 5, "Report Date", bold)
        sheet.write(3, 6, "Period in Service", bold)
        sheet.write(3, 7, "E.O.S For the 2st 5 Years", bold)
        sheet.write(3, 8, "E.O.S For the 5st 10 Years", bold)
        sheet.write(3, 9, "E.O.S After 10 Years", bold)
        sheet.write(3, 10, "Amount EOS", bold)
        sheet.write(3, 11, "EOS Paid", bold)
        sheet.write(3, 12, "Balance", bold)
        leng = len(data['list'])
        i = 0
        for  l in data['list']:
            print("LKKKKKKKKKKKKKKKKKKKKKKKKKKK",l)
            i = i + 1
            sheet.write(3 + i, 3, l['name'])
            sheet.write(3+i, 4, l['join_date'])
            sheet.write(3+i, 5, l['report_date'])
            sheet.write(3+i, 6, l['period'])
            sheet.write(3+i, 7,l['2_5'])
            sheet.write(3+i, 8,l['more_5'])
            sheet.write(3+i, 9,l['more_10'])
            sheet.write(3+i, 10, l['amount'])
            sheet.write(3+i, 11, l['paid'])
            sheet.write(3+i, 12, l['balance'])


            
           
            # sheet.write(0, 0, "tet", bold)


class EOSXlsx2(models.AbstractModel):
    _name = "report.hr_report_ksa.report2_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "EOS XLSX Report"

    def generate_xlsx_report(self, workbook, data,partners):
        bold = workbook.add_format({"bold": True})
        bold.set_bg_color("#808080")
        sheet = workbook.add_worksheet("Report")
        sheet.set_column(3, 1, 10)
        sheet.set_column(3, 2, 10)
        sheet.set_column(3, 3, 10)
        sheet.set_column(3, 4, 60)
        sheet.set_column(3, 5, 30)
        sheet.set_column(3, 6, 90)
        sheet.set_column(3, 7, 80)
        sheet.set_column(3, 8, 80)
        sheet.set_column(3, 9, 80)
        sheet.set_column(3, 10, 30)
        sheet.set_column(3, 11, 30)
        sheet.set_column(3, 12, 30)


        sheet.write(0, 4, "End of Service Report", bold)
        sheet.write(3, 1, "SN", bold)
        sheet.write(3, 2, "Employee Code", bold)
        sheet.write(3, 3, "Employee Name", bold)
        sheet.write(3, 4, "Joining Date", bold)
        sheet.write(3, 5, "Report Date", bold)
        sheet.write(3, 6, "Period in Service", bold)
        sheet.write(3, 7, "E.O.S For the 2st 5 Years", bold)
        sheet.write(3, 8, "E.O.S For the 5st 10 Years", bold)
        sheet.write(3, 9, "E.O.S After 10 Years", bold)
        sheet.write(3, 10, "Amount EOS", bold)
        sheet.write(3, 11, "EOS Paid", bold)
        sheet.write(3, 12, "Balance", bold)
        leng = len(data['list'])
        i = 0
        for  l in data['list']:
            print("LKKKKKKKKKKKKKKKKKKKKKKKKKKK",l)
            i = i + 1
            sheet.write(3 + i, 3, l['name'])
            sheet.write(3+i, 4, l['join_date'])
            sheet.write(3+i, 5, l['report_date'])
            sheet.write(3+i, 6, l['period'])
            sheet.write(3+i, 7,l['2_5'])
            sheet.write(3+i, 8,l['more_5'])
            sheet.write(3+i, 9,l['more_10'])
            sheet.write(3+i, 10, l['amount'])
            sheet.write(3+i, 11, l['paid'])
            sheet.write(3+i, 12, l['balance'])


            
           
            # sheet.write(0, 0, "tet", bold)

