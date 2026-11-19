import base64
import csv
import io

from odoo import fields, models
from odoo.exceptions import UserError


class McArdisResult(models.TransientModel):
    _name = 'mc.ardis.result'
    _description = "Ardis-resultaat inlezen"

    batch_id = fields.Many2one('mc.cutting.batch', required=True, ondelete='cascade')
    mode = fields.Selection([
        ('simulate', "Demo: resultaat simuleren"),
        ('file', "Exportbestand van Ardis opladen"),
    ], default='simulate', required=True, string="Bron")
    result_file = fields.Binary(string="Ardis-resultaat (CSV)")
    result_filename = fields.Char()

    def _mc_parse_file(self):
        """Expected columns: Materiaal;Verbruik (Ardis code and sheets or metres used)."""
        content = base64.b64decode(self.result_file).decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content), delimiter=';')
        quantities = {}
        Product = self.env['product.product']
        for row in reader:
            code = (row.get('Materiaal') or '').strip()
            if not code:
                continue
            product = Product.search([('default_code', '=', code)], limit=1)
            if not product:
                raise UserError(self.env._("Onbekende Ardis-code in het resultaat: %s", code))
            quantities[product] = quantities.get(product, 0.0) + float((row.get('Verbruik') or '0').replace(',', '.'))
        return quantities

    def action_apply(self):
        self.ensure_one()
        batch = self.batch_id
        if self.mode == 'file':
            if not self.result_file:
                raise UserError(self.env._("Kies het resultaatbestand van Ardis."))
            quantities = self._mc_parse_file()
        else:
            quantities = {product: need['qty'] for product, need in batch._mc_needs().items()}
        plates = {p: q for p, q in quantities.items() if p.mc_kind == 'plate'}
        sheets = sum(plates.values())
        area = sum(batch.project_ids.part_ids.mapped('area'))
        sheet_area = sum(
            q * (p.mc_sheet_length or 2800) * (p.mc_sheet_width or 2070) / 1e6 for p, q in plates.items())
        waiting = [p.display_name for p, q in quantities.items() if p.qty_available < q]
        if not waiting:
            batch._mc_consume(quantities)
        batch.write({
            'state': 'waiting' if waiting else 'ready',
            'sheets_used': sheets,
            'yield_percent': round(area / sheet_area * 100, 1) if sheet_area else 0.0,
        })
        batch.project_ids.filtered(lambda p: p.stage == 'prep').write({'stage': 'sawing'})
        if waiting:
            batch.message_post(body=self.env._(
                "Zaagplannen van Ardis ingelezen. Wacht op levering van: %s. "
                "Het verbruik wordt geboekt zodra het materiaal binnen is.", waiting))
        else:
            batch.message_post(body=self.env._(
                "Zaagplannen van Ardis ingelezen: %(sheets)s platen, rendement %(pct)s %%. Verbruik geboekt op de voorraad.",
                sheets=sheets, pct=batch.yield_percent))
        for project in batch.project_ids:
            project.message_post(body=self.env._("Ardis-resultaat ingelezen (%s): klaar om te zagen.", batch.name))
        return {'type': 'ir.actions.act_window_close'}
