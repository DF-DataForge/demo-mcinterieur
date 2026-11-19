from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    mc_kind = fields.Selection(
        selection=[
            ('plate', "Plaatmateriaal"),
            ('edge', "Kantenband"),
            ('hardware', "Beslag"),
        ],
        string="Soort interieurmateriaal",
        help="Bepaalt hoe het artikel gebruikt wordt in offertes, Ardis-export en werkvoorbereiding. "
             "De interne referentie is de Ardis-code.",
    )
    mc_sheet_length = fields.Integer(string="Plaatlengte (mm)", default=2800)
    mc_sheet_width = fields.Integer(string="Plaatbreedte (mm)", default=2070)
    mc_thickness = fields.Float(string="Dikte (mm)")
    mc_grain = fields.Boolean(string="Heeft nerf")
