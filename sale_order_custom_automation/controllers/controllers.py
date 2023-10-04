# -*- coding: utf-8 -*-
# from odoo import http


# class SaleOrderCustomAutomation(http.Controller):
#     @http.route('/sale_order_custom_automation/sale_order_custom_automation', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_order_custom_automation/sale_order_custom_automation/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_order_custom_automation.listing', {
#             'root': '/sale_order_custom_automation/sale_order_custom_automation',
#             'objects': http.request.env['sale_order_custom_automation.sale_order_custom_automation'].search([]),
#         })

#     @http.route('/sale_order_custom_automation/sale_order_custom_automation/objects/<model("sale_order_custom_automation.sale_order_custom_automation"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_order_custom_automation.object', {
#             'object': obj
#         })
