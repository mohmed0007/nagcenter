# -*- coding: utf-8 -*-
# from odoo import http


# class SmallSaleOrderInvoice(http.Controller):
#     @http.route('/small_sale_order_invoice/small_sale_order_invoice', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/small_sale_order_invoice/small_sale_order_invoice/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('small_sale_order_invoice.listing', {
#             'root': '/small_sale_order_invoice/small_sale_order_invoice',
#             'objects': http.request.env['small_sale_order_invoice.small_sale_order_invoice'].search([]),
#         })

#     @http.route('/small_sale_order_invoice/small_sale_order_invoice/objects/<model("small_sale_order_invoice.small_sale_order_invoice"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('small_sale_order_invoice.object', {
#             'object': obj
#         })
