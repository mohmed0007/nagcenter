# from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare
import json

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_treatment_plan = fields.Selection(readonly=False,related='company_id.tax_discount_policy_prescribtion_order',string='Discount Applies On',default_model='prescription.order'
        )


class ResCompany(models.Model):
    _inherit = 'res.company'

    tax_discount_policy_prescribtion_order = fields.Selection([('tax', 'Tax Amount'), ('untax', 'Untax Amount')],
        default_model='prescription.order',default='tax')



    def _valid_field_parameter_treatment(self, field, name):
        return name == 'default_model' or super()._valid_field_parameter(field, name)
