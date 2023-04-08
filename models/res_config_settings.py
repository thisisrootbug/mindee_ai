# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mindee_api_key = fields.Char(string="Mindee Api Key",config_parameter="mindee_api_key")
