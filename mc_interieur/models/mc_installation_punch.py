from odoo import fields, models


class McInstallationPunch(models.Model):
    _name = 'mc.installation.punch'
    _description = "Nazorgpunt na plaatsing"
    _order = 'done, id'

    installation_id = fields.Many2one('mc.installation', required=True, ondelete='cascade', index=True)
    name = fields.Char(string="Nazorgpunt", required=True)
    done = fields.Boolean(string="Opgelost")
