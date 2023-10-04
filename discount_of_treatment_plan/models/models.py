# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

import odoo.addons.decimal_precision as dp

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare
import json

class Prescription(models.Model):
    _inherit = 'prescription.order'
    tax_totals_json = fields.Char(
        compute='_compute_tax_totals_json',
    )
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string='Fiscal Position',
        domain="[('company_id', '=', company_id)]", 
        help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices."
        "The default value comes from the customer.")

    @api.onchange('patient_id', 'company_id')
    def onchange_partner_shipping_id(self):
        """
        Trigger the change of fiscal position when the shipping address is modified.
        """
        self.fiscal_position_id = self.env['account.fiscal.position'].with_company(self.company_id).get_fiscal_position(self.patient_id.partner_id.id)
        return {}
    
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

    
    @api.depends('prescription_line_ids','prescription_line_ids.price_total','prescription_line_ids.price_subtotal',\
        'prescription_line_ids.dose','discount_amount',\
        'discount_method','discount_type' ,'prescription_line_ids.discount_amount',\
        'prescription_line_ids.discount_method','prescription_line_ids.discount_amt')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        res_config= self.env.company
        cur_obj = self.env['res.currency']
        for order in self:                      
            applied_discount = line_discount = sums = order_discount =  amount_untaxed = amount_tax = amount_after_discount =  0.0
            for line in order.prescription_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                applied_discount += line.discount_amt
    
                if line.discount_method == 'fix':
                    line_discount += line.discount_amount
                elif line.discount_method == 'per':
                    line_discount += line.price_subtotal * (line.discount_amount/ 100) 
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>443",applied_discount)           

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
                        print("444444444444444444444444444444",{
                            'amount_untaxed': amount_untaxed,
                            'amount_tax': amount_tax,
                            'amount_total': amount_untaxed + amount_tax - applied_discount,
                            'discount_amt_line' : applied_discount,
                        })
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
                            if order.prescription_line_ids:
                                for line in order.prescription_line_ids:
                                    if line.tax_ids:
                                        final_discount = 0.0
                                        try:
                                            final_discount = ((order.discount_amount*line.price_subtotal)/100.0)
                                        except ZeroDivisionError:
                                            pass
                                        discount = line.price_subtotal - final_discount
                                        taxes = line.tax_ids.compute_all(discount, \
                                                            order.currency_id,1.0, product=line.product_id, \
                                                            partner=order.patient_id.partner_id)
                                        sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                            order.update({
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': sums,
                                'amount_total': amount_untaxed + sums - order_discount,
                                'discount_amt' : order_discount,  
                            })
                        elif order.discount_method == 'fix':
                            order_discount = order.discount_amount
                            if order.prescription_line_ids:
                                for line in order.prescription_line_ids:
                                    if line.tax_ids:
                                        final_discount = 0.0
                                        try:
                                            final_discount = ((order.discount_amount*line.price_subtotal)/amount_untaxed)
                                        except ZeroDivisionError:
                                            pass
                                        discount = line.price_subtotal - final_discount

                                        taxes = line.tax_ids.compute_all(discount, \
                                                            order.currency_id,1.0, product=line.product_id, \
                                                            partner=order.patient_id.partner_id)
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
                    })

    # def _amount_all(self):
        # """
        # Compute the total amounts of the SO.
        # """
        # res_config= self.env.company
        # cur_obj = self.env['res.currency']
        # for order in self:                      
        #     applied_discount = line_discount = sums = order_discount =  amount_untaxed = amount_tax = amount_after_discount =  0.0
        #     for line in order.prescription_line_ids:
        #         amount_untaxed += line.price_subtotal
        #         amount_tax += line.price_tax
        #         applied_discount += line.discount_amt
    
        #         if line.discount_method == 'fix':
        #             line_discount += line.discount_amount
        #         elif line.discount_method == 'per':
        #             line_discount += line.price_subtotal * (line.discount_amount/ 100)            

        #     if res_config.tax_discount_policy_prescribtion_order:
        #         if res_config.tax_discount_policy_prescribtion_order == 'tax':
        #             if order.discount_type == 'line':
        #                 order.discount_amt = 0.00
        #                 order.update({
        #                     'amount_untaxed': amount_untaxed,
        #                     'amount_tax': amount_tax,
        #                     'amount_total': amount_untaxed + amount_tax - line_discount,
        #                     'discount_amt_line' : line_discount,
        #                 })

        #             elif order.discount_type == 'global':
        #                 order.discount_amt_line = 0.00
                        
        #                 if order.discount_method == 'per':
        #                     order_discount = amount_untaxed * (order.discount_amount / 100)  
        #                     order.update({
        #                         'amount_untaxed': amount_untaxed,
        #                         'amount_tax': amount_tax,
        #                         'amount_total': amount_untaxed + amount_tax - order_discount,
        #                         'discount_amt' : order_discount,
        #                     })
        #                 elif order.discount_method == 'fix':
        #                     order_discount = order.discount_amount
        #                     order.update({
        #                         'amount_untaxed': amount_untaxed,
        #                         'amount_tax': amount_tax,
        #                         'amount_total': amount_untaxed + amount_tax - order_discount,
        #                         'discount_amt' : order_discount,
        #                     })
        #                 else:
        #                     order.update({
        #                         'amount_untaxed': amount_untaxed,
        #                         'amount_tax': amount_tax,
        #                         'amount_total': amount_untaxed + amount_tax ,
        #                     })
        #             else:
        #                 print(">>>>>>>>>>>>>amount tax>>>>>>>>>>",amount_tax)
        #                 order.update({
        #                     'amount_untaxed': amount_untaxed,
        #                     'amount_tax': amount_tax,
        #                     'amount_total': amount_untaxed + amount_tax ,
        #                     })
        #         elif res_config.tax_discount_policy_prescribtion_order == 'untax':
        #             if order.discount_type == 'line':
        #                 order.discount_amt = 0.00 
        #                 order.update({
        #                     'amount_untaxed': amount_untaxed,
        #                     'amount_tax': amount_tax,
        #                     'amount_total': amount_untaxed + amount_tax - applied_discount,
        #                     'discount_amt_line' : applied_discount,
        #                 })
        #             elif order.discount_type == 'global':
        #                 order.discount_amt_line = 0.00
        #                 if order.discount_method == 'per':
        #                     order_discount = amount_untaxed * (order.discount_amount / 100)
        #                     if order.prescription_line_ids:
        #                         for line in order.prescription_line_ids:
        #                           if line.tax_ids:
        #                                 final_discount = 0.0
        #                                 try:
        #                                     final_discount = ((order.discount_amount*line.price_subtotal)/100.0)
        #                                 except ZeroDivisionError:
        #                                     pass
        #                                 discount = line.price_subtotal - final_discount
        #                                 taxes = line.tax_ids.compute_all(discount, \
        #                                                     order.currency_id,1.0, product=line.product_id, \
        #                                                     partner=order.patient_id)
        #                                 sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
        #                     order.update({
        #                         'amount_untaxed': amount_untaxed,
        #                         'amount_tax': sums,
        #                         'amount_total': amount_untaxed + sums - order_discount,
        #                         'discount_amt' : order_discount,  
        #                     })
        #                 elif order.discount_method == 'fix':
        #                     order_discount = order.discount_amount
        #                     if order.prescription_line_ids:
        #                         for line in order.prescription_line_ids:
        #                             if line.tax_ids:
        #                                 final_discount = 0.0
        #                                 try:
        #                                     final_discount = ((order.discount_amount*line.price_subtotal)/amount_untaxed)
        #                                 except ZeroDivisionError:
        #                                     pass
        #                                 discount = line.price_subtotal - final_discount

        #                                 taxes = line.tax_ids.compute_all(discount, \
        #                                                     order.currency_id,1.0, product=line.product_id, \
        #                                                     partner=order.patient_id)
        #                                 sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
        #                                 print("sums===========",sums)
        #                     order.update({
        #                         'amount_untaxed': amount_untaxed,
        #                         'amount_tax': sums,
        #                         'amount_total': amount_untaxed + sums - order_discount,
        #                         'discount_amt' : order_discount,
        #                     })
        #                 else:
        #                     order.update({
        #                         'amount_untaxed': amount_untaxed,
        #                         'amount_tax': amount_tax,
        #                         'amount_total': amount_untaxed + amount_tax ,
        #                     })
        #             else:
        #                 print(">>>>>>>>>>>>>amount tax>>>>>>>>>>",amount_tax)
        #                 order.update({
        #                     'amount_untaxed': amount_untaxed,
        #                     'amount_tax': amount_tax,
        #                     'amount_total': amount_untaxed + amount_tax ,
        #                     })
        #         else:
        #             order.update({
        #                     'amount_untaxed': amount_untaxed,
        #                     'amount_tax': amount_tax,
        #                     'amount_total': amount_untaxed + amount_tax ,
        #                     })         
        #     else:
        #         order.update({
        #             'amount_untaxed': amount_untaxed,
        #             'amount_tax': amount_tax,
        #             'amount_total': amount_untaxed + amount_tax ,
        #             })


    # def create_invoice(self):
    #     if not self.prescription_line_ids:
    #         raise UserError(_("Please add prescription lines first."))
    #     product_data = []
    #     for line in self.prescription_line_ids:
    #         product_data.append({
    #             'product_id': line.product_id,
    #             'quantity': line.quantity,
    #             'name': line.name,
    #             'display_type': line.display_type,
    #             'discount': 0.0,
    #             'discount_type':line.discount_type,
    #             'discount_method': line.discount_method ,
    #             'discount_amount': line.discount_amount,
    #             'discount_amt' : line.discount_amt,
                
    #         })

            
    #     inv_data = {
    #         'physician_id': self.physician_id and self.physician_id.id or False,
    #         'hospital_invoice_type': 'pharmacy',
            
    #     }
    #     invoice = self.acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data=inv_data)
    #     invoice.write({
    #         'create_stock_moves': False if self.deliverd else True,
    #         'prescription_id': self.id,
    #         'discount_method': self.discount_method,
    #         'discount_amount': self.discount_amount,
    #         'discount_amt': self.discount_amt,
    #         'discount_amt_line' : self.discount_amt_line,
    #         'invoice_line_ids': [(0,0,{
    #             'discount_type': self.prescription_line_ids.discount_type,
    #             'discount_method': self.prescription_line_ids.discount_method ,
    #             'discount_amount': self.prescription_line_ids.discount_amount,
    #             'discount_amt' : self.prescription_line_ids.discount_amt,
    #         })]

    #     })
    #     self.sudo().invoice_id = invoice.id





    # @api.depends('prescription_line_ids.price_total')
    # def _amount_all(self):
    #     """
    #     Compute the total amounts of the order.
    #     """
    #     for order in self:
    #         amount_untaxed = amount_tax = 0.0
    #         for line in order.prescription_line_ids:
    #             amount_untaxed += line.price_subtotal
    #             amount_tax += line.price_tax
    #         order.update({
    #             'amount_untaxed': order.company_id.currency_id.round(amount_untaxed),
    #             'amount_tax': order.company_id.currency_id.round(amount_tax),
    #             'amount_total': amount_untaxed + amount_tax,
    #         })


    def view_invoice(self):
        invoices = self.mapped('invoice_id')
        action = self.acs_action_view_invoice(invoices)

        return action


    @api.depends('prescription_line_ids.tax_ids', 'prescription_line_ids.price_unit', 'amount_total', 'amount_untaxed','discount_amount',\
        'discount_method','discount_type' ,'prescription_line_ids.discount_amount',\
        'prescription_line_ids.discount_method','prescription_line_ids.discount_amt',)
    def _compute_tax_totals_json(self):
        if self.state == 'draft':
            def compute_taxes(prescription_line_ids):
                amount_untaxed = 0.0
                res_config= self.env.company
                if res_config.tax_discount_policy_prescribtion_order == 'tax':
                    price = prescription_line_ids.price_unit * (1 - (prescription_line_ids.discount or 0.0) / 100.0)
                    order = prescription_line_ids.prescription_id  
                    return prescription_line_ids.tax_ids._origin.compute_all(price, order.currency_id, prescription_line_ids.quantity, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)
                elif res_config.tax_discount_policy_prescribtion_order == 'untax':
                    order = prescription_line_ids.prescription_id 
                    if order.discount_type == 'line':
                        order.discount_amt = 0.00 
                        for line in order.prescription_line_ids:
                            amount_untaxed += line.price_subtotal
                        if prescription_line_ids.discount_method == 'fix':
                            price_amount = prescription_line_ids.price_subtotal - prescription_line_ids.discount_amount 
                            taxes = prescription_line_ids.tax_ids._origin.compute_all(price_amount, prescription_line_ids.prescription_id.currency_id, 1, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)
                        
                        elif prescription_line_ids.discount_method == 'per':
                            price_amount = prescription_line_ids.price_subtotal - ((prescription_line_ids.discount_amount*prescription_line_ids.price_subtotal)/100.0)
                            taxes = prescription_line_ids.tax_ids._origin.compute_all(price_amount, prescription_line_ids.prescription_id .currency_id, 1, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)
                        else:
                            #hina
                            price = prescription_line_ids.price_unit * (1 - (prescription_line_ids.discount or 0.0) / 100.0)
                            order = prescription_line_ids.prescription_id
                            taxes = prescription_line_ids.tax_ids._origin.compute_all(price, order.currency_id, prescription_line_ids.quantity, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)
                        return taxes
                    elif order.discount_type == 'global':
                        order.discount_amt_line = 0.00
                        if order.discount_method == 'per':
                            for line in order.prescription_line_ids:
                                amount_untaxed += line.price_subtotal
                            order_discount = amount_untaxed * (order.discount_amount / 100)
                            if prescription_line_ids.tax_ids:
                                final_discount = 0.0
                                try:
                                    final_discount = ((order.discount_amount*prescription_line_ids.price_subtotal)/100.0)
                                except ZeroDivisionError:
                                    pass
                                discount = prescription_line_ids.price_subtotal - final_discount
                                taxes = prescription_line_ids.tax_ids._origin.compute_all(discount, \
                                                    order.currency_id,1.0, product=prescription_line_ids.product_id, \
                                                    partner=order.patient_id.partner_id)
                                return taxes
                            else:
                                price = prescription_line_ids.price_unit * (1 - (prescription_line_ids.discount or 0.0) / 100.0)
                                order = prescription_line_ids.prescription_id
                                return prescription_line_ids.tax_ids._origin.compute_all(price, order.currency_id, prescription_line_ids.quantity, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)


                        elif order.discount_method == 'fix':
                            order_discount = order.discount_amount
                            if prescription_line_ids.tax_ids:
                                for line in order.prescription_line_ids:
                                    amount_untaxed += line.price_subtotal
                                final_discount = 0.0
                                try:
                                    final_discount = ((order.discount_amount*prescription_line_ids.price_subtotal)/amount_untaxed)
                                except ZeroDivisionError:
                                    pass
                                discount = prescription_line_ids.price_subtotal - final_discount

                                taxes = prescription_line_ids.tax_ids._origin.compute_all(discount, \
                                                    order.currency_id,1.0, product=prescription_line_ids.product_id, \
                                                    partner=order.patient_id.partner_id)
                                return taxes
                            else:
                                price = prescription_line_ids.price_unit * (1 - (prescription_line_ids.discount or 0.0) / 100.0)
                                #hina
                                order = prescription_line_ids.prescription_id
                                return prescription_line_ids.tax_ids._origin.compute_all(price, order.currency_id, prescription_line_ids.quantity, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)

                        else:
                            price = prescription_line_ids.price_unit * (1 - (prescription_line_ids.discount or 0.0) / 100.0)
                            order = prescription_line_ids.prescription_id
                            return prescription_line_ids.tax_ids._origin.compute_all(price, order.currency_id, prescription_line_ids.quantity, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)
                    else:
                        price = prescription_line_ids.price_unit * (1 - (prescription_line_ids.discount or 0.0) / 100.0)
                        order = prescription_line_ids.prescription_id
                        #hina
                        return prescription_line_ids.tax_ids._origin.compute_all(price, order.currency_id, prescription_line_ids.quantity, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)
                else:
                    price = prescription_line_ids.price_unit * (1 - (prescription_line_ids.discount or 0.0) / 100.0)
                    order = prescription_line_ids.prescription_id
                    return prescription_line_ids.tax_ids._origin.compute_all(price, order.currency_id, prescription_line_ids.quantity, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)

            account_move = self.env['account.move']
            for order in self:
                tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.prescription_line_ids, compute_taxes)
                tax_totals = account_move._get_tax_totals(order.patient_id.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
                print("tax_totals===============",tax_totals)
                order.tax_totals_json = json.dumps(tax_totals)
        else:
            def compute_taxes(prescription_line_ids):
                price = prescription_line_ids.price_unit * (1 - (prescription_line_ids.discount or 0.0) / 100.0)
                order = prescription_line_ids.prescription_id
                return prescription_line_ids.tax_ids._origin.compute_all(price, order.currency_id, prescription_line_ids.quantity, product=prescription_line_ids.product_id, partner=prescription_line_ids.prescription_id.create_uid.partner_id)

            account_move = self.env['account.move']
            for order in self:
                tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.prescription_line_ids, compute_taxes)
                tax_totals = account_move._get_tax_totals(order.patient_id.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
                order.tax_totals_json = json.dumps(tax_totals)



    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method')
    discount_amount = fields.Float('Discount Amount')
    discount_amt = fields.Monetary(compute='_amount_all',string='Discount', store=True, readonly=True)
    discount_type = fields.Selection([('line', 'Order Line'), ('global', 'Global'),('non_discount','No Discount')],string='Discount Applies to',default='non_discount')
    discount_amt_line = fields.Float(compute='_amount_all',string='Line Discount', digits=(16, 4), store=True, readonly=True)


    # compute='_amount_all',

class PrescriptionLine(models.Model):
    _inherit = 'prescription.line'

    # @api.depends('quantity', 'price_unit', 'tax_ids')
    # def _compute_amount(self):
    #     """
    #     Compute the amounts of the line.
    #     """
    #     for line in self:
    #         if not line.display_type:
    #             price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
    #             taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, line.quantity, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)
    #             line.update({
    #                 'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
    #                 'price_total': taxes['total_included'],
    #                 'price_subtotal': taxes['total_excluded'],
    #             })
    #         else:
    #             line.price_tax = 0
    #             line.price_total = 0
    #             line.price_subtotal = 0

    def _compute_tax_id(self):
        for line in self:
            company_id = self.env.company
            line = line.with_company(company_id)
            fpos = line.prescription_id.fiscal_position_id or line.prescription_id.fiscal_position_id.get_fiscal_position(line.prescription_id.patient_id.partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company)
            line.tax_ids = fpos.map_tax(taxes)
    @api.onchange('product_id')
    def product_id_change(self):
        for rec in self:
            rec._compute_tax_id()

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids','discount_method','discount_amount')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        res_config= self.env.company
        for line in self:
            if res_config.tax_discount_policy_prescribtion_order:
                if res_config.tax_discount_policy_prescribtion_order == 'untax':
                    if line.discount_type == 'line':
                        if line.discount_method == 'fix':
                            price = (line.price_unit * line.quantity) - line.discount_amount
                            taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, 1, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'] + line.discount_amount,
                                'price_subtotal': taxes['total_excluded'] + line.discount_amount,
                                'discount_amt' : line.discount_amount,
                            })

                        elif line.discount_method == 'per':
                            price = (line.price_unit * line.quantity) * (1 - (line.discount_amount or 0.0) / 100.0)
                            price_x = ((line.price_unit * line.quantity) - (line.price_unit * line.quantity) * (1 - (line.discount_amount or 0.0) / 100.0))
                            taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, 1, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'] + price_x,
                                'price_subtotal': taxes['total_excluded'] + price_x,
                                'discount_amt' : price_x,
                            })
                        else:
                            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                            taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, line.quantity, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)
                            line.update({
                                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                                'price_total': taxes['total_included'],
                                'price_subtotal': taxes['total_excluded'],
                            })
                    else:
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, line.quantity, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)
                        line.update({
                            'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                            'price_total': taxes['total_included'],
                            'price_subtotal': taxes['total_excluded'],
                        })
                elif res_config.tax_discount_policy_prescribtion_order == 'tax':
                    if line.discount_type == 'line':
                        price_x = 0.0
                        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                        taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, line.quantity, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)

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
                        taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, line.quantity, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)
                        line.update({
                            'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                            'price_total': taxes['total_included'],
                            'price_subtotal': taxes['total_excluded'],
                        })
                else:
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, line.quantity, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)
                    
                    line.update({
                        'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                        'price_total': taxes['total_included'],
                        'price_subtotal': taxes['total_excluded'],
                    })
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(price, line.prescription_id.currency_id, line.quantity, product=line.product_id, partner=line.prescription_id.create_uid.partner_id)
                
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
    
    is_apply_on_discount_amount =  fields.Boolean("Tax Apply After Discount")
    discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method')
    discount_type = fields.Selection(related='prescription_id.discount_type', string="Discount Applies to")
    discount_amount = fields.Float('Discount Amount')
    discount_amt = fields.Float('Discount Final Amount')