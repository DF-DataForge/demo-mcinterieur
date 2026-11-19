from odoo import fields, models


class McTeam(models.Model):
    _name = 'mc.team'
    _description = "Plaatsingsploeg"
    _order = 'sequence, id'

    name = fields.Char(string="Ploeg", required=True)
    sequence = fields.Integer(default=10)
    user_ids = fields.Many2many('res.users', string="Leden", domain=[('share', '=', False)])
    color = fields.Integer(string="Kleur")
    active = fields.Boolean(default=True)
