# -*- coding: utf-8 -*-
# from odoo import http


# class FinancialCovenant15(http.Controller):
#     @http.route('/petty_cash/petty_cash', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/petty_cash/petty_cash/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('petty_cash.listing', {
#             'root': '/petty_cash/petty_cash',
#             'objects': http.request.env['petty_cash.petty_cash'].search([]),
#         })

#     @http.route('/petty_cash/petty_cash/objects/<model("petty_cash.petty_cash"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('petty_cash.object', {
#             'object': obj
#         })
