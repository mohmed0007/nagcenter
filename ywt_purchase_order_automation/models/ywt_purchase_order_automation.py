# -*- coding: utf-8 -*-pack
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import ValidationError


class YWTPurchaseOrderAutomation(models.Model):
    _name = "ywt.purchase.order.automation"
    _description = "Purchase Order Automation"

    is_confirm_purchase_order = fields.Boolean(string="Confirm Order", default=False)
    is_order_date_same_bill_date = fields.Boolean(string='Order Date Bill Date', default=False)
    is_validate_incoming_shipment = fields.Boolean(string="Validate Shipment")
    is_create_vendor_bill = fields.Boolean(string='Create Vendor Bill', default=False)
    is_post_vendor_bill = fields.Boolean(string='Post Vendor Bill', default=False)
    is_paid_vendor_bill = fields.Boolean(string='Paid Payment', default=False)
    is_true_default = fields.Boolean(string='default Purchase Order Automation', default=False)
    name = fields.Char(string='Name', size=64)
    
    purchase_journal_id = fields.Many2one('account.journal', string='Purchase Journal', domain=[('type', '=', 'purchase')])
    journal_id = fields.Many2one('account.journal', string='Payment Journal', domain=[('type', 'in', ['cash', 'bank'])])
    outbound_payment_method_id = fields.Many2one('account.payment.method', string="Credit Method", domain=[('payment_type', '=', 'outbound')])

    @api.onchange("is_confirm_purchase_order")
    def onchange_confirm_purchase_order(self):
        for record_id in self:
            if not record_id.is_confirm_purchase_order:
                record_id.is_create_vendor_bill = False

    @api.onchange("is_create_vendor_bill")
    def onchange_vendor_bill_create(self):
        for record_id in self:
            if not record_id.is_create_vendor_bill:
                record_id.is_post_vendor_bill = False

    @api.onchange("is_post_vendor_bill")
    def onchange_validate_vendor_bill(self):
        for record_id in self:
            if not record_id.is_post_vendor_bill:
                record_id.is_paid_vendor_bill = False
                record_id.is_order_date_same_bill_date = False

    @api.model
    def ywt_main_purchase_order_automation_method(self, self_genrated_automation_id=False):
        purchase_order_obj = self.env['purchase.order']
        ywt_purchase_order_automation_history_obj = self.env['ywt.purchase.order.automation.history']
        account_move_obj = self.env['account.move']
        account_payment_register_obj = self.env['account.payment.register']
        
        active_context_ids = self._context.get('purchase_ids')
        if not self_genrated_automation_id:
            purchase_order_automation_ids = self.search([])
        else:
            purchase_order_automation_ids = self.browse(self_genrated_automation_id)
        if not purchase_order_automation_ids:
            return True
        for purchase_order_automation_id in purchase_order_automation_ids:
            if not active_context_ids:
                po_order_ids = purchase_order_obj.search([('ywt_purchase_order_automation_id', '=', purchase_order_automation_id.id), ('state', 'not in', ('done', 'cancel', 'purchase')), ('invoice_status', '!=', 'invoiced')])
            else:
                po_order_ids = purchase_order_obj.search([('ywt_purchase_order_automation_id', '=', purchase_order_automation_id.id), ('id', 'in', active_context_ids)])
            if not po_order_ids:
                continue
            for purchase_order_id in po_order_ids:
                if purchase_order_id.invoice_status and purchase_order_id.invoice_status == 'invoiced':
                    continue

                purchase_order_automation_history_id = ywt_purchase_order_automation_history_obj.create_purchase_order_automation_history()
                if purchase_order_automation_id.is_confirm_purchase_order:
                    try:
                        purchase_order_id.button_confirm()
                    except Exception as e:
                        purchase_order_automation_history_id.write({'mismatch_type': "purchase", 'error_message': "Purchase Order Confirmation Error Please Check in Details Order No %s \n  Error %s" % (purchase_order_id.name, e)})
                        continue
                if purchase_order_automation_id.is_validate_incoming_shipment:
                    try:
                        for picking_id in purchase_order_id.picking_ids.filtered(lambda p: p.state in ('draft', 'waiting', 'confirmed', 'assigned')):
                            for move_line_id in picking_id.move_lines:
                                move_line_id.quantity_done = move_line_id.product_uom_qty
                            picking_id.button_validate()

                    except Exception as e:
                        purchase_order_automation_history_id.write({'mismatch_type': "transfer", 'error_message': "Purchase Order Shipment Validation Error Please Check in Details Order No %s \n  Error %s" % (purchase_order_id.name, e)})
                        continue

                if purchase_order_automation_id.is_create_vendor_bill:
                    try:
                        invoice_vals = {'move_type': 'in_invoice', 'purchase_id': purchase_order_id.id, 'company_id': purchase_order_id.company_id.id}
                        if purchase_order_automation_id.is_order_date_same_bill_date:
                            invoice_vals.update({'invoice_date': str(purchase_order_id.date_order)})

                        if purchase_order_automation_id.purchase_journal_id.id:
                            invoice_vals.update({'journal_id': purchase_order_automation_id.purchase_journal_id.id})
                        else:
                            invoice_vals.update({'currency_id': purchase_order_id.currency_id.id})

                        invoice_obj = account_move_obj.new(invoice_vals)
                        invoice_obj._onchange_purchase_auto_complete()
                        invoice_obj._onchange_partner_id()
                        invoice_obj._onchange_journal()
                        invoice_obj._onchange_invoice_date()
                        invoice_values = invoice_obj._convert_to_write(invoice_obj._cache)
                        create_invoice_id = account_move_obj.create(invoice_values)

                    except Exception as e:
                        purchase_order_automation_history_id.write({'mismatch_type': "invoice", 'error_message': "Purchase Order Create Vendor Bill Error Please Check in Details Order No %s \n  Error %s" % (purchase_order_id.name, e)})
                        continue
                if purchase_order_automation_id.is_post_vendor_bill:
                    for invoice_id in purchase_order_id.invoice_ids.filtered(lambda inv: inv.state == 'draft'):
                        try:
                            invoice_id.action_post()
                        except Exception as e:
                            purchase_order_automation_history_id.write({'mismatch_type': "invoice", 'error_message': "Purchase Order Vendor Bill Validation Error Please Check in Details Order No %s \n  Error %s" % (purchase_order_id.name, e)})
                            continue

                        if purchase_order_automation_id.is_paid_vendor_bill:
                            if invoice_id.amount_residual:
                                vals = {'journal_id': purchase_order_automation_id.journal_id.id,
                                        'communication': invoice_id.name,
                                        'currency_id': invoice_id.currency_id.id,
                                        'payment_type': 'outbound',
                                        'partner_id': invoice_id.commercial_partner_id.id,
                                        'amount': invoice_id.amount_residual,
                                        'partner_type': 'supplier',
                                        'payment_method_id': purchase_order_automation_id.outbound_payment_method_id.id}
                                account_payment_register_id = account_payment_register_obj.with_context({'active_model': 'account.move', 'active_ids': invoice_id.ids}).create(vals)
                                try:
                                    payment_id = account_payment_register_id.action_create_payments()
                                except Exception as e:
                                    purchase_order_automation_history_id.write({'mismatch_type': "invoice", 'error_message': "Purchase Order Vendor Bill Payment Validation Error Please Check in Details Order No %s \n  Error %s" % (purchase_order_id.name, e)})
                                    continue

        return True
