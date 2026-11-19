from odoo import fields, models


class McMaterialMapping(models.Model):
    _name = 'mc.material.mapping'
    _description = "Materiaalkoppeling TopSolid naar Ardis"
    _order = 'name, id'

    name = fields.Char(string="Materiaal in TopSolid", required=True)
    product_id = fields.Many2one(
        'product.product', string="Voorraadartikel (Ardis-code)",
        domain=[('mc_kind', '=', 'plate')],
    )
    ardis_code = fields.Char(related='product_id.default_code', string="Ardis-code")

    _name_uniq = models.Constraint('UNIQUE(name)', "Dit TopSolid-materiaal is al gekoppeld.")
