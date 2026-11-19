from odoo import api, fields, models


class McPart(models.Model):
    _name = 'mc.part'
    _description = "Onderdeel uit de TopSolid-materiaallijst"
    _order = 'project_id, sequence, id'

    project_id = fields.Many2one('mc.project', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    cabinet = fields.Char(string="Kast", help="Kastcode uit TopSolid, bv. O1-O4 of K1 bureau")
    name = fields.Char(string="Onderdeel", required=True)
    topsolid_material = fields.Char(string="Materiaal in TopSolid", required=True)
    product_id = fields.Many2one(
        'product.product', string="Ardis-materiaal", domain=[('mc_kind', '=', 'plate')],
        help="Ingevuld via de materiaalkoppeling. Leeg = nog te koppelen voor de export naar Ardis.")
    length = fields.Integer(string="Lengte (mm)", required=True)
    width = fields.Integer(string="Breedte (mm)", required=True)
    thickness = fields.Float(string="Dikte (mm)")
    quantity = fields.Integer(string="Aantal", default=1, required=True)
    grain = fields.Boolean(string="Nerf")
    edge_l1_id = fields.Many2one('product.product', string="Kant L1", domain=[('mc_kind', '=', 'edge')])
    edge_l2_id = fields.Many2one('product.product', string="Kant L2", domain=[('mc_kind', '=', 'edge')])
    edge_w1_id = fields.Many2one('product.product', string="Kant B1", domain=[('mc_kind', '=', 'edge')])
    edge_w2_id = fields.Many2one('product.product', string="Kant B2", domain=[('mc_kind', '=', 'edge')])
    cnc_program = fields.Char(string="CNC-programma", help="Bestandsnaam uit de TopSolid CNC-plugin")
    area = fields.Float(string="Oppervlakte (m2)", compute='_compute_area', digits=(16, 3))
    piece_ids = fields.One2many('mc.piece', 'part_id', string="Etiketten")

    _quantity_positive = models.Constraint('CHECK(quantity > 0)', "Het aantal moet groter dan nul zijn.")

    @api.depends('length', 'width', 'quantity')
    def _compute_area(self):
        for part in self:
            part.area = part.length * part.width * part.quantity / 1e6

    @api.model_create_multi
    def create(self, vals_list):
        parts = super().create(vals_list)
        parts.filtered(lambda p: not p.product_id)._mc_apply_mapping()
        return parts

    def _mc_apply_mapping(self):
        names = set(self.mapped('topsolid_material'))
        mappings = self.env['mc.material.mapping'].search([('name', 'in', list(names))])
        by_name = {mapping.name: mapping.product_id for mapping in mappings}
        for part in self:
            product = by_name.get(part.topsolid_material)
            if product and part.product_id != product:
                part.product_id = product

    def _mc_edges(self):
        """Edge banding of this part as (product, length in mm per piece)."""
        self.ensure_one()
        edges = []
        for field_name, length in (('edge_l1_id', self.length), ('edge_l2_id', self.length),
                                   ('edge_w1_id', self.width), ('edge_w2_id', self.width)):
            if self[field_name]:
                edges.append((self[field_name], length))
        return edges

    def _mc_edge_label(self):
        self.ensure_one()
        sides = {}
        for side, field_name in (('L1', 'edge_l1_id'), ('L2', 'edge_l2_id'), ('B1', 'edge_w1_id'), ('B2', 'edge_w2_id')):
            if self[field_name]:
                sides.setdefault(self[field_name].default_code or self[field_name].name, []).append(side)
        return ", ".join(f"{code}: {' '.join(s)}" for code, s in sides.items())
