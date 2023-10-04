from odoo import api, fields, models, _
from odoo.exceptions import AccessError,ValidationError


class CustomSaleOrderAutomation(models.Model):
    _name = "custom.sale.order.automation"

    _description = "Sale Order Automation"

    is_confirm_sale_order = fields.Boolean(string="Confirm Order", default=False)
    is_order_date_same_bill_date = fields.Boolean(string='Order Date Invoice Date', default=False)
    is_validate_incoming_shipment = fields.Boolean(string="Validate Shipment")
    is_create_vendor_bill = fields.Boolean(string='Create Customer Invoice', default=False)
    is_post_vendor_bill = fields.Boolean(string='Post Customer Invoice', default=False)
    is_paid_vendor_bill = fields.Boolean(string='Paid Payment', default=False)
    is_true_default = fields.Boolean(string='default Sale Order Automation', default=False)
    name = fields.Char(string='Name', size=64)
    
    sale_journal_id = fields.Many2one('account.journal', string='Sale Journal', domain=[('type', '=', 'sale')])
    journal_id = fields.Many2one('account.journal', string='Payment Journal', domain=[('type', 'in', ['cash', 'bank'])])
    outbound_payment_method_id = fields.Many2one('account.payment.method', string="Credit Method", domain=[('payment_type', '=', 'outbound')])

    @api.onchange("is_confirm_purchase_order")
    def onchange_confirm_sale_order(self):
        for record_id in self:
            if not record_id.is_confirm_sale_order:
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
    def custom_main_sale_order_automation_method(self, self_genrated_automation_id=False):
        sale_order_obj = self.env['sale.order']
        # custom_sale_order_automation_history_obj = self.env['custom.sale.order.automation.history']
        account_move_obj = self.env['account.move']
        account_payment_register_obj = self.env['account.payment.register']
        
        active_context_ids = self._context.get('sale_ids')
       
        print("this>>>>>>>>>>>>>>> ",active_context_ids)

        
        if not self_genrated_automation_id:
            sale_order_automation_ids = self.search([])
        else:
            sale_order_automation_ids = self.browse(self_genrated_automation_id)
        if not sale_order_automation_ids:
            return True
        for sale_order_automation_id in sale_order_automation_ids:
        
            if not active_context_ids:
                po_order_ids = sale_order_obj.search([('custom_sale_order_automation_id', '=', sale_order_automation_id.id), ('state', 'not in', ('done', 'cancel', 'sale')), ('invoice_status', '!=', 'invoiced')])
            else:
                po_order_ids = sale_order_obj.search([('custom_sale_order_automation_id', '=', sale_order_automation_id.id), ('id', 'in', active_context_ids)])
            print("this>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", po_order_ids)
            if not po_order_ids:
                continue
            
            for sale_order_id in po_order_ids:
                if sale_order_id.invoice_status and sale_order_id.invoice_status == 'invoiced':
                    continue

                # sale_order_automation_history_id = custom_sale_order_automation_history_obj.create_sale_order_automation_history()
                if sale_order_automation_id.is_confirm_sale_order:
                    try:
                        sale_order_id.action_confirm()
                        print("here im 2222222222")
                    except Exception as e:
                        print("jjjjjjjjjjjjjjjjjjjjjjjjjbuggggggggg")
                        # sale_order_automation_history_id.write({'mismatch_type': "sale", 'error_message': "Sale Order Confirmation Error Please Check in Details Order No %s \n  Error %s" % (sale_order_id.name, e)})
                        continue
              
                if sale_order_automation_id.is_validate_incoming_shipment:
                    try:
                         
                        for picking_id in sale_order_id.picking_ids.filtered(lambda p: p.state in ('draft', 'waiting', 'confirmed', 'assigned')):
                            for move_line_id in picking_id.move_lines:
                                move_line_id.quantity_done = move_line_id.product_uom_qty
                            picking_id.button_validate()

                    except Exception as e:
                        # sale_order_automation_history_id.write({'mismatch_type': "transfer", 'error_message': "Sale Order Shipment Validation Error Please Check in Details Order No %s \n  Error %s" % (purchase_order_id.name, e)})
                        continue

                if sale_order_automation_id.is_create_vendor_bill:
                    try:
                        # 'sale_id': sale_order_id.id,
                        invoice_vals = {'move_type': 'out_invoice', 'company_id': sale_order_id.company_id.id}
                        # print("this vals",invoice_vals)
                        if sale_order_automation_id.is_order_date_same_bill_date:
                            invoice_vals.update({'invoice_date': str(sale_order_id.date_order)})

                        if sale_order_automation_id.sale_journal_id.id:
                            invoice_vals.update({'journal_id': sale_order_automation_id.sale_journal_id.id})
                        else:
                            invoice_vals.update({'currency_id': sale_order_id.currency_id.id})
                        sale_order_id._create_invoices(invoice_vals)
                        # invoice_obj = account_move_obj.new(invoice_vals)
                        # invoice_obj._onchange_sale_auto_complete()
                        # invoice_obj._onchange_partner_id()
                        # invoice_obj._onchange_journal()
                        # invoice_obj._onchange_invoice_date()
                        # invoice_values = invoice_obj._convert_to_write(invoice_obj._cache)  
                        # create_invoice2 = account_move_obj._create_invoices(invoice_values)
                        # create_invoice_id = account_move_obj.create(invoice_values)

                    except Exception as e:
                        # sale_order_automation_history_id.write({'mismatch_type': "invoice", 'error_message': "Sale Order Create Vendor Bill Error Please Check in Details Order No %s \n  Error %s" % (purchase_order_id.name, e)})
                        continue
                if sale_order_automation_id.is_post_vendor_bill:
                    for invoice_id in sale_order_id.invoice_ids.filtered(lambda inv: inv.state == 'draft'):
                        try:
                            invoice_id.action_post()
                        except Exception as e:
                            # sale_order_automation_history_id.write({'mismatch_type': "invoice", 'error_message': "Sale Order Vendor Bill Validation Error Please Check in Details Order No %s \n  Error %s" % (purchase_order_id.name, e)})
                            continue

                        if sale_order_automation_id.is_paid_vendor_bill:
                            if invoice_id.amount_residual:
                                vals = {'journal_id': sale_order_automation_id.journal_id.id,
                                        'communication': invoice_id.name,
                                        'currency_id': invoice_id.currency_id.id,
                                        'payment_type': 'outbound',
                                        'partner_id': invoice_id.commercial_partner_id.id,
                                        'amount': invoice_id.amount_residual,
                                        'partner_type': 'supplier',
                                        'payment_method_id': sale_order_automation_id.outbound_payment_method_id.id}
                                account_payment_register_id = account_payment_register_obj.with_context({'active_model': 'account.move', 'active_ids': invoice_id.ids}).create(vals)
                                try:
                                    payment_id = account_payment_register_id.action_create_payments()
                                except Exception as e:
                                    # sale_order_automation_history_id.write({'mismatch_type': "invoice", 'error_message': "Sale Order Vendor Bill Payment Validation Error Please Check in Details Order No %s \n  Error %s" % (sale_order_id.name, e)})
                                    continue

        return True

class ResPartner(models.Model):
    _inherit = 'res.partner'
    #,default=_get_sale_order_automation
    def _get_sale_order_automation(self):
        return self.env['custom.sale.order.automation'].search([('is_true_default', '=', True)], limit=1).id
    is_auto_sale_order_automation = fields.Boolean(string="Set Sale Order Automation", default=True)
    custom_sale_order_automation_id = fields.Many2one('custom.sale.order.automation', string='Sale Order Automation',default=_get_sale_order_automation)


class AccountMove(models.Model):
    _inherit = 'account.move'
    sale_id = fields.Many2one('sale.order', store=False, readonly=True,
        states={'draft': [('readonly', False)]},
        string='Sale Order',
        help="Auto-complete from a past sale order.")
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    # sale_id = fields.Many2one('sale.order', store=False, readonly=True,
    #     states={'draft': [('readonly', False)]},
    #     string='Sale Order',
    #     help="Auto-complete from a past sale order.")
    
    
    
    # def action_confirm(self):
    #     if self.discount_type == 'global' and self.discount_method == ' ' :
    #         raise ValidationError(_('Pleas Enter Discount Method.'))
    #     if self.discount_type == 'line' and self.order_line.discount_method == ' ' :
    #         raise ValidationError(_('Pleas Enter Discount Method Peer Line.'))
    #     super(SaleOrder, self).action_confirm()


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id.is_auto_sale_order_automation:
            self.custom_sale_order_automation_id = self.partner_id.custom_sale_order_automation_id
        return res
    
    # test_f = fields.Char(string='field_name')
       
    custom_sale_order_automation_id = fields.Many2one('custom.sale.order.automation', string='Order Automation')
    # currency_base = fields.Many2one('res.currency','Currency', related='template_id.currency_id',readonly=True) 
    
    # test = fields.Char('test')
    
    
    # def _create_invoices(self, grouped=False, final=False):
    #     res = super(SaleOrder,self)._create_invoices(grouped=grouped, final=final)
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


    #     return res
    
    def action_sale_order_automation_method(self):
        # print("hello")
        for rec in self:
            if rec.discount_type == 'global':
                if not rec.discount_method:
                    raise ValidationError(_('Pleas Enter Discount Method.'))

            if rec.discount_type == 'line': 
              for line in rec.order_line:
                if not line.discount_method:
                    raise ValidationError(_('Pleas Enter Discount Method Peer Line.'))
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$4",rec.ids)
            rec.env['custom.sale.order.automation'].with_context({"sale_ids":rec.ids}).custom_main_sale_order_automation_method()
        




# class PurchaseOrder(models.Model):
#     _inherit = 'purchase.order'
    
#     ywt_purchase_order_automation_id = fields.Many2one('custom.sale.order.automation', string='Order Automation')

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     res = super(PurchaseOrder, self).onchange_partner_id()
    #     if self.partner_id.is_auto_purchase_order_automation:
    #         self.ywt_purchase_order_automation_id = self.partner_id.ywt_purchase_order_automation_id
    #     return res
      
    # def action_purchase_order_automation_method(self):
    #     self.env['ywt.purchase.order.automation'].with_context({"purchase_ids":self.ids}).ywt_main_purchase_order_automation_method()


#________________________________________________________





#______________________________________________________________

# class YWTPurchaseOrderAutomationHistory(models.Model):
#     _name = 'ywt.purchase.order.automation.history'
#     name = fields.Char(string="Name") 
#     mismatch_type = fields.Selection([('purchase', 'Purchase'), ('transfer', 'Transfer'), ('invoice', 'Invoice')], string="Mismatch Type")
#     error_message = fields.Text(string="Error Message")
    
#     def create_purchase_order_automation_history(self):
#         sequence_id = self.env.ref('ywt_purchase_order_automation.ywt_purchase_automation_history_sequence').ids
#         if sequence_id:
#             record_name = self.env['ir.sequence'].get_id(sequence_id[0])
#         else:
#             record_name = '/'
#         history_vals = {'name': record_name}
#         purchase_order_automation_history_id = self.create(history_vals)
#         return purchase_order_automation_history_id

# class CUSTOMSaleOrderAutomationHistory(models.Model):
#     _name = 'custom.sale.order.automation.history'
#     name = fields.Char(string="Name") 
#     mismatch_type = fields.Selection([('sale', 'Sale'), ('transfer', 'Transfer'), ('invoice', 'Invoice')], string="Mismatch Type")
#     error_message = fields.Text(string="Error Message")
    
#     def create_purchase_order_automation_history(self):
#         sequence_id = self.env.ref('sale_order_custom_automation.custom_sale_automation_history_sequence').ids
#         if sequence_id:
#             record_name = self.env['ir.sequence'].get_id(sequence_id[0])
#         else:
#             record_name = '/'
#         history_vals = {'name': record_name}
#         purchase_order_automation_history_id = self.create(history_vals)
#         return purchase_order_automation_history_id
#__________________________________________________________________

# class YWTPurchaseOrderAutomation(models.Model):
#     _name = "ywt.purchase.order.automation"

