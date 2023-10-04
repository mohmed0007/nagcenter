# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError, ValidationError


class account_move(models.Model):
	_inherit = 'account.move'
   
	def calc_discount(self):
		for calculate in self:
			calculate._calculate_discount()

	@api.depends('discount_amount')
	def _calculate_discount(self):
		res = discount = 0.0
		res_config= self.env.company
		if res_config.tax_discount_policy:
			for self_obj in self:
				if self_obj.discount_type == 'global':
					if self_obj.discount_method == 'fix':
						res = self_obj.discount_amount
					elif self_obj.discount_method == 'per':
						res = self_obj.amount_untaxed * (self_obj.discount_amount/ 100)
	
				else:
					res = discount

		return res

	@api.depends(
		'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
		'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
		'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
		'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
		'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
		'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
		'line_ids.debit',
		'line_ids.credit',
		'line_ids.currency_id',
		'line_ids.amount_currency',
		'line_ids.amount_residual',
		'line_ids.amount_residual_currency',
		'line_ids.payment_id.state',
		'line_ids.full_reconcile_id','discount_method','discount_amount','discount_amount_line')
	def _compute_amount(self):
		for move in self:

			if move.payment_state == 'invoicing_legacy':
				move.payment_state = move.payment_state
				continue

			total_untaxed = 0.0
			total_untaxed_currency = 0.0
			total_tax = 0.0
			total_tax_currency = 0.0
			total_to_pay = 0.0
			total_residual = 0.0
			total_residual_currency = 0.0
			total = 0.0
			total_currency = 0.0
			currencies = move._get_lines_onchange_currency().currency_id

			for line in move.line_ids:
				if move.is_invoice(include_receipts=True):

					if not line.exclude_from_invoice_tab:
						
						total_untaxed += line.balance
						total_untaxed_currency += line.amount_currency
						total += line.balance
						total_currency += line.amount_currency
					elif line.tax_line_id:
						total_tax += abs(line.balance)
						total_tax_currency += line.amount_currency
						total += line.balance
						total_currency += line.amount_currency
					elif line.account_id.user_type_id.type in ('receivable', 'payable'):
						total_to_pay += line.balance
						total_residual += line.amount_residual
						total_residual_currency += line.amount_residual_currency
				else:
					if line.debit:
						total += line.balance
						total_currency += line.amount_currency

			if move.move_type == 'entry' or move.is_outbound():
				sign = 1
			else:
				sign = -1
			move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
			move.amount_tax = abs(sign * (total_tax_currency if len(currencies) == 1 else total_tax))
			move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
			move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
			move.amount_untaxed_signed = total_untaxed
			print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAM",total_tax)
			move.amount_tax_signed = total_tax
			move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
			move.amount_residual_signed = total_residual

			currency = len(currencies) == 1 and currencies or move.company_id.currency_id
			new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

			if move.is_invoice(include_receipts=True) and move.state == 'posted':

				if currency.is_zero(move.amount_residual):
					reconciled_payments = move._get_reconciled_payments()
					if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
						new_pmt_state = 'paid'
					else:
						new_pmt_state = move._get_invoice_in_payment_state()
				elif currency.compare_amounts(total_to_pay, total_residual) != 0:
					new_pmt_state = 'partial'

			if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
				reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
				reverse_moves = self.env['account.move'].search([('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])
				reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
				if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
					new_pmt_state = 'reversed'

			move.payment_state = new_pmt_state
			res = move._calculate_discount()
			move.discount_amt = res
			move.amount_total = move.amount_untaxed - res + move.amount_tax


		res_config= self.env.company
		if res_config.tax_discount_policy:
			for rec in self:
				if res_config.tax_discount_policy == 'tax':
					if rec.discount_type == 'line':
						rec.discount_amt = 0.00
						total = 0
						if self._context.get('default_move_type') == 'out_invoice' :
							if rec.discount_amount_line > 0.0:
								rec.discount_amt_line = rec.discount_amount_line
							else:
								rec.discount_amt_line = 0.0

						rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.discount_amt_line
						rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total)
					elif rec.discount_type == 'global':
						if rec.discount_method == 'fix':
							rec.discount_amt = rec.discount_amount
							rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.discount_amt
							rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total)
						elif rec.discount_method == 'per':
							rec.discount_amt = (rec.amount_untaxed) * (rec.discount_amount / 100.0)
							rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.discount_amt
							rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total)
						else:
							rec.amount_total = rec.amount_tax + rec.amount_untaxed
							rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total)
					else:
						rec.amount_total = rec.amount_tax + rec.amount_untaxed
						rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total)
				elif res_config.tax_discount_policy == 'untax':
					sums = 0.00
					if rec.discount_type == 'line':
						total = 0
						if self._context.get('default_move_type') == 'out_invoice' :
							if rec.discount_amount_line > 0.0:
								rec.discount_amt_line = rec.discount_amount_line
							else:
								rec.discount_amt_line = 0.0
						rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.discount_amt_line        
						rec.discount_amt = 0.00   
					elif rec.discount_type == 'global':
						if rec.discount_method == 'fix':
							sums =0
							if rec.invoice_line_ids:
								for line in rec.invoice_line_ids:
									if line.tax_ids:
										if rec.amount_untaxed:
											final_discount = ((rec.discount_amt*line.price_subtotal)/rec.amount_untaxed)
											discount = line.price_subtotal - final_discount
											taxes = line.tax_ids.compute_all(discount, rec.currency_id, 1.0,
																			line.product_id,rec.partner_id)
											sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
							rec.amount_tax = sums				
							rec.amount_total = sums + rec.amount_untaxed - rec.discount_amt
							rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total)
					
						elif rec.discount_method == 'per':
							sums = 0
							print("LLLLLLLLLLLLLLLLLpercetage")
							if rec.invoice_line_ids:
								for line in rec.invoice_line_ids:
									if line.tax_ids:
										final_discount = ((rec.discount_amount*line.price_subtotal)/100.0)
										discount = line.price_subtotal - final_discount
										taxes = line.tax_ids.compute_all(discount, rec.currency_id, 1.0,
																		line.product_id,rec.partner_id)
										sums += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
							rec.amount_tax =  sums
							rec.amount_total = sums + rec.amount_untaxed - rec.discount_amt
							rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total)
						else:
							print("in else 1")
							rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.discount_amt  
							rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total)  
					else:
						print("in else 2 >>>>>>",rec.discount_type)
						rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.discount_amt
						rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total)
				else:
					print("in else 3")
					rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.discount_amt   
					rec.amount_total_signed = abs(rec.amount_total) if move.move_type == 'entry' else sign * (-rec.amount_total) 

				for record in self:
					for line in record.invoice_line_ids:
						if line.product_id:
							rec.discount_account_id = line.account_id.id 
   

	def _compute_amount_account(self):
		for record in self:
			for line in record.invoice_line_ids:
				if line.product_id:
					record.discount_account_id = line.account_id.id 

	discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')],'Discount Method',default='fix')
	discount_amount = fields.Float('Discount Amount')
	discount_amt = fields.Float(string='Discount', readonly=True, compute='_compute_amount')
	amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, tracking=True,
		compute='_compute_amount')
	amount_tax = fields.Monetary(string='Tax', store=True, readonly=True,
		compute='_compute_amount')
	amount_total = fields.Monetary(string='Total', store=True, readonly=True,
		compute='_compute_amount',
		inverse='_inverse_amount_total')
	discount_type = fields.Selection([('line', 'Order Line'), ('global', 'Global'),('non_discount','No Discount')], 'Discount Applies to',default='non_discount')
	discount_account_id = fields.Many2one('account.account', 'Discount Account',compute='_compute_amount_account',store=True)
	discount_amt_line = fields.Float(compute='_compute_amount', string='Line Discount', digits='Discount', store=True, readonly=True)
	discount_amount_line = fields.Float(string="Discount Line")
   


	# def _recompute_tax_lines(self, recompute_tax_base_amount=False):

	# 	self.ensure_one()
	# 	in_draft_mode = self != self._origin
        
	# 	def _serialize_tax_grouping_key(grouping_dict):
	# 		return '-'.join(str(v) for v in grouping_dict.values())

	# 	def _compute_base_line_taxes(base_line):
	# 		print("88888888888888888888")
	# 		move = base_line.move_id

	# 		if move.is_invoice(include_receipts=True):
	# 			handle_price_include = True
	# 			sign = -1 if move.is_inbound() else 1
	# 			quantity = base_line.quantity
	# 			is_refund = move.move_type in ('out_refund', 'in_refund')
	# 			price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
	# 		else:
	# 			handle_price_include = False
	# 			quantity = 1.0
	# 			tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
	# 			is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
	# 			price_unit_wo_discount = base_line.amount_currency

	# 		res_config= self.env.company
	# 		if res_config.tax_discount_policy:
	# 			for rec in self:
	# 				if res_config.tax_discount_policy == 'untax':
	# 					if rec.discount_type == 'line':
	# 						if base_line.discount_method == 'fix':
	# 							price_unit_wo_discount = base_line.price_subtotal - base_line.discount_amount
	# 						elif base_line.discount_method == 'per':
	# 							price_unit_wo_discount = base_line.price_subtotal * (1 - (base_line.discount_amount / 100.0))
	# 						else:
	# 							price_unit_wo_discount = -(price_unit_wo_discount)    

	# 					elif rec.discount_type == 'global' or rec.discount_type == 'non_discount':
	# 						# if rec.discount_method != False:
	# 							if rec.amount_untaxed != 0.0:
	# 								final_discount = ((rec.discount_amt*base_line.price_subtotal)/rec.amount_untaxed)
	# 								price_unit_wo_discount = base_line.price_subtotal - rec.currency_id.round(final_discount)
	# 								quantity = 1.0
	# 							else:
	# 								print("MMMMMMMMMMMMMMMMMMherererererer")
	# 								final_discount = (rec.discount_amt*base_line.price_subtotal)/1.0
	# 								discount = base_line.price_subtotal - rec.currency_id.round(final_discount)
	# 						# else:
	# 							# price_unit_wo_discount = (price_unit_wo_discount)                 
	# 				else:
	# 					if self._context.get('default_move_type') in ('out_invoice','out_refund','out_receipt'):
	# 						if self.discount_amt > 0:
	# 						    sign = -(sign)
	# 					else:
	# 						pass
	# 			print(">>>>>>>>>>>>>>>>>>>>>>>>>>sign",sign)
	# 			print(">>>>>>>>>>>>>>>>>>>>>>>>>> ttotoot",sign*price_unit_wo_discount)
	# 			price_unit_wo_discount = sign*price_unit_wo_discount        

	# 		balance_taxes_res = base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
	# 			price_unit_wo_discount,
	# 			currency=base_line.currency_id,
	# 			quantity=quantity,
	# 			product=base_line.product_id,
	# 			partner=base_line.partner_id,
	# 			is_refund=is_refund,
	# 			handle_price_include=handle_price_include,
	# 		)
	# 		print("####################################refund",balance_taxes_res)

	# 		if move.move_type == 'entry':
	# 			repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
	# 			repartition_tags = base_line.tax_ids.flatten_taxes_hierarchy().mapped(repartition_field).filtered(lambda x: x.repartition_type == 'base').tag_ids
	# 			tags_need_inversion = (tax_type == 'sale' and not is_refund) or (tax_type == 'purchase' and is_refund)
	# 			if tags_need_inversion:
	# 				balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
	# 				for tax_res in balance_taxes_res['taxes']:
	# 					tax_res['tag_ids'] = base_line._revert_signed_tags(self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

	# 		return balance_taxes_res

	# 	taxes_map = {}

	# 	to_remove = self.env['account.move.line']
	# 	for line in self.line_ids.filtered('tax_repartition_line_id'):
	# 		grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
	# 		grouping_key = _serialize_tax_grouping_key(grouping_dict)
	# 		if grouping_key in taxes_map:
	# 			to_remove += line
	# 		else:
	# 			taxes_map[grouping_key] = {
	# 				'tax_line': line,
	# 				'amount': 0.0,
	# 				'tax_base_amount': 0.0,
	# 				'grouping_dict': False,
	# 			}
	# 	if not recompute_tax_base_amount:
	# 		self.line_ids -= to_remove

	# 	for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
	# 		if not line.tax_ids:
	# 			if not recompute_tax_base_amount:
	# 				line.tax_tag_ids = [(5, 0, 0)]
	# 			continue

	# 		compute_all_vals = _compute_base_line_taxes(line)

	# 		if not recompute_tax_base_amount:
	# 			line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

	# 		for tax_vals in compute_all_vals['taxes']:
	# 			grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
	# 			grouping_key = _serialize_tax_grouping_key(grouping_dict)

	# 			tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
	# 			tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

	# 			taxes_map_entry = taxes_map.setdefault(grouping_key, {
	# 				'tax_line': None,
	# 				'amount': 0.0,
	# 				'tax_base_amount': 0.0,
	# 				'grouping_dict': False,
	# 			})
	# 			taxes_map_entry['amount'] += tax_vals['amount']
	# 			taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
	# 			taxes_map_entry['grouping_dict'] = grouping_dict

	# 	for taxes_map_entry in taxes_map.values():
	# 		if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
	# 			if not recompute_tax_base_amount:
	# 				self.line_ids -= taxes_map_entry['tax_line']
	# 			continue

	# 		currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

	# 		if currency.is_zero(taxes_map_entry['amount']):
	# 			if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
	# 				self.line_ids -= taxes_map_entry['tax_line']
	# 			continue

	# 		tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

	# 		if recompute_tax_base_amount:
	# 			if taxes_map_entry['tax_line']:
	# 				taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
	# 			continue

	# 		balance = currency._convert(
	# 			taxes_map_entry['amount'],
	# 			self.company_currency_id,
	# 			self.company_id,
	# 			self.date or fields.Date.context_today(self),
	# 		)
	# 		print(">>>>>>>>>>>>>>>>>>>>>>>>group",balance)
	# 		to_write_on_line = {
	# 			'amount_currency': taxes_map_entry['amount'],
	# 			'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
	# 			'debit': balance > 0.0 and balance or 0.0,
	# 			'credit': balance < 0.0 and -balance or 0.0,
	# 			'tax_base_amount': tax_base_amount,
	# 		}

	# 		if taxes_map_entry['tax_line']:
	# 			taxes_map_entry['tax_line'].update(to_write_on_line)
	# 		else:
	# 			create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
	# 			tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
	# 			tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
	# 			tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
	# 			taxes_map_entry['tax_line'] = create_method({
	# 				**to_write_on_line,
	# 				'name': tax.name,
	# 				'move_id': self.id,
	# 				'partner_id': line.partner_id.id,
	# 				'company_id': line.company_id.id,
	# 				'company_currency_id': line.company_currency_id.id,
	# 				'tax_base_amount': tax_base_amount,
	# 				'exclude_from_invoice_tab': True,
	# 				**taxes_map_entry['grouping_dict'],
	# 			})

	# 		if in_draft_mode:
	# 			taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))
	
	def _recompute_tax_lines(self, recompute_tax_base_amount=False):
		""" Compute the dynamic tax lines of the journal entry.

        :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
        """
		self.ensure_one()
		in_draft_mode = self != self._origin

		def _serialize_tax_grouping_key(grouping_dict):
			''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
			return '-'.join(str(v) for v in grouping_dict.values())

		def _compute_base_line_taxes(base_line):
			''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
			move = base_line.move_id

			if move.is_invoice(include_receipts=True):
				handle_price_include = True
				sign = -1 if move.is_inbound() else 1
				quantity = base_line.quantity
				is_refund = move.move_type in ('out_refund', 'in_refund')
				price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
			else:
				handle_price_include = False
				quantity = 1.0
				tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
				is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
				price_unit_wo_discount = base_line.amount_currency

			res_config= self.env.company
			if res_config.tax_discount_policy:
				for rec in self:
					if res_config.tax_discount_policy == 'untax':
						if rec.discount_type == 'line':
							if base_line.discount_method == 'fix':
								price_unit_wo_discount = base_line.price_subtotal - base_line.discount_amount
							elif base_line.discount_method == 'per':
								price_unit_wo_discount = base_line.price_subtotal * (1 - (base_line.discount_amount / 100.0))
							else:
								price_unit_wo_discount = -(price_unit_wo_discount)    

						elif rec.discount_type == 'global' or rec.discount_type == 'non_discount':
							# if rec.discount_method != False and rec.discount_amount != False:
								if rec.amount_untaxed != 0.0:
									final_discount = ((rec.discount_amt*base_line.price_subtotal)/rec.amount_untaxed)
									price_unit_wo_discount = base_line.price_subtotal - rec.currency_id.round(final_discount)
									quantity = 1.0
								else:
									final_discount = (rec.discount_amt*base_line.price_subtotal)/1.0
									discount = base_line.price_subtotal - rec.currency_id.round(final_discount)
							# else:
								# price_unit_wo_discount = (price_unit_wo_discount)                 
					else:
						if self._context.get('default_move_type') in ('out_invoice','out_refund','out_receipt'):
							sign = -(sign)
						else:
							pass

				price_unit_wo_discount = sign*price_unit_wo_discount


			return base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
				price_unit_wo_discount,
				currency=base_line.currency_id,
				quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=move.always_tax_exigible,
            )

		taxes_map = {}

        # ==== Add tax lines ====
		to_remove = self.env['account.move.line']
		for line in self.line_ids.filtered('tax_repartition_line_id'):
			grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
			grouping_key = _serialize_tax_grouping_key(grouping_dict)
			if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
				to_remove += line
			else:
				taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
		if not recompute_tax_base_amount:
			self.line_ids -= to_remove

        # ==== Mount base lines ====
		for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
			if not line.tax_ids:
				if not recompute_tax_base_amount:
					line.tax_tag_ids = [(5, 0, 0)]
				continue

			compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
			if not recompute_tax_base_amount:
				line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

			for tax_vals in compute_all_vals['taxes']:
				grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
				grouping_key = _serialize_tax_grouping_key(grouping_dict)

				tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
				tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

				taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
				taxes_map_entry['amount'] += tax_vals['amount']
				taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
				taxes_map_entry['grouping_dict'] = grouping_dict

        # ==== Pre-process taxes_map ====
		taxes_map = self._preprocess_taxes_map(taxes_map)

        # ==== Process taxes_map ====
		for taxes_map_entry in taxes_map.values():
            # The tax line is no longer used in any base lines, drop it.
			if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
				if not recompute_tax_base_amount:
					self.line_ids -= taxes_map_entry['tax_line']
				continue

			currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

            # tax_base_amount field is expressed using the company currency.
			tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

            # Recompute only the tax_base_amount.
			if recompute_tax_base_amount:
				if taxes_map_entry['tax_line']:
					taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
				continue

			balance = currency._convert(
				taxes_map_entry['amount'],
				self.company_currency_id,
				self.company_id,
				self.date or fields.Date.context_today(self),
            )
			to_write_on_line = {
                'amount_currency': taxes_map_entry['amount'],
                'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
                'tax_base_amount': tax_base_amount,	}

			if taxes_map_entry['tax_line']:
                # Update an existing tax line.
				taxes_map_entry['tax_line'].update(to_write_on_line)
			else:
                # Create a new tax line.
				create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
				tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
				tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
				tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
				taxes_map_entry['tax_line'] = create_method({
                    **to_write_on_line,
                    'name': tax.name,
                    'move_id': self.id,
                    'company_id': line.company_id.id,
                    'company_currency_id': line.company_currency_id.id,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    **taxes_map_entry['grouping_dict'],
                })
			if in_draft_mode:
				taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))

	@api.model_create_multi
	def create(self, vals_list):
		res = super(account_move,self).create(vals_list)
		settings= self.env.company

		tax_discount_policy = settings.tax_discount_policy;
		if not tax_discount_policy and res.discount_amt == 0:
			return res
		if len(vals_list):
			obj = self.env["account.move"].search([("name","=",vals_list[0])]);
		name_flag = False;
		
		print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#",self.discount_type)
		for line in self.line_ids:
			if line.name == "Discount":
				name_flag = True;
		if self.discount_type == 'line':
			price = self.discount_amt_line
		elif self.discount_type == 'global':
			price = self.discount_amt
		else:
			price = 0  
		move_line = res.line_ids.filtered(lambda x : x.name == 'Discount')
		if not len(res) > 1:
			if not name_flag and res.move_type != 'entry':
				if not move_line:
					# if res.discount_type != 'non_discount':
					if res.discount_account_id:       
						discount_vals = {
								'account_id': res.discount_account_id, 
								'quantity': 1,
								'price_unit': -price,
								'name': "Discount", 
								'exclude_from_invoice_tab': True,
								} 
						res.with_context(check_move_validity=False).write({
								'invoice_line_ids' : [(0,0,discount_vals)]
								})
				else:
					pass   
		# res._compute_amount() 
		return res

	@api.onchange('invoice_line_ids','discount_amount','discount_method')
	def _onchange_invoice_line_ids_discount(self):
		for res in self:
			res._compute_amount()
			if res.move_type != "entry":
				if res.discount_type and (res.discount_method in ["fix","per"] and res.discount_amount != 0 \
					or any(l.discount_method in ["fix","per"] and l.discount_amount != 0 for l in res.invoice_line_ids)):
					
					line = res.line_ids.filtered(lambda s: s.name == "Discount");
					
					if res.discount_type == 'line':
						price = res.discount_amt_line
					elif res.discount_type == 'global':
						price = res.discount_amt
					else:
						price = 0  
					
					if len(line or []) == 0:
						if res.discount_account_id:       
							discount_vals = {
									'account_id': res.discount_account_id, 
									'quantity': 1,
									'price_unit': -price,
									'name': "Discount", 
									'exclude_from_invoice_tab': True,
								}    
							res.with_context(check_move_validity=False).update({
									'invoice_line_ids' : [(0,0,discount_vals)]
									})
						else:
							pass
			

		if res.discount_type and (res.discount_method in ["fix","per"] and res.discount_amount != 0 \
					or any(l.discount_method in ["fix","per"] and l.discount_amount > 0 for l in res.invoice_line_ids)):
			
			if self.discount_type == 'line':
				price = self.discount_amt_line
			elif self.discount_type == 'global':
				price = self.discount_amt
			else:
				price = 0
			for rec in self.line_ids:
				if self._context.get('default_move_type') in ('out_invoice','in_refund'):
					if rec.name == "Discount":
						rec.with_context(check_move_validity=False).write({'debit':price})
					if rec.name == False or rec.name == '' or rec.name == self.name:
						rec.with_context(check_move_validity=False).write({'debit':self.amount_total})
				
				elif self._context.get('default_move_type') in ('in_invoice','out_refund'):
					if rec.name == "Discount":
						rec.with_context(check_move_validity=False).write({'credit':price})
					if rec.name == False or rec.name == '' or rec.name == self.name:
						rec.with_context(check_move_validity=False).write({'credit':self.amount_total})
				else:
					pass

	@api.onchange('invoice_line_ids','discount_amount','discount_method','invoice_line_ids.discount_amount')
	def _onchange_invoice_line_ids(self):
		current_invoice_lines = self.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)
		others_lines = self.line_ids - current_invoice_lines
		if others_lines and current_invoice_lines - self.invoice_line_ids:
			others_lines[0].recompute_tax_line = True
		self.line_ids = others_lines + self.invoice_line_ids
		self._onchange_recompute_dynamic_lines() 
		if self._context.get('default_move_type') == 'out_invoice' :
			total = 0.0
			for line in self.invoice_line_ids:
				if line.discount_method == 'per':
					total += line.price_subtotal * (line.discount_amount/ 100)
				elif line.discount_method == 'fix':
					total += line.discount_amount
			self.discount_amount_line = total
	

	@api.depends('discount_amount','discount_method')
	def write(self,vals):

		res = super(account_move,self).write(vals)
		for move in self:
			for rec in move.line_ids:
				if move._context.get('default_move_type') == 'out_invoice' :
					if move.discount_type != 'line':
						if rec.name == "Discount":
							if rec.move_id.discount_amt > 0.0:
								rec.with_context(check_move_validity=False).write({'price_unit':-move.discount_amt})
							# else:
								# rec.unlink()

				if move._context.get('default_move_type') == 'out_invoice' :
					amount_total = move.amount_tax + move.amount_untaxed - move.discount_amount_line

					if move.discount_type == 'line':
						if rec.name == "Discount":
							if move.discount_amount_line > 0.0:
								rec.with_context(check_move_validity=False).write({'debit':move.discount_amount_line})
								rec.with_context(check_move_validity=False).write({'credit':0.0})
							else:
								rec.with_context(check_move_validity=False).write({'debit':0.0})
								rec.unlink()
						if rec.name == False or rec.name == '' or rec.name == move.name:
							rec.with_context(check_move_validity=False).write({'debit':amount_total})


					else:
						if rec.name == False or rec.name == '' or rec.name == move.name:
							rec.with_context(check_move_validity=False).write({'debit':move.amount_total})

				else:
					pass  

		return res  
	@api.onchange('discount_amount','discount_method')
	def _onchange_taxes(self):
		for line in self.line_ids:
			if not line.tax_repartition_line_id:
				line.recompute_tax_line = True
		self._recompute_dynamic_lines()


class account_move_line(models.Model):
	_inherit = 'account.move.line'
 
	discount_method = fields.Selection([('fix', 'Fixed'), ('per', 'Percentage')], 'Discount Method')
	discount_type = fields.Selection(related='move_id.discount_type', string="Discount Applies to")
	discount_amount = fields.Float('Discount Amount')
	discount_amt = fields.Float('Discount Final Amount')
	flag = fields.Boolean("Flag")

	@api.onchange('discount_method','discount_amount','amount_currency', 'currency_id', 'debit', 'credit', 'tax_ids', 'account_id',)
	def _onchange_mark_recompute_taxes(self):
		for line in self:
			if not line.tax_repartition_line_id:
				line.recompute_tax_line = True

