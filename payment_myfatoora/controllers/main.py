# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

import logging
import pprint
from odoo.exceptions import UserError
import requests
from datetime import date
from odoo import http
from odoo import _
from odoo.http import request
import requests
from odoo.http import request
import werkzeug
import json
from odoo import http
from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class MyfatooraController(http.Controller):
    _return_url = '/payment/myfatoora/return'

    @http.route('/payment/myfatoora/return', type='http', auth="public", csrf=False,
                )
    def myfatoora_dpn(self, **post):

        """ Myfatoora DPN """
        provider = request.env['payment.acquirer'].sudo().search([('provider', '=', 'myfatoora')])
        token = provider.sudo().token
        if provider.state == 'test':
            baseURL = "https://apitest.myfatoorah.com"
        else:
            baseURL = "https://api.myfatoorah.com"
        try:
            headers = {'Content-Type': "application/json", 'Authorization': "bearer " + token}
            url = baseURL + "/v2/GetPaymentStatus"
            payload = {
                "Key": post['paymentId'],
                "KeyType": "PaymentId"
            }
            response = requests.request("POST", url, data=str(payload), headers=headers)
            response = json.loads(response.text)
        except UserError as e:
            raise UserError(_(e))

        _logger.info('Beginning MyFatoorah DPN form_feedback with post data %s', pprint.pformat(post))  # debug

        _logger.exception('Unable to validate the myFatoorah payment')
        form_feedback = request.env['payment.transaction'].sudo().form_feedback(response, 'myfatoora')
        return werkzeug.utils.redirect('/payment/process')

    @http.route('/shop/myfatoora/payment/', type='http', auth="public", csrf=False, website=True)
    def _payment_myfatoora(self, **kw):
        initiate_payment = request.env['payment.acquirer'].initiate_payment(kw.get('Environment'))
        _logger.info("-----/payment/hyperpay/result-----response------------%r----", initiate_payment)
        if initiate_payment.get('ValidationErrors'):
            raise UserError(initiate_payment.get('ValidationErrors')[0].get('Error'))

        payment_methods = initiate_payment['Data']['PaymentMethods']
        return request.render("payment_myfatoora.myfatoora_card",
                              {'CustomerName': kw.get("CustomerName"),
                               'InvoiceValue': kw.get("InvoiceValue"),
                               'CustomerBlock': kw.get("CustomerBlock"),
                               'CustomerStreet': kw.get("CustomerStreet"),
                               'CustomerHouseBuildingNo': kw.get("CustomerHouseBuildingNo"),
                               'CustomerCivilId': kw.get("CustomerCivilId"),
                               'CustomerAddress': kw.get("CustomerAddress"),
                               'CustomerReference': kw.get("CustomerReference"),
                               'CountryCodeId': kw.get("CountryCodeId"),
                               'CustomerMobile': kw.get("CustomerMobile"),
                               'CustomerEmail': kw.get("CustomerEmail"),
                               'DisplayCurrencyId': kw.get("DisplayCurrencyId"),
                               'SendInvoiceOption': kw.get("SendInvoiceOption"),
                               'CallBackUrl': kw.get("CallBackUrl"),
                               'payment_methods': payment_methods,
                               "Environment": kw.get("Environment"),
                               "ErrorUrl": kw.get("ErrorUrl"),

                               })

    @http.route(['/myfatoora/process'], type='http', auth="public", website=True, csrf=False)
    def payment_process(self, **post):
        initiate_payment = request.env['payment.acquirer'].initiate_payment(post.get('Environment'))
        _logger.info("-----/payment/hyperpay/result-----response------------%r----", initiate_payment)
        payment_methods = initiate_payment['Data']['PaymentMethods']
        DisplayCurrencyIso = ''
        for method in payment_methods:
            if method['PaymentMethodId'] == int(post['PaymentMethodId']):
                DisplayCurrencyIso = method['CurrencyIso']
        currency_id = request.env['res.currency'].search([('name', '=', post.get('DisplayCurrencyId'))])
        initiate_payment_currency_id = request.env['res.currency'].search(
            [('name', '=', DisplayCurrencyIso)])
        if not initiate_payment_currency_id:
            raise UserError(
                _("Currency Supported by the Payment Method is not activated. Please activate Currency %s") % DisplayCurrencyIso)
        customer = request.env['res.partner'].search([('name', '=', post.get('CustomerName'))])
        if currency_id.id != initiate_payment_currency_id.id:
            if customer.company_id:
                company = customer.company_id
            else:
                company = request.env.company

            amount = currency_id._convert(float(post.get('InvoiceValue')), initiate_payment_currency_id,
                                          company,
                                          date.today())
        else:
            amount = float(post.get('InvoiceValue'))

        if post.get('Environment') == 'test':
            baseURL = "https://apitest.myfatoorah.com"
        else:
            baseURL = "https://api.myfatoorah.com"
        provider = request.env['payment.acquirer'].sudo().search([('provider', '=', 'myfatoora')])
        token = provider.sudo().token
        url = baseURL + "/v2/ExecutePayment"
        payload = {"PaymentMethodId": post['PaymentMethodId'],
                   "CustomerName": post['CustomerName'],
                   "MobileCountryCode": +965,
                   "CustomerMobile": post['CustomerMobile'],
                   "CustomerEmail": post['CustomerEmail'],
                   "InvoiceValue": amount,
                   "DisplayCurrencyIso": DisplayCurrencyIso,
                   "CallBackUrl": post['CallBackUrl'] + "payment/myfatoora/return",
                   "ErrorUrl": post['ErrorUrl'] + "payment/myfatoorah/error_url",
                   "Language": "en",
                   "CustomerReference": post['CustomerReference'],
                   "CustomerCivilId": post['CustomerCivilId'],
                   "UserDefinedField": "Custom field",
                   "ExpireDate": "",
                   "CustomerAddress": {"Block": post['CustomerBlock'],
                                       "Street": post['CustomerStreet'],
                                       "HouseBuildingNo": post['CustomerHouseBuildingNo'],
                                       "Address": post['CustomerAddress'],
                                       "AddressInstructions": ""}}
        try:
            headers = {'Content-Type': "application/json", 'Authorization': "bearer " + token}
            response = requests.request("POST", url, data=str(payload).encode('utf-8'), headers=headers)
            response = json.loads(response.text)
            if response.get('ValidationErrors'):
                ValidationErrors = response['ValidationErrors']
                for error in ValidationErrors:
                    raise UserError(
                        _(error.get('Error')))

            return werkzeug.utils.redirect(response['Data']['PaymentURL'])
        except UserError as e:
            raise UserError(_(e))

    @http.route('/payment/myfatoorah/error_url', type='http', auth="public", csrf=False, website=True
                )
    def myfatoora_error_url(self, **post):
        provider = request.env['payment.acquirer'].sudo().search([('provider', '=', 'myfatoora')])
        token = provider.sudo().token
        if provider.state == 'test':
            baseURL = "https://apitest.myfatoorah.com"
        else:
            baseURL = "https://api.myfatoorah.com"
        try:
            headers = {'Content-Type': "application/json", 'Authorization': "bearer " + token}
            url = baseURL + "/v2/GetPaymentStatus"
            payload = {
                "Key": post['paymentId'],
                "KeyType": "PaymentId"
            }
            response = requests.request("POST", url, data=str(payload), headers=headers)
            response = json.loads(response.text)
            transaction_status = ''
            error = ''
            for transaction in response['Data']['InvoiceTransactions']:
                transaction_status = transaction['TransactionStatus']
                error = transaction['Error']

        except UserError as e:
            raise UserError(_(e))

        return request.render("payment_myfatoora.error_page", {"TransactionStatus": transaction_status,
                                                               "Error": error})

    @http.route(['/myfatoora/return/shop'], type='http', auth="public", website=True, csrf=False)
    def return_hop(self):
        return werkzeug.utils.redirect('/shop')
