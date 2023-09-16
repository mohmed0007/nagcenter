# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID
from odoo.http import request


class HREmployeePortal(http.Controller):

    @http.route(['/letters/get_letter/<int:letter_id>'], type='http', auth="public", website=True)
    def get_letters(self, letter_id, access_token=None, report_type=None, download=False, **kw):
        # API to get letter data
        report_name = False
        letter_data = request.env['letter.request'].sudo().browse(letter_id)
        if letter_data.service_type == 'salary_introduction':
            report_name = request.env.ref('hr_letter_request_ksa.salary_introduction_report_action')
        elif letter_data.service_type == 'salary_transfer':
            report_name = request.env.ref('hr_letter_request_ksa.salary_transfer_template')
        elif letter_data.service_type == 'letter_of_authority':
            report_name = request.env.ref('hr_letter_request_ksa.letter_of_authority_template')
        else:
            report_name = request.env.ref('hr_letter_request_ksa.experience_certificate_template')

        pdf = report_name.with_user(SUPERUSER_ID)._render_qweb_pdf(letter_data.id)
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', 'attachment; filename=report.pdf')
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
