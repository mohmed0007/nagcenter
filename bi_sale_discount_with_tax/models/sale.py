# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare
import json
from itertools import groupby


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.depends('discount_amount','discount_method','discount_type')
    def _calculate_discount(self):
        res=0.0
        discount = 0.0
        for self_obj in self:
            if self_obj.discount_method == 'fix':
                discount = self_obj.discount_amount
                res = discount
            elif self_obj.discount_method == 'per':
                discount = self_obj.amount_untaxed * (self_obj.discount_amount/ 100)
                res = discount
            else:
                res = discount
        return res


    @api.depends('order_line','order_line.price_total','order_line.price_subtotal',\
        'order_line.product_uom_qty','discount_amount',\
        'discount_method','discount_type' ,'order_line.discount_amount',\
        'order_line.discount_method','order_line.discount_amt')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        res_config= self.env.company
        cur_obj = self.env['res.currency']
        for order in self:                      
            applied_discount = line_discount = sums = order_discount =  amount_untaxed = amount_tax = amount_after_discount =  0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                applied_discount += line.discount_amt
    
                if line.discount_method == 'fix':
                    line_discount += line.discount_amount
                elif line.discount_method == 'per':
                    line_discount += line.price_subtotal * (line.discount_amount/ 100)            

            if res_config.tax_discount_policy:
                if res_config.tax_discount_policy == 'tax':
                    if order.discount_type == 'line':
                        order.discount_amt = 0.00
                        order.update({
                            'amount_untaxed': amount_untaxed,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax - line_discount,
                            'discount_amt_line' : line_discount,
                        })

                    elif order.discount_type == 'global':
                        order.discount_amt_line = 0.00
                        
                        if order.discount_method == 'per':
                            order_discount = amount_untaxed * (order.discount_amount / 100)  
                            order.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': amount_tax,
                                'amount_total': amount_untaxed + amount_tax - order_discount,
                                'discount_amt' : order_discount,
                            })
                        elif order.discount_method == 'fix':
                            order_discount = order.discount_amount
                            order.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': amount_tax,
                                'amount_total': amount_untaxed + amount_tax - order_discount,
                                'discount_amt' : order_discount,
                            })
                        else:
                            order.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': amount_tax,
                                'amount_total': amount_untaxed + amount_tax ,
                            })
                    else:
                        order.update({
                            'amount_untaxed': amount_untaxed,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax ,
                            })
                elif res_config.tax_discount_policy == 'untax':
                    if order.discount_type == 'line':
                        order.discount_amt = 0.00 
                        order.update({
                            'amount_untaxed': amount_untaxed,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax - applied_discount,
                            'discount_amt_line' : applied_discount,
                        })
                    elif order.discount_type == 'global':
                        order.discount_amt_line = 0.00
                        if order.discount_method == 'per':
                            order_discount = amount_untaxed * (order.discount_amount / 100)
                            if order.order_line:
                                for line in order.order_line:
                                    if line.tax_id:
                                        final_discount = 0.0
                                        try:
                                            final_discount = ((order.discount_amount*line.price_subtotal)/100.0)
                                        except ZeroDivisionError:
                                            pass
                                        discount = line.price_subtotal - final_discount
                                        taxes = line.tax_id.compute_all(discount, \
                                                            order.currency_id,1.0, product=line.product_id, \
                                                            partner=order.partner_id)
                                        sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                                        print("^^^^^^^^^^^^^^^^^here ",sums)
                            order.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': sums,
                                'amount_total': amount_untaxed + sums - order_discount,
                                'discount_amt' : order_discount,  
                            })
                        elif order.discount_method == 'fix':
                            order_discount = order.discount_amount
                            if order.order_line:
                                for line in order.order_line:
                                    if line.tax_id:
                                        final_discount = 0.0
                                        try:
                                            final_discount = ((order.discount_amount*line.price_subtotal)/amount_untaxed)
                                        except ZeroDivisionError:
                                            pass
                                        discount = line.price_subtotal - final_discount

                                        taxes = line.tax_id.compute_all(discount, \
                                                            order.currency_id,1.0, product=line.product_id, \
                                                            partner=order.partner_id)
                                        sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                                        print("sums===========",sums)
                            order.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': sums,
                                'amount_total': amount_untaxed + sums - order_discount,
                                'discount_amt' : order_discount,
                            })
                        else:
                            order.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': amount_tax,
                                'amount_total': amount_untaxed + amount_tax ,
                            })
                    else:
                        order.update({
                            'amount_untaxed': amount_untaxed,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax ,
                            })
                else:
                    order.update({
                            'amount_untaxed': amount_untaxed,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax ,
                            })         
            else:
                order.update({
                    'amount_untaxed': amount_untaxed,
                    'amount_tax': amount_tax,
                    'amount_total': amount_untaxed + amount_tax ,
                    'discount_amt_line': 0,
                    'discount_amt': 0,
                    
                    })

    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method')
    discount_amount = fields.Float('Discount Amount')
    # discount_amt = fields.Monetary(compute='_amount_all', string='Discount', store=False, readonly=True)
    discount_amt = fields.Monetary(compute=False, string='Discount', store=False, readonly=True)
    discount_type = fields.Selection([('line', 'Order Line'), ('global', 'Global'),('non_discount','No Discount')],string='Discount Applies to',default='non_discount')
    # discount_amt_line = fields.Float(compute='_amount_all', string='Line Discount', digits=(16, 4), store=False, readonly=True)
    discount_amt_line = fields.Float(compute=False, string='Line Discount', digits=(16, 4), store=False, readonly=True)

    # def _prepare_invoice(self):
    #     res = super(sale_order,self)._prepare_invoice()
    #     res.update({'discount_method': self.discount_method,
    #             'discount_amount': self.discount_amount,
    #             'discount_amt': self.discount_amt,
    #             'discount_type': self.discount_type,
    #             'discount_amt_line' : self.discount_amt_line,
    #             'discount_amount_line':self.discount_amt_line
    #             })
    #     print("HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHEERE>>//>>",res.discount_type)
    #     return 
        
    # def _prepare_invoice(self):
    #     """
    #     Prepare the dict of values to create the new invoice for a sales order. This method may be
    #     overridden to implement custom invoice generation (making sure to call super() to establish
    #     a clean extension chain).
    #     """
    #     self.ensure_one()
    #     journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
    #     if not journal:
    #         raise UserError(_('Please define an accounting sales journal for the company %s (%s).', self.company_id.name, self.company_id.id))

    #     invoice_vals = {
    #         'ref': self.client_order_ref or '',
    #         'move_type': 'out_invoice',
    #         'narration': self.note,
    #         'currency_id': self.pricelist_id.currency_id.id,
    #         'campaign_id': self.campaign_id.id,
    #         'medium_id': self.medium_id.id,
    #         'source_id': self.source_id.id,
    #         'user_id': self.user_id.id,
    #         'invoice_user_id': self.user_id.id,
    #         'team_id': self.team_id.id,
    #         'partner_id': self.partner_invoice_id.id,
    #         'partner_shipping_id': self.partner_shipping_id.id,
    #         'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_invoice_id.id)).id,
    #         'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
    #         'journal_id': journal.id,  # company comes from the journal
    #         'invoice_origin': self.name,
    #         'invoice_payment_term_id': self.payment_term_id.id,
    #         'payment_reference': self.reference,
    #         'transaction_ids': [(6, 0, self.transaction_ids.ids)],
    #         'invoice_line_ids': [],
    #         'company_id': self.company_id.id,
    #         'discount_method': self.discount_method,
    #         'discount_amount': self.discount_amount,
    #         'discount_amt': self.discount_amt,
    #         'discount_type': self.discount_type,
    #         'discount_amt_line' : self.discount_amt_line,
    #         'discount_amount_line':self.discount_amt_line
    #     }
    #     return invoice_vals

    # def _create_invoices(self, grouped=False, final=False):
    #     res = super(sale_order,self)._create_invoices(grouped=grouped, final=final)
    #     res.update({'discount_type': self.discount_type})
    #     invoice_vals = []
    #     line = res.invoice_line_ids.filtered(lambda x: x.name == _('Down Payments'))
    #     if not line or final == False:
    #         res.update({'discount_method': self.discount_method,
    #                 'discount_amount': self.discount_amount,
    #                 'discount_amt': self.discount_amt,
    #                 'discount_amt_line' : self.discount_amt_line,
    #                 })
    #     else:
    #         for line in res.invoice_line_ids:
    #             line.update({'discount': 0.0,
    #                 'discount_method':None,
    #                 'discount_amount':0.0,
    #                 'discount_amt' : 0.0,})

    #     print("res>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>res$$$$$$$$$$",res.discount_type)
    #     return res
    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['sale.order.line']

            invoice_vals = order._prepare_invoice()
            invoice_vals.update({'discount_method': self.discount_method,
                'discount_amount': self.discount_amount,
                'discount_amt': self.discount_amt,
                'discount_type': self.discount_type,
                'discount_amt_line' : self.discount_amt_line,
                'discount_amount_line':self.discount_amt_line
                })
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        (0, 0, order._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                line_u = line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )
                invoice_line_vals.append(
                    (0, 0, line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ]
            )
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                    
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        print("####################################",invoice_vals_list)
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        return moves


    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed','discount_amount',\
        'discount_method','discount_type' ,'order_line.discount_amount',\
        'order_line.discount_method','order_line.discount_amt',)
    def _compute_tax_totals_json(self):
        if self.state == 'draft' or self.state == 'sale' or self.state == 'sent' or self.state == 'done' or self.state == 'cancel':
            def compute_taxes(order_line):
                amount_untaxed = 0.0
                res_config= self.env.company
                if res_config.tax_discount_policy == 'tax':
                    price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                    order = order_line.order_id
                    return order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)
                elif res_config.tax_discount_policy == 'untax':
                    order = order_line.order_id
                    if order.discount_type == 'line':
                        order.discount_amt = 0.00 
                        for line in order.order_line:
                            amount_untaxed += line.price_subtotal
                        if order_line.discount_method == 'fix':
                            price_amount = order_line.price_subtotal - order_line.discount_amount 
                            taxes = order_line.tax_id._origin.compute_all(price_amount, order_line.order_id.currency_id, 1, product=order_line.product_id, partner=order_line.order_id.partner_shipping_id)
                        
                        elif order_line.discount_method == 'per':
                            price_amount = order_line.price_subtotal - ((order_line.discount_amount*order_line.price_subtotal)/100.0)
                            taxes = order_line.tax_id._origin.compute_all(price_amount, order_line.order_id.currency_id, 1, product=order_line.product_id, partner=order_line.order_id.partner_shipping_id)
                        else:
                            price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                            order = order_line.order_id
                            taxes = order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)
                        return taxes
                    elif order.discount_type == 'global':
                        order.discount_amt_line = 0.00
                        if order.discount_method == 'per':
                            for line in order.order_line:
                                amount_untaxed += line.price_subtotal
                            order_discount = amount_untaxed * (order.discount_amount / 100)
                            if order_line.tax_id:
                                final_discount = 0.0
                                try:
                                    final_discount = ((order.discount_amount*order_line.price_subtotal)/100.0)
                                except ZeroDivisionError:
                                    pass
                                discount = order_line.price_subtotal - final_discount
                                taxes = order_line.tax_id._origin.compute_all(discount, \
                                                    order.currency_id,1.0, product=order_line.product_id, \
                                                    partner=order.partner_id)
                                return taxes
                            else:
                                price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                                order = order_line.order_id
                                return order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)


                        elif order.discount_method == 'fix':
                            order_discount = order.discount_amount
                            if order_line.tax_id:
                                for line in order.order_line:
                                    amount_untaxed += line.price_subtotal
                                final_discount = 0.0
                                try:
                                    final_discount = ((order.discount_amount*order_line.price_subtotal)/amount_untaxed)
                                except ZeroDivisionError:
                                    pass
                                discount = order_line.price_subtotal - final_discount

                                taxes = order_line.tax_id._origin.compute_all(discount, \
                                                    order.currency_id,1.0, product=order_line.product_id, \
                                                    partner=order.partner_id)
                                return taxes
                            else:
                                price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                                order = order_line.order_id
                                return order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)

                        else:
                            price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                            order = order_line.order_id
                            return order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)
                    else:
                        price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                        order = order_line.order_id
                        return order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)
                else:
                    price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                    order = order_line.order_id
                    return order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)

            account_move = self.env['account.move']
            for order in self:
                tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line, compute_taxes)
                tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
                print("tax_totals===============",tax_totals)
                order.tax_totals_json = json.dumps(tax_totals)
        else:
            def compute_taxes(order_line):
                price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                order = order_line.order_id
                return order_line.tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)

            account_move = self.env['account.move']
            for order in self:
                tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line, compute_taxes)
                tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
                order.tax_totals_json = json.dumps(tax_totals)
        


    def action_confirm(self):
        if self.discount_type == 'global' and self.discount_type != 'non_discount':
            if not self.discount_method:
                raise ValidationError(_('Pleas Enter Discount Method.'))

        if self.discount_type == 'line' and self.discount_type != 'non_discount': 
            for line in self.order_line:
                if not line.discount_method:
                    raise ValidationError(_('Pleas Enter Discount Method Peer Line.'))
        # if self.discount_type == 'non_discount':
        #     print("No ")
        super(sale_order, self).action_confirm()


            
class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv,self)._create_invoice(order, so_line, amount)
        res.write({'discount_type': order.discount_type})
        return res


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','discount_method','discount_amount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        res_config= self.env.company
        for line in self:
            if res_config.tax_discount_policy:
                if res_config.tax_discount_policy == 'untax':
                    if line.discount_type == 'line':
                        if line.discount_method == 'fix':
                            price = (line.price_unit * line.product_uom_qty) - line.discount_amount
                            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'] + line.discount_amount,
                                'price_subtotal': taxes['total_excluded'] + line.discount_amount,
                                'discount_amt' : line.discount_amount,
                            })

                        elif line.discount_method == 'per':
                            price = (line.price_unit * line.product_uom_qty) * (1 - (line.discount_amount or 0.0) / 100.0)
                            price_x = ((line.price_unit * line.product_uom_qty) - (line.price_unit * line.product_uom_qty) * (1 - (line.discount_amount or 0.0) / 100.0))
                            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'] + price_x,
                                'price_subtotal': taxes['total_excluded'] + price_x,
                                'discount_amt' : price_x,
                            })
                        else:
                            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'],
                                'price_subtotal': taxes['total_excluded'],
                            })
                    else:
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                        line.update({
                            'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                            'price_total': taxes['total_included'],
                            'price_subtotal': taxes['total_excluded'],
                        })
                elif res_config.tax_discount_policy == 'tax':
                    if line.discount_type == 'line':
                        price_x = 0.0
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)

                        if line.discount_method == 'fix':
                            price_x = (taxes['total_included']) - ( taxes['total_included'] - line.discount_amount)
                        elif line.discount_method == 'per':
                            price_x = (taxes['total_included']) - (taxes['total_included'] * (1 - (line.discount_amount or 0.0) / 100.0))
                        else:
                            price_x = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                
                        line.update({
                            'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                            'price_total': taxes['total_included'],
                            'price_subtotal': taxes['total_excluded'],
                            'discount_amt' : price_x,
                        })
                    else:
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                        line.update({
                            'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                            'price_total': taxes['total_included'],
                            'price_subtotal': taxes['total_excluded'],
                        })
                else:
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                    
                    line.update({
                        'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                        'price_total': taxes['total_included'],
                        'price_subtotal': taxes['total_excluded'],
                    })
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

    is_apply_on_discount_amount =  fields.Boolean("Tax Apply After Discount")
    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method')
    discount_type = fields.Selection(related='order_id.discount_type', string="Discount Applies to")
    discount_amount = fields.Float('Discount Amount')
    discount_amt = fields.Float('Discount Final Amount')

    def _prepare_invoice_line(self,**optional_values):
        res = super(sale_order_line,self)._prepare_invoice_line(**optional_values)
        res.update({'discount': self.discount,
                    'discount_method':self.discount_method,
                    'discount_amount':self.discount_amount,
                    'discount_amt' : self.discount_amt,})
        return res


class ResCompany(models.Model):
    _inherit = 'res.company'

    tax_discount_policy = fields.Selection([('tax', 'Tax Amount'), ('untax', 'Untax Amount')],
        default_model='sale.order',default='tax')


    def _valid_field_parameter(self, field, name):
        return name == 'default_model' or super()._valid_field_parameter(field, name)
        
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_discount_policy = fields.Selection(readonly=False,related='company_id.tax_discount_policy',string='Discount Applies On',default_model='sale.order'
        )





