from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    mc_project_id = fields.Many2one('mc.project', string="Interieurproject", index='btree_not_null', copy=False)
    mc_version_id = fields.Many2one('mc.drawing.version', string="Tekeningversie", copy=False)
