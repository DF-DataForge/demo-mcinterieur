from odoo import fields, models


class McProjectType(models.Model):
    _name = 'mc.project.type'
    _description = "Projecttype"
    _order = 'sequence, id'

    name = fields.Char(string="Projecttype", required=True, translate=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(
        string="Technische code",
        help="Vaste code voor de logica (bv. kitchen). Laat leeg voor eigen types.")
    show_appliances = fields.Boolean(
        string="Tabblad werkblad en toestellen",
        help="Toon de vragen over werkblad en toestellen bij dit type project.")
    default_install_days = fields.Integer(string="Standaard plaatsingsdagen", default=1)
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint('UNIQUE(code)', "Deze technische code bestaat al.")
