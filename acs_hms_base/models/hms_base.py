# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime

from random import randint

import base64
from io import BytesIO

class ACSQrcodeMixin(models.AbstractModel):
    _name = "acs.qrcode.mixin"
    _description = "QrCode Mixin"

    unique_code = fields.Char("Unique UID")
    qr_image = fields.Binary("QR Code", compute='acs_generate_qrcode')

    def acs_generate_qrcode(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            import qrcode
            model_name = (rec._name).replace('.','')
            url = base_url + '/validate/%s/%s' % (model_name,rec.unique_code)
            data = BytesIO()
            qrcode.make(url.encode(), box_size=4).save(data, optimise=True, format='PNG')
            qrcode = base64.b64encode(data.getvalue()).decode()
            rec.qr_image = qrcode


class ACSHmsMixin(models.AbstractModel):
    _name = "acs.hms.mixin"
    _description = "HMS Mixin"

    def acs_prepare_invocie_data(self, partner, patient, product_data, inv_data):
        fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(partner.id)
        data = {
            'partner_id': partner.id,
            'patient_id': patient and patient.id,
            'move_type': inv_data.get('move_type','out_invoice'),
            'ref': self.name,
            'invoice_origin': self.name,
            'currency_id': self.env.user.company_id.currency_id.id,
            'invoice_line_ids': self.acs_get_invoice_lines(product_data, partner, inv_data, fiscal_position_id),
            'physician_id': inv_data.get('physician_id',False),
            'hospital_invoice_type': inv_data.get('hospital_invoice_type',False),
            'fiscal_position_id': fiscal_position_id,
        }
        if inv_data.get('ref_physician_id',False):
            data['ref_physician_id'] = inv_data.get('ref_physician_id',False)
        if inv_data.get('appointment_id',False):
            data['appointment_id'] = inv_data.get('appointment_id',False)
        data['discount_method'] = inv_data.get('discount_method',False)
        data['discount_amount'] = inv_data.get('discount_amount',False)
        data['discount_amt'] = inv_data.get('discount_amt',False)
        data['discount_amt_line'] = inv_data.get('discount_amt_line',False)
        data['discount_type'] = inv_data.get('discount_type',False)

        return data

    @api.model
    def acs_create_invoice(self, partner, patient=False, product_data=[], inv_data={}):
        inv_data1 = self.acs_prepare_invocie_data(partner, patient, product_data, inv_data)
        vals_list = []
        vals_list.append(inv_data1)
        invoice = self.env['account.move'].with_context(check_move_validity=False).create(vals_list)

        invoice._onchange_partner_id()
        # for line in invoice.invoice_line_ids:
        #     line._get_computed_name()
        #     line._get_computed_account()
        #     line._get_computed_taxes()
        #     line._get_computed_uom()

        invoice._recompute_dynamic_lines(recompute_all_taxes=True,recompute_tax_base_amount=True)
        return invoice

    @api.model
    def acs_get_invoice_lines(self, product_data, partner, inv_data, fiscal_position_id):
        lines = []
        for data in product_data:
            product = data.get('product_id')
            if product:
                acs_pricelist_id = self.env.context.get('acs_pricelist_id')
                if not data.get('price_unit') and (partner.property_product_pricelist or acs_pricelist_id):
                    pricelist_id = acs_pricelist_id or partner.property_product_pricelist.id
                    price = product.with_context(pricelist=pricelist_id).price
                else:
                    price = data.get('price_unit', product.list_price)

                if inv_data.get('move_type','out_invoice') in ['out_invoice','out_refund']:
                    tax_ids = product.taxes_id
                else:
                    tax_ids = product.supplier_taxes_id

                if tax_ids:
                    if fiscal_position_id:
                        tax_ids = fiscal_position_id.map_tax(tax_ids._origin)
                    tax_ids = [(6, 0, tax_ids.ids)]
                t = data.get('tax_ids')
                tax_ids = [(6, 0, t or [])]

                lines.append((0, 0, {
                    'name': data.get('name',product.get_product_multiline_description_sale()),
                    'product_id': product.id,
                    'price_unit': price,
                    'quantity': data.get('quantity',1.0),
                    'discount': data.get('discount',0.0),
                    'product_uom_id': data.get('product_uom_id',product.uom_id.id),
                    'analytic_account_id': data.get('account_analytic_id',False),
                    'tax_ids':tax_ids,
                    'discount_method':data.get('discount_method',False),
                    'discount_amount':data.get('discount_amount',False),
                    'discount_amt':data.get('discount_amt',False),
                    # 'discount_method':data.get('discount_method',False),
                    
                }))
            else:
                lines.append((0, 0, {
                    'name': data.get('name'),
                    'display_type': data.get('display_type', 'line_section'),
                }))
        return lines

    @api.model
    def acs_create_invoice_line(self, product_data, invoice):
        product = product_data.get('product_id')
        MoveLine = self.env['account.move.line']
        if product:
            acs_pricelist_id = self.env.context.get('acs_pricelist_id')
            if not product_data.get('price_unit') and (invoice.partner_id.property_product_pricelist or acs_pricelist_id):
                pricelist_id = acs_pricelist_id or invoice.partner_id.property_product_pricelist.id
                price = product.with_context(pricelist=pricelist_id).price
            else:
                price = product_data.get('price_unit', product.list_price)

            if invoice.move_type in ['out_invoice','out_refund']:
                tax_ids = product.taxes_id
            else:
                tax_ids = product.supplier_taxes_id

            if tax_ids:
                if invoice.fiscal_position_id:
                    tax_ids = invoice.fiscal_position_id.map_tax(tax_ids._origin)
                tax_ids = [(6, 0, tax_ids.ids)]
            t = product_data.get('tax_ids',[])
            tax_ids = [(6, 0, t)]


            account_id = product.property_account_income_id or product.categ_id.property_account_income_categ_id
            line = MoveLine.with_context(check_move_validity=False).create({
                'move_id': invoice.id,
                'name': product_data.get('name',product.get_product_multiline_description_sale()),
                'product_id': product.id,
                'account_id': account_id.id,
                'price_unit': price,
                'quantity': product_data.get('quantity',1.0),
                'discount': product_data.get('discount',0.0),
                'product_uom_id': product_data.get('product_uom_id',product.uom_id.id),
                'analytic_account_id': product_data.get('account_analytic_id',False),
                'tax_ids': tax_ids,
            })
        else:
            line = MoveLine.with_context(check_move_validity=False).create({
                'move_id': invoice.id,
                'name': product_data.get('name'),
                'display_type': 'line_section',
            })
            
        return line

    def acs_action_view_invoice(self, invoices):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [('id', 'in', invoices.ids)]
        context = {
            'default_move_type': 'out_invoice',
        }
        action['context'] = context
        # if len(invoices) > 1:
        #     action['domain'] = [('id', 'in', invoices.ids)]
        # elif len(invoices) == 1:
        #     action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        #     action['res_id'] = invoices.id
        # elif self.env.context.get('acs_open_blank_list'):
        #     #Allow to open invoices
        #     action['domain'] = [('id', 'in', invoices.ids)]
        # else:
        #     action = {'type': 'ir.actions.act_window_close'}

        # context = {
        #     'default_move_type': 'out_invoice',
        # }
        # action['context'] = context
        return action

    @api.model
    def assign_given_lots(self, move, lot_id, lot_qty):
        MoveLine = self.env['stock.move.line']
        move_line_id = MoveLine.search([('move_id', '=', move.id),('lot_id','=',False)],limit=1)
        if move_line_id:
            move_line_id.lot_id = lot_id
            move_line_id.quantity_done = lot_qty

    def consume_material(self, source_location_id, dest_location_id, product_data):
        product = product_data['product']
        move = self.env['stock.move'].create({
            'name' : product.name,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': product_data.get('qty',1.0),
            'date': product_data.get('date',fields.datetime.now()),
            'location_id': source_location_id,
            'location_dest_id': dest_location_id,
            'state': 'draft',
            'origin': self.name,
            'quantity_done': product_data.get('qty',1.0),
        })
        move._action_confirm()
        move._action_assign()
        if product_data.get('lot_id', False):
            lot_id = product_data.get('lot_id')
            lot_qty = product_data.get('qty',1.0)
            self.assign_given_lots(move, lot_id, lot_qty)
        if move.state == 'assigned':
            move._action_done()
        return move


class ACSDocumntMixin(models.AbstractModel):
    _name = "acs.documnt.mixin"
    _description = "Document Mixin"

    def _acs_attachemnt_count(self):
        AttachmentObj = self.env['ir.attachment']
        for rec in self:
            attachments = AttachmentObj.search([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id)])
            rec.attachment_ids = [(6,0,attachments.ids)]
            rec.attach_count = len(attachments.ids)

    def _acs_attachemnt_count_2(self):
        AttachmentObj = self.env['ir.attachment']
        for rec in self:
            attachments = AttachmentObj.search([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id)])
            rec.attachment_2_ids = [(6,0,attachments.ids)]
            rec.attach_count_2 = len(attachments.ids)

    attach_count = fields.Integer(compute="_acs_attachemnt_count", readonly=True, string="Documents")
    attach_count_2 = fields.Integer(compute="_acs_attachemnt_count_2", readonly=True, string="Documents2")
    attachment_ids = fields.Many2many('ir.attachment', 'attachment_acs_hms_rel', 'record_id', 'attachment_id', compute="_acs_attachemnt_count", string="Attachments")
    attachment_2_ids = fields.Many2many('ir.attachment', 'attachment_acs_hms_rel_2', 'record_id_2', 'attachment_id_2', compute="_acs_attachemnt_count_2", string="Attachments2")
    
    def action_view_attachments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("base.action_attachment")
        action['domain'] = [('id', 'in', self.attachment_ids.ids)]
        action['context'] = {
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_is_document': True}
        return action

    def action_attachments_preview(self):
        raise UserError(_("Please install Document Preview module first."))


class ACSAppointmentConsumable(models.Model):
    _name = "hms.consumable.line"
    _description = "List of Consumables"

    name = fields.Char(string='Name',default=lambda self: self.product_id.name)
    product_id = fields.Many2one('product.product', ondelete="restrict", string='Consumable')
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', help='Amount of medication (eg, 250 mg) per dose', domain="[('category_id', '=', product_uom_category_id)]")
    qty = fields.Float(string='Quantity', default=1.0)
    move_id = fields.Many2one('stock.move', string='Stock Move')
    date = fields.Date("Date", default=fields.Date.context_today)
    note = fields.Char("Note")

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

class ACSPatientTag(models.Model):
    _name = "hms.patient.tag"
    _description = "Acs Patient Tag"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string="Name")
    color = fields.Integer('Color', default=_get_default_color)


class ACSTherapeuticEffect(models.Model):
    _name = "hms.therapeutic.effect"
    _description = "Acs Therapeutic Effect"


    code = fields.Char(string="Code")
    name = fields.Char(string="Name", required=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: