# -*- coding: utf-8 -*-
# import json
# import time
# from ast import literal_eval
# from datetime import date, timedelta
# from itertools import groupby
# from operator import attrgetter, itemgetter
# from collections import defaultdict

# from odoo import SUPERUSER_ID, _, api, fields, models
# from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
# from odoo.exceptions import UserError
# from odoo.osv import expression
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
# from odoo.tools.float_utils import float_compare, float_is_zero, float_round
# from odoo.tools.misc import format_date
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
import uuid





#   'discount_type':line.discount_type,
#                 'discount_method': line.discount_method ,
#                 'discount_amount': line.discount_amount,
#                 'discount_amt' : line.discount_amt,
#   'discount_method': self.discount_method ,
#                 'discount_amount': self.discount_amount,
#                 'discount_amt' : self.discount_amt,
#    (0, 0, {'discount_amount': self.prescription_line_ids.discount_amount}),
#                  (0, 0, {'discount_amt': self.prescription_line_ids.discount_amt}),

class ACSPrescriptionOrder(models.Model):
    _inherit = 'prescription.order'
    

    # def create_invoice(self):
    #     # res = super(ACSPrescriptionOrder, self).create_invoice()
    #     if not self.prescription_line_ids:
    #         raise UserError(_("Please add prescription lines first."))

    #     if self.discount_type == 'global':
    #         if not self.discount_method:
    #             raise UserError(_('Pleas Enter Discount Method.'))

    #     if self.discount_type == 'line': 
    #         for line_pre in self.prescription_line_ids:
    #             if not line_pre.discount_method:
    #                 raise UserError(_('Pleas Enter Discount Method Peer Line.'))
    #     product_data = []
    #     for line in self.prescription_line_ids:
    #         product_data.append({
    #             'product_id': line.product_id,
    #             'quantity': line.quantity,
    #             'name': line.name,
    #             'display_type': line.display_type,
    #             'discount': 0.0,
    #             'discount_method': line.discount_method,
    #             'discount_amount': line.discount_amount,
    #             'discount_amt': line.discount_amt,
    #             'tax_ids':line.tax_ids.ids
                
    #         })
    #     print('>>>>>>>>>>>>>>>>>pp>>>>>',product_data)
                         
    #     inv_data = {
    #         'physician_id': self.physician_id and self.physician_id.id or False,
    #         'hospital_invoice_type': 'pharmacy',
    #         'discount_method': self.discount_method,
    #         'discount_amount': self.discount_amount,
    #          'discount_amt': self.discount_amt,
    #         'discount_amt_line' : self.discount_amt_line,
    #         'discount_amount_line':self.discount_amt_line,
    #          'discount_type': self.discount_type,
            
    #     }
    #     invoice = self.acs_create_invoice(partner=self.patient_id.partner_id, patient=self.patient_id, product_data=product_data, inv_data=inv_data)
    #     now_data_dis =[]
    #     # if self.discount_type == 'line' or self.discount_type == 'global': 
    #     # for dis_now in self.prescription_line_ids:
    #     #     line_prescription_now = (1, invoice.invoice_line_ids.id,{'discount_method': dis_now.discount_method,
    #     #                         'discount_amount': dis_now.discount_amount,
    #     #                         'discount_amt': dis_now.discount_amt
    #     #                         })
    #     #     line_prescription_now = (1,0,{'discount_method': dis_now.discount_method,
    #     #                         'discount_amount': dis_now.discount_amount,
    #     #                         'discount_amt': dis_now.discount_amt
    #     #                         })
    #     #     now_data_dis.append(line_prescription_now)

    #     invoice.write({
    #             'create_stock_moves': False if self.deliverd else True,
    #             'prescription_id': self.id,
    #             'discount_method': self.discount_method,
    #             'discount_amount': self.discount_amount,
    #             'discount_amt': self.discount_amt,
    #             'discount_amt_line' : self.discount_amt_line,
    #             'discount_amount_line':self.discount_amt_line,
    #             'discount_type': self.discount_type,
    #             # 'invoice_line_ids':now_data_dis
    #     })
    #     self.sudo().invoice_id = invoice.id
    #     # else:
    #         # for dis_now in self.prescription_line_ids:
    #         # line_prescription_now = (1, invoice.invoice_line_ids.id,{'discount_method': dis_now.discount_method,
    #         #                     'discount_amount': dis_now.discount_amount,
    #         #                     'discount_amt': dis_now.discount_amt
    #         #                     })
    #             # line_prescription_now = (1,0,{'discount_method': None,
    #             #                 'discount_amount': 0.0,
    #             #                 'discount_amt': 0.0
    #             #                 })
    #             # now_data_dis.append(line_prescription_now)
    #         # invoice.write({
    #         #     'create_stock_moves': False if self.deliverd else True,
    #         #     'prescription_id': self.id,
    #         #     'discount_type': self.discount_type,
    #             # 'discount_method': None,
    #             # 'discount_amount': 0.0,
    #             # 'discount_amt': 0.0,
    #             # 'discount_amt_line' : 0.0,
    #             # 'discount_amount_line':now_data_dis
    #         # })
    #         # self.sudo().invoice_id = invoice.id
    #     # return res

    def button_confirm(self):
        res = super(ACSPrescriptionOrder, self).button_confirm()
        for order in self:
            # warehouse = order.warehouse_id
            order.acs_create_delivery()
            
            if order.picking_ids: 
                for picking in self.picking_ids:
                    picking.action_assign()
                    picking.action_set_quantities_to_reservation() 
                    picking.action_confirm()
                    for move_line_id in picking.move_lines:
                        move_line_id.quantity_done = move_line_id.product_uom_qty
                  
                    picking.button_validate()
                    
                       
            
            # order.create_invoice()
            if not order.invoice_id:
                order.create_invoice()
            # if order.invoice_id:
            #     for invoice in order.invoice_id:
            #         invoice.action_post()
          

        return res  

    


        




class HmsTreatment(models.Model):
    _inherit = 'hms.treatment'
    mobile_treatment = fields.Char(related='patient_id.mobile',string='mobile')



class Appointment(models.Model):
    _inherit = 'hms.appointment'
    mobile_appointment = fields.Char(related='patient_id.mobile',string='mobile')





# class Picking(models.Model):
#     _inherit = 'stock.picking'

#     def button_validate(self):
#         # Clean-up the context key at validation to avoid forcing the creation of immediate
#         # transfers.
#         ctx = dict(self.env.context)
#         ctx.pop('default_immediate_transfer', None)
#         self = self.with_context(ctx)

#         # Sanity checks.
#         pickings_without_moves = self.browse()
#         pickings_without_quantities = self.browse()
#         pickings_without_lots = self.browse()
#         products_without_lots = self.env['product.product']
#         for picking in self:
#             for picking_tow in picking.move_ids_without_package:
#                 picking_tow.quantity_done = picking_tow.product_uom_qty
#             if not picking.move_lines and not picking.move_line_ids:
#                 pickings_without_moves |= picking

#             picking.message_subscribe([self.env.user.partner_id.id])
#             picking_type = picking.picking_type_id
#             precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
#             # no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
#             # no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
#             # if no_reserved_quantities and no_quantities_done:
#             #     pickings_without_quantities |= picking

#             if picking_type.use_create_lots or picking_type.use_existing_lots:
#                 lines_to_check = picking.move_line_ids
#                 # if not no_quantities_done:
#                     # lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
#                 for line in lines_to_check:
#                     product = line.product_id
#                     if product and product.tracking != 'none':
#                         if not line.lot_name and not line.lot_id:
#                             pickings_without_lots |= picking
#                             products_without_lots |= product

#         if not self._should_show_transfers():
#             if pickings_without_moves:
#                 raise UserError(_('Please add some items to move.'))
#             # if pickings_without_quantities:
#             #     raise UserError(self._get_without_quantities_error_message())
#             if pickings_without_lots:
#                 raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(products_without_lots.mapped('display_name')))
#         else:
#             message = ""
#             if pickings_without_moves:
#                 message += _('Transfers %s: Please add some items to move.') % ', '.join(pickings_without_moves.mapped('name'))
#             # if pickings_without_quantities:
#             #     message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(pickings_without_quantities.mapped('name'))
#             if pickings_without_lots:
#                 message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
#             if message:
#                 raise UserError(message.lstrip())

#         # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
#         # moves and/or the context and never call `_action_done`.
#         if not self.env.context.get('button_validate_picking_ids'):
#             self = self.with_context(button_validate_picking_ids=self.ids)
#         res = self._pre_action_done_hook()
#         if res is not True:
#             return res

#         # Call `_action_done`.
#         if self.env.context.get('picking_ids_not_to_backorder'):
#             pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
#             pickings_to_backorder = self - pickings_not_to_backorder
#         else:
#             pickings_not_to_backorder = self.env['stock.picking']
#             pickings_to_backorder = self
#         pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
#         pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

#         if self.user_has_groups('stock.group_reception_report') \
#                 and self.user_has_groups('stock.group_auto_reception_report') \
#                 and self.filtered(lambda p: p.picking_type_id.code != 'outgoing'):
#             lines = self.move_lines.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
#             if lines:
#                 # don't show reception report if all already assigned/nothing to assign
#                 wh_location_ids = self.env['stock.location']._search([('id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id), ('usage', '!=', 'supplier')])
#                 if self.env['stock.move'].search([
#                         ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
#                         ('product_qty', '>', 0),
#                         ('location_id', 'in', wh_location_ids),
#                         ('move_orig_ids', '=', False),
#                         ('picking_id', 'not in', self.ids),
#                         ('product_id', 'in', lines.product_id.ids)], limit=1):
#                     action = self.action_view_reception_report()
#                     action['context'] = {'default_picking_ids': self.ids}
#                     return action
#         return True