
from odoo import models, fields, api

class AccountMoveLine(models.Model):
        _inherit = "account.move.line"
        cate = fields.Many2one('product.category')
        date = fields.Date(compute='_compute_info')
        ref = fields.Char(compute='_compute_info')
        user_id = fields.Many2one('res.users',compute='_compute_info')
        user =  fields.Char(store=True)
        location_id = fields.Many2one('stock.location')
        move_type = fields.Char(compute='_compute_info')
        credit_total = fields.Float()
        untaxed_total = fields.Float(compute='_compute_amount')
        taxed_total = fields.Float(compute='_compute_amount')
        tax_amount = fields.Float(compute='_compute_amount')
        partner_id = fields.Many2one(compute='_compute_info', store=True,string="Customer")
        Discount = fields.Float(compute='_compute_amount')
        total_wd = fields.Float(compute='_compute_amount',string="total without discount")
        
        @api.depends('price_unit','quantity')
        def _compute_amount(self):
            for rec in self:
                sign = 1
                if rec.move_id.move_type == 'out_refund':
                    sign = -1
                rec.total_wd = rec.price_unit * rec.quantity * sign
                rec.Discount = rec.total_wd * rec.discount/100
                rec.untaxed_total = rec.total_wd -rec.Discount 
                sum = 0 
                for t in rec.tax_ids:
                    tax = self.env['account.tax'].search([('id','=',t.id)])
                    sum = sum + t.amount
                    # if tax :
                    #     sum = tax.amount
                rec.taxed_total = rec.untaxed_total * sum/100  + rec.untaxed_total 
                rec.tax_amount = rec.taxed_total - rec.untaxed_total
                # if rec.move_id.move_type == 'out_refund':
                #     rec.total_wd = -1*rec.total_wd
                #     rec.untaxed_total = -1*rec.untaxed_total
                #     rec.discount = -1*rec.discount
                #     rec.taxed_total =  -1*rec.taxed_total
                   
                    
                print('>>>>>>>>>>>>>>>>',rec.taxed_total)
                

        @api.depends('move_id')
        def _compute_info(self):
            for rec in self :
                rec.date = rec.move_id.invoice_date
                rec.ref =  rec.move_id.name
                rec.user_id = rec.move_id.invoice_user_id.id
                rec.user = rec.move_id.invoice_user_id.name
                rec.move_type = rec.move_id.move_type
                rec.cate = rec.product_id.categ_id.id
                rec.partner_id = rec.move_id.partner_id.id
                
        @api.onchange('product_id')
        def _onchange_product(self):
            for rec in self:
                rec.cate = rec.product_id.categ_id.id
                