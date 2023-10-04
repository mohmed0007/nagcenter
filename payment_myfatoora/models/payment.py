# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.


import json
import logging
from urllib.parse import urljoin

import requests
from odoo.addons.payment.models.payment_acquirer import ValidationError

from odoo.http import request
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AcquirerMyFatoora(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('myfatoora', 'MyFatoora')], ondelete={'myfatoora': 'set default'})
    token = fields.Char('Token', groups='base.group_user')
    payment_url = fields.Char(string="Payment URL")

    def _get_feature_support(self):
        res = super(AcquirerMyFatoora, self)._get_feature_support()
        res['fees'].append('myfatoora')
        return res

    @api.model
    def _get_myfatoora_urls(self, environment):

        base_url = self.get_base_url()
        """ MyFatoora URLS """
        if environment == 'prod':
            return {
                'myfatoora_form_url': base_url + "shop/myfatoora/payment/",
            }
        else:

            return {
                'myfatoora_form_url': base_url + "shop/myfatoora/payment/"
            }

    def myfatoora_form_generate_values(self, values):
        currency = self.env['res.currency'].browse(values['currency_id'])
        base_url = self.get_base_url()
        myfatoora_tx_values = dict(values)
        myfatoora_tx_values.update({
            "InvoiceValue": values.get('amount'),
            "PaymentMethodId": 2,
            "CustomerName": values.get('partner_name'),
            "CustomerBlock": "",
            "CustomerStreet": values.get('partner_city'),
            "CustomerHouseBuildingNo": "",
            "CustomerCivilId": "",
            "CustomerAddress": values.get('partner_address'),
            "CustomerReference": values.get('reference'),
            "CountryCodeId": values.get('partner_country').code,
            "CustomerMobile": values.get('partner').phone,
            "CustomerEmail": values.get('partner_email'),
            "DisplayCurrencyId": currency.name,
            "SendInvoiceOption": 1,
            "CallBackUrl": self.get_base_url(),
            "ErrorUrl": self.get_base_url(),
            'return_url': '%s' % urljoin(base_url, '/payment/myfatoora/return'),
            "Language": 1,
            "SourceInfo": "",
            "Environment": self.state
        })

        return myfatoora_tx_values

    def myfatoora_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_myfatoora_urls(environment)['myfatoora_form_url']

    def initiate_payment(self, state=False):
        print('>>>>>>>>>>>>>>', state)
        if state:
            baseURL = "https://apitest.myfatoorah.com" if state == 'test' else "https://api.myfatoorah.com"
        else:
            baseURL = "https://apitest.myfatoorah.com"
        provider = self.env['payment.acquirer'].sudo().search([('provider', '=', 'myfatoora')])
        token = provider.sudo().token
        url = baseURL + "/v2/InitiatePayment"
        payload = {
            "InvoiceAmount": 1,
            "CurrencyIso": self.env.company.currency_id.name
        }
        try:
            headers = {'Content-Type': "application/json", 'Authorization': "bearer " + token}
            response = requests.request("POST", url, data=str(payload), headers=headers)
            print('response', response)
        except UserError as e:
            raise UserError(_(e))
        if response:
            return json.loads(response.text)
        else:
            raise UserError(_('No Response, Please Check Your Environment and Token In Payment Acquirer. This may due to wrong token configuration accroding to the enviornment'))


class TxMyFatoorah(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _myfatoora_form_get_tx_from_data(self, data):
        transaction_id = 1
        for transaction in data['Data']['InvoiceTransactions']:
            transaction_id = transaction['TransactionId']
        reference, txn_id = data['Data']['CustomerReference'], transaction_id
        if not reference or not txn_id:
            error_msg = _('MyFatoorah: received data with missing reference (%s) or (%s)') % (reference, txn_id)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        txs = self.env['payment.transaction'].search([('reference', '=', reference)])
        if not txs or len(txs) > 1:
            error_msg = 'MyFatoorah: received data for reference %s' % (reference)
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    def _myfatoora_form_get_invalid_parameters(self, data):
        transaction_id = 1
        for transaction in data['Data']['InvoiceTransactions']:
            transaction_id = transaction['TransactionId']
        invalid_parameters = []
        if self.acquirer_reference and transaction_id != self.acquirer_reference:
            invalid_parameters.append(('TransactionId', transaction_id, self.acquirer_reference))
        return invalid_parameters

    def _myfatoora_form_validate(self, data):
        transaction_status = ''
        transaction_id = 1
        for transaction in data['Data']['InvoiceTransactions']:
            transaction_status = transaction['TransactionStatus']
            transaction_id = transaction['TransactionId']
        if transaction_status == 'Succss':
            success_message = "Transaction Successfully Completed"
            logger_msg = _('MyFatoorah:' + success_message)
            _logger.info(logger_msg)
            self.write({
                'acquirer_reference': transaction_id,
            })
            self._set_transaction_done()
            return True
        elif transaction_status == 'InProgress':
            pending_message = "Transaction is Pending"
            logger_msg = _('MyFatoorah:' + pending_message)
            _logger.info(logger_msg)
            self.write({
                'acquirer_reference': transaction_id,
            })
            self._set_transaction_pending()
            return True
        elif transaction_status == 'Failed':
            error_message = "Transaction Failed!!"
            error = _('MyFatoorah:' + error_message)
            _logger.info(error)
            self.write({'state_message': error})
            self._set_transaction_cancel()
            return False
