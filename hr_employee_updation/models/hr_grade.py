# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _


class HrGrade(models.Model):
    _name = 'hr.grade'
    _description = "Grade Description"

    name = fields.Char('Name', required=True)
    hr_job_ids = fields.One2many('hr.job', 'grade_id', 'Job')
    per_diem_amount = fields.Float('Per Diem Amount', default=0.0)


class HrJob(models.Model):
    _inherit = 'hr.job'
    _description = 'HR Job'

    grade_id = fields.Many2one('hr.grade', string='Grade')
    annual_leave_rate = fields.Float('Annual Leave Rate', default=2)
