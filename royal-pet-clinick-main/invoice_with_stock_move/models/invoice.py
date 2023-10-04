# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = "res.users"

    acs_warehouse_id = fields.Many2one('stock.warehouse', 'Default Picking Warehouse', copy=False)
    acs_picking_type_id = fields.Many2one('stock.picking.type', 'Default Picking Type', copy=False)

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['acs_warehouse_id', 'acs_picking_type_id']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['acs_warehouse_id', 'acs_picking_type_id']


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _get_default_warehouse(self):
        acs_warehouse_id = self.env.user.sudo().acs_warehouse_id
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        return acs_warehouse_id or warehouse_id

    @api.model
    def _get_default_picking_type(self):
        return self.env.user.sudo().acs_picking_type_id or False

    STATES = {'posted': [('readonly', True)]}

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', default=_get_default_warehouse, states=STATES)
    create_stock_moves = fields.Boolean("Create Stock Moves?", copy=False, states=STATES)
    picking_id = fields.Many2one('stock.picking', 'Picking', copy=False, states=STATES)
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', copy=False, default=_get_default_picking_type, states=STATES)
    acs_location_id = fields.Many2one('stock.location', 'Src Location', copy=False, states=STATES)
    acs_location_dest_id = fields.Many2one('stock.location', 'Destiantion Location', copy=False, states=STATES)

    @api.onchange('warehouse_id','picking_type_id','move_type','create_stock_moves')
    def onchange_warehouse(self):
        if self.warehouse_id:
            if self.move_type == 'out_invoice':
                self.picking_type_id = self.warehouse_id.out_type_id.id
                self.acs_location_id = self.picking_type_id.default_location_src_id and self.picking_type_id.default_location_src_id.id or self.warehouse_id.lot_stock_id.id
                self.acs_location_dest_id = self.picking_type_id.default_location_dest_id and self.picking_type_id.default_location_dest_id.id or self.partner_id.property_stock_customer.id

            elif self.move_type == 'in_invoice':
                self.picking_type_id = self.warehouse_id.in_type_id.id
                self.acs_location_id = self.picking_type_id.default_location_src_id and self.picking_type_id.default_location_src_id.id or self.partner_id.property_stock_supplier.id
                self.acs_location_dest_id = self.picking_type_id.default_location_dest_id and self.picking_type_id.default_location_dest_id.id or self.warehouse_id.lot_stock_id.id

            elif self.move_type == 'out_refund':
                self.picking_type_id = self.warehouse_id.in_type_id.id
                self.acs_location_id =  self.picking_type_id.default_location_src_id and self.picking_type_id.default_location_src_id.id or self.partner_id.property_stock_customer.id
                self.acs_location_dest_id = self.picking_type_id.default_location_dest_id and self.picking_type_id.default_location_dest_id.id or self.warehouse_id.lot_stock_id.id

            elif self.move_type == 'in_refund':
                self.picking_type_id = self.warehouse_id.out_type_id.id
                self.acs_location_id =  self.picking_type_id.default_location_src_id and self.picking_type_id.default_location_src_id.id or self.warehouse_id.lot_stock_id.id
                self.acs_location_dest_id = self.picking_type_id.default_location_dest_id and self.picking_type_id.default_location_dest_id.id or self.partner_id.property_stock_supplier.id

    #Hook: Allow to change in other module
    @api.model
    def assign_invoice_lots(self, picking):
        pass

    def acs_check_picking_possibility(self):
        create_picking = False
        if any(inv_line.product_id and inv_line.product_id.type in ['consu','product'] for inv_line in self.invoice_line_ids):
            create_picking = True
        return create_picking

    @api.model
    def move_line_from_invoice_lines(self, picking, location_id, location_dest_id):
        StockMove = self.env['stock.move']
        for line in self.invoice_line_ids:
            if line.product_id and line.product_id.type!='service':
                StockMove.create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_uom_id.id,
                    'date': fields.datetime.now(),
                    'picking_id': picking.id,
                    'picking_type_id': picking.picking_type_id.id,
                    'state': 'draft',
                    'name': line.name,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                    #'quantity_done': line.quantity,
                })

    @api.model
    def acs_create_picking(self, picking_type_id, location_id, location_dest_id):
        picking_id = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'date': fields.datetime.now(), 
            'company_id': self.company_id.id,
            'picking_type_id': picking_type_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'move_type': 'direct',
            'origin': self.name,
        })

        self.picking_id = picking_id.id
        self.move_line_from_invoice_lines(picking_id, location_id, location_dest_id)

        picking_id.action_confirm()
        picking_id.action_assign()
        self.assign_invoice_lots(picking_id)
        if picking_id.state == 'assigned':
            #Set Done Qty
            for move in picking_id.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
            picking_id.button_validate()

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for inv in self:
            if inv.create_stock_moves and inv.acs_check_picking_possibility():
                if (not inv.picking_type_id) or (not inv.acs_location_id) or (not inv.acs_location_dest_id):
                    inv.onchange_warehouse()
                if inv.picking_type_id and inv.acs_location_id and inv.acs_location_dest_id:
                    inv.acs_create_picking(inv.picking_type_id, inv.acs_location_id, inv.acs_location_dest_id)
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        if self.picking_id:
            self.picking_id.action_cancel()