from odoo import fields, models


class McInstallationCheck(models.Model):
    _name = 'mc.installation.check'
    _description = "Controlepunt plaatsing"
    _order = 'sequence, id'

    installation_id = fields.Many2one('mc.installation', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Controlepunt", required=True)
    done = fields.Boolean(string="OK")
