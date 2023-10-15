# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, route
from datetime import datetime
from odoo import models, fields, _

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import UserError, Warning


class HrSelfService(CustomerPortal):

    @route(['/my', '/my/home'], type='http', auth="public", website=True)
    def home(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id','=',user.id)])
        is_employee = 0
        if employee:
            is_employee = 1
        values['is_employee'] = is_employee
        return request.render("hr_portal.portal_my_home_time_off", values)

    @route(['/hr/self/service'], type='http', auth="user", website=True)
    def hr_portal(self, **kwargs):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id','=',user.id)])
        if not employee:
            return request.render("hr_portal.not_employee_template")

        time_off = len(request.env['hr.leave'].sudo().search([('employee_id','=',employee.id)]))
        payslips = request.env['hr.payslip'].sudo().search([('employee_id','=',employee.id)])
        loans = request.env['hr.loan'].sudo().search([('employee_id','=',employee.id)])
        render_values = {
        'employee':employee,
        'partner':user,
        'time_off':time_off,
        'payslips':payslips,
        'loans':loans,
        }
        
        return request.render("hr_portal.my_account",render_values)

    @http.route(['/my/time_off'], type='http', auth="user",method='post', website=True)
    def portal_my_time_off(self,**post):
        values = self._prepare_portal_layout_values()
        user_id = request.env.user.id
        employee = request.env['hr.employee'].sudo().search([('user_id','=',user_id)])
        time_off = request.env['hr.leave'].sudo().search([('employee_id','=',employee.id)])
        types = request.env['hr.leave.type'].sudo().search([('requires_allocation','=','no')])
        error = []
        if 'submit' in post:
            time_off_type_options=[]
            for option in types:
                time_off_type_options.append(_(option.id))
            if post.get('time_off_type'):
                time_off_type = post['time_off_type'].strip()
                if time_off_type not in time_off_type_options:
                    error["time_off_type"] = _('Please choose a valid time off type')
            if error:
                pass   

            else:
                try :
                    date_to = datetime.strptime(post['date_to'], '%Y-%m-%d')
                    date_from = datetime.strptime(post['date_from'], '%Y-%m-%d')
                    m = date_to - date_from

                    time_off_id = request.env['hr.leave'].sudo().create({
                            'request_date_from': date_from.date(),
                            'request_date_to': date_to.date(),
                            'holiday_status_id': int(time_off_type),
                            'employee_id': employee.id,
                            'number_of_days': m.total_seconds()/(60*60*24),
                            'name': post['name'],
                            })
                except:
                    raise UserError(_('Please make sure  your information and dates is correct'))
                return request.redirect('/my/time_off')
    
        values.update({
            'page_name': 'time_off',
            'error':error,
            'types':types,
            'time_off': time_off,
            'page_name': 'time off',
            'default_url': '/my/time_off',
        })

        return request.render("hr_portal.portal_my_time_off", values)

    #####################################################################################################

    @http.route(['/my/letter'], type='http', auth="user", website=True)
    def portal_my_letter_request(self, **post):
        values = self._prepare_portal_layout_values()
        user_id = request.env.user.id
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)])
        letter_request_ids = request.env['letter.request'].sudo().search([('employee_id', '=', employee.id)])
        error = []
        if 'submit' in post:
            if error:
                pass

            else:
                try:
                    letter_request_id = request.env['letter.request'].sudo().create({
                        'service_type': post['service_type'],
                        'service_to': post['service_to'],
                        'reason': post['reason'],
                        'employee_id': employee.id
                    })
                except:
                    raise UserError(_('Set Correct  information'))
                return request.redirect('/my/letter')

        values.update({
            'page_name': 'Letter Request',
            'letter_request_ids': letter_request_ids,
            'page_name': 'Letters',
            'default_url': '/my/letter',
        })
        return request.render("hr_portal.portal_my_letter_request", values)

    #####################################################################################################

#                       EOS
    #####################################################################################################

    @http.route(['/my/eos'], type='http', auth="user", website=True)
    def portal_my_eos(self, **post):
        values = self._prepare_portal_layout_values()
        user_id = request.env.user.id
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user_id)])
        leavings = request.env['hr.employee.leaving'].sudo().search([('employee_id', '=', employee.id)])
        error = []
        if 'submit' in post:
            if error:
                pass

            else:
                try:
                    leaving_id = request.env['hr.employee.leaving'].sudo().create({
                        'reason': post['reason'],
                        'description': post['description'],
                        'requested_date': post['requested_date'],
                        'notice_start_date': post['notice_start_date'],
                        'employee_id': employee.id
                    })
                except:
                    raise UserError(_('Set Correct  information'))
                return request.redirect('/my/eos')

        values.update({
            'page_name': 'EOS Request',
            'leavings': leavings,
            'page_name': 'leavings',
            'default_url': '/my/eos',
        })
        return request.render("hr_portal.portal_my_eos", values)

    #####################################################################################################


    @http.route(['/my/loans'], type='http', auth="user", website=True)
    def portal_my_loans(self,**post):
        values = self._prepare_portal_layout_values()
        user_id = request.env.user.id
        employee = request.env['hr.employee'].sudo().search([('user_id','=',user_id)])
        loans = request.env['hr.loan'].sudo().search([('employee_id','=',employee.id)])
        error = []
        if 'submit' in post:
            if error:
                pass

            else:
                try:
                    loan_id = request.env['hr.loan'].sudo().create({
                        'loan_amount':post['amount'],
                        'installment':post['installment'],
                        'payment_date':post['date'],
                        'employee_id':employee.id
                        })
                except:
                    raise UserError(_('Set Correct  information'))
                return request.redirect('/my/loans')

        values.update({
            'page_name': 'loans',
            'loans': loans,
            'page_name': 'loans',
            'default_url': '/my/loans',
        })
        return request.render("hr_portal.portal_my_loans", values)
