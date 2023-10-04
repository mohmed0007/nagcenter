# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class product_template(models.Model):
    _inherit = "product.template"

    form_id = fields.Many2one('drug.form', ondelete='cascade', string='Drug Form', tracking=True)
    active_component_ids = fields.Many2many('active.comp', 'product_active_comp_rel', 'product_id','comp_id','Active Component')
    drug_company_id = fields.Many2one('drug.company', ondelete='cascade', string='Drug Company', help='Company producing this drug')
    hospital_product_type = fields.Selection([
        ('medicament','Medicament'),
        ('fdrinks', 'Food & Drinks'),
        ('os', 'Other Service'),
        ('not_medical', 'Not Medical'),], string="Hospital Product Type", default='medicament')
    indications = fields.Text(string='Indication', help='Indications') 
    therapeutic_effect_ids = fields.Many2many('hms.therapeutic.effect', 'therapeutic_action_rel', 'therapeutic_effect_id', 'effect_id', string='Therapeutic Effect', help='Therapeutic action')
    pregnancy_warning = fields.Boolean(string='Pregnancy Warning',
        help='The drug represents risk to pregnancy')
    lactation_warning = fields.Boolean('Lactation Warning',
        help='The drug represents risk in lactation period')
    pregnancy = fields.Text(string='Pregnancy and Lactancy',
        help='Warnings for Pregnant Women')

    notes = fields.Text(string='Extra Info')
    storage = fields.Char(string='Storage')
    adverse_reaction = fields.Char(string='Adverse Reactions')
    dosage = fields.Float(string='Dosage', help='Dosage')
    product_uom_category_id = fields.Many2one('uom.category', related='uom_id.category_id')
    dosage_uom_id = fields.Many2one('uom.uom', string='Unit of Dosage', domain="[('category_id', '=', product_uom_category_id)]")
    route_id = fields.Many2one('drug.route', ondelete='cascade', 
        string='Route', help='')
    form_id = fields.Many2one('drug.form', ondelete='cascade', 
        string='Form',help='Drug form, such as tablet or gel')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: