# -*- coding: utf-8 -*-pack
from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    ywt_purchase_order_automation_id = fields.Many2one('ywt.purchase.order.automation', string='Order Automation')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()
        if self.partner_id.is_auto_purchase_order_automation:
            self.ywt_purchase_order_automation_id = self.partner_id.ywt_purchase_order_automation_id
        return res
      
    def action_purchase_order_automation_method(self):
        self.env['ywt.purchase.order.automation'].with_context({"purchase_ids":self.ids}).ywt_main_purchase_order_automation_method()
