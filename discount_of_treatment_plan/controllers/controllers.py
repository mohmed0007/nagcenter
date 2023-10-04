# -*- coding: utf-8 -*-
# from odoo import http


# class DiscountOfTreatmentPlan(http.Controller):
#     @http.route('/discount_of_treatment_plan/discount_of_treatment_plan', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/discount_of_treatment_plan/discount_of_treatment_plan/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('discount_of_treatment_plan.listing', {
#             'root': '/discount_of_treatment_plan/discount_of_treatment_plan',
#             'objects': http.request.env['discount_of_treatment_plan.discount_of_treatment_plan'].search([]),
#         })

#     @http.route('/discount_of_treatment_plan/discount_of_treatment_plan/objects/<model("discount_of_treatment_plan.discount_of_treatment_plan"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('discount_of_treatment_plan.object', {
#             'object': obj
#         })
