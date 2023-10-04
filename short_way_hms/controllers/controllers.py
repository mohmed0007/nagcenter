# -*- coding: utf-8 -*-
# from odoo import http


# class ShortWayHms(http.Controller):
#     @http.route('/short_way_hms/short_way_hms', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/short_way_hms/short_way_hms/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('short_way_hms.listing', {
#             'root': '/short_way_hms/short_way_hms',
#             'objects': http.request.env['short_way_hms.short_way_hms'].search([]),
#         })

#     @http.route('/short_way_hms/short_way_hms/objects/<model("short_way_hms.short_way_hms"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('short_way_hms.object', {
#             'object': obj
#         })
