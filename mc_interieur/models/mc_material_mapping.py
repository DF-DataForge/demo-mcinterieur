from odoo import api, fields, models


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

    @api.model_create_multi
    def create(self, vals_list):
        mappings = super().create(vals_list)
        mappings._mc_apply_to_parts()
        return mappings

    def write(self, vals):
        result = super().write(vals)
        if 'product_id' in vals or 'name' in vals:
            self._mc_apply_to_parts()
        return result

    def _mc_apply_to_parts(self):
        """Parts not in production yet pick up the new link straight away."""
        parts = self.env['mc.part'].search([
            ('topsolid_material', 'in', self.mapped('name')),
            ('project_id.piece_ids', '=', False),
        ])
        parts._mc_apply_mapping()
