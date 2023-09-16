# -*- coding: utf-8 -*-
# from odoo import http


# class InvoiceReport(http.Controller):
#     @http.route('/invoice_report/invoice_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/invoice_report/invoice_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('invoice_report.listing', {
#             'root': '/invoice_report/invoice_report',
#             'objects': http.request.env['invoice_report.invoice_report'].search([]),
#         })

#     @http.route('/invoice_report/invoice_report/objects/<model("invoice_report.invoice_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('invoice_report.object', {
#             'object': obj
#         })
