# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BusinessTripPayment(models.TransientModel):
    _name = "business.trip.payment"
    _description = "Business Trip Payment"

    amount = fields.Monetary(string='Payment Amount')
    payment_type = fields.Selection([('bank', 'Bank'), ('cash', 'Cash')], required=True)
    journal_id = fields.Many2one('account.journal', string='Payment Method', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True, copy=False)
    debit_account_id = fields.Many2one('account.account', string="Employee Account")
    business_trip_id = fields.Many2one('business.trip', string='Business Trip')

    @api.model
    def default_get(self, fields):
        rec = super(BusinessTripPayment, self).default_get(fields)
        if rec.get('business_trip_id'):
            business_trip_id = self.env['business.trip'].browse(rec.get('business_trip_id'))
            if not business_trip_id.employee_id.address_home_id:
                raise UserError('You must Define a Private address for employee.You can configure it in employee master')
            if business_trip_id.employee_id.address_home_id and not business_trip_id.employee_id.address_home_id.property_account_receivable_id:
                raise UserError(_("Please configure 'Account Receivable' on customer %s.") % (business_trip_id.employee_id.address_home_id.name))
            if business_trip_id.employee_id.address_home_id.property_account_receivable_id:
                rec['debit_account_id'] = business_trip_id.employee_id.address_home_id.property_account_receivable_id.id
        return rec

    def action_validate_payment(self):
        context = self._context
        for trip in self:
            if trip.amount == 0.0:
                raise UserError('You can not pay amount 0.0')
             
            payment_methods = trip.journal_id.outbound_payment_method_ids
            payment_obj = self.env['account.payment']
            all_fields = payment_obj.fields_get()
            account_payment_data = payment_obj.default_get(all_fields)
            if not trip.business_trip_id.employee_id.address_home_id:
                raise UserError(_("No Home Address found for the employee %s, please configure one.") % (
                    trip.business_trip_id.employee_id.name))

            account_payment_data.update({'payment_method_id': payment_methods and payment_methods[0].id or False,
                                        'payment_type': 'outbound',
                                        'partner_type': 'supplier',
                                        'partner_id': trip.business_trip_id.employee_id.address_home_id.id,
                                        'amount': trip.amount,
                                        'journal_id': trip.journal_id.id,
                                        'date': fields.Date.today(),
                                        })
            payment_id = self.env['account.payment'].create(account_payment_data)
            payment_id.action_post()
            if context.get('advance_payment', False):
                trip.business_trip_id.advance_payment_id = payment_id.id
                trip.business_trip_id.advance_amount = trip.amount
            else:
                trip.business_trip_id.payment_entry_id = payment_id.id
                trip.business_trip_id.adjustment_amount = trip.amount
        return True
                    
