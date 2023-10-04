# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_


class AcsPatientProcedure(models.Model):
    _inherit="acs.patient.procedure"

    STATES = {'cancel': [('readonly', True)], 'done': [('readonly', True)]}

    patient_id = fields.Many2one('hms.patient', string='Patient/Pet', required=True, states=STATES)
    partner_id = fields.Many2one("res.partner", required=True, string="Owner Name", states=STATES)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: