# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class AcsPetType(models.Model):
    _name="acs.pet.type"
    _description = "Pet Type"
    _order = "sequence"

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", default="50")
    image = fields.Image("Image")
    description = fields.Char(string="Description")


class AcsPetBreed(models.Model):
    _name="acs.pet.breed"
    _description = "Pet Breed"
    _order = "sequence"

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", default="50")
    image = fields.Image("Image")
    description = fields.Char(string="Description")
    pet_type_id = fields.Many2one('acs.pet.type', 'Pet Type', required=True)


class AcsPetColor(models.Model):
    _name="acs.pet.color"
    _description = "Pet Color"
    _order = "sequence"

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", default="50")
    description = fields.Char(string="Description")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:   