# -*- coding: utf-8 -*-pack
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    def _get_purchase_order_automation(self):
        return self.env['ywt.purchase.order.automation'].search([('is_true_default', '=', True)], limit=1).id
    is_auto_purchase_order_automation = fields.Boolean(string="Set Purchase Order Automation", default=True)
    ywt_purchase_order_automation_id = fields.Many2one('ywt.purchase.order.automation', string='Purchase Order Automation',default=_get_purchase_order_automation)


    

        # if is_auto_purchase_order_automation == True:

        # default=_get_default_journal



        #     active_default_id = self.env['ywt.purchase.order.automation'].search([('is_true_default','=',True)]).id
        #     ywt_purchase_order_automation_id = active_default_id
    
    # def (self):
    #     act_model = self.env.context.get('active_model')
    #     active_model_id = self.env['ir.model'].search([('name','=',act_model)]).id
    #     filtered_report = self.env['ir.actions.report'].search([('binding_model_id','=',active_model_id)], limit=1)



   
    # def _default_head_branch(self):

    #      return self.env['head.branch'].search([('name', '=', 'Head/Branch')], limit=1).id

    #  head_branch=fields.Many2one('head.branch', string='Head/Branch', index=True, ondelete='cascade', default=_default_head_branch)