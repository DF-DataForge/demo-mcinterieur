import csv
import io

from odoo import fields, models
from odoo.exceptions import UserError

REQUIRED_COLUMNS = ('Onderdeel', 'Materiaal', 'Lengte', 'Breedte')


class McTopsolidImport(models.TransientModel):
    _name = 'mc.topsolid.import'
    _description = "TopSolid-materiaallijst inlezen"

    project_id = fields.Many2one('mc.project', required=True, ondelete='cascade')
    parts_file = fields.Binary(string="Materiaallijst (CSV uit TopSolid)", required=True)
    parts_filename = fields.Char()
    replace_existing = fields.Boolean(
        string="Bestaande onderdelen vervangen", default=True,
        help="Vervangt de huidige onderdelenlijst, bv. na een nieuwe tekeningversie.")

    def _mc_float(self, value, line_number, column):
        try:
            return float((value or '0').replace(',', '.'))
        except ValueError as error:
            raise UserError(self.env._(
                "Lijn %(line)s: \"%(value)s\" in kolom %(column)s is geen getal.",
                line=line_number, value=value, column=column)) from error

    def _mc_parse(self):
        """Read the TopSolid export: semicolon separated, one line per part, header on the first line."""
        content = self.parts_file.content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content), delimiter=';')
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise UserError(self.env._(
                "Dit lijkt geen TopSolid-materiaallijst: kolommen %s ontbreken.", missing))
        edges = {
            product.default_code: product
            for product in self.env['product.product'].search([('mc_kind', '=', 'edge')])
        }
        unknown_edges = set()
        vals_list = []
        for line_number, row in enumerate(reader, start=2):
            if not (row.get('Onderdeel') or '').strip():
                continue
            edge_ids = {}
            for column, field_name in (('Kant_L1', 'edge_l1_id'), ('Kant_L2', 'edge_l2_id'),
                                       ('Kant_B1', 'edge_w1_id'), ('Kant_B2', 'edge_w2_id')):
                code = (row.get(column) or '').strip()
                if code and code in edges:
                    edge_ids[field_name] = edges[code].id
                elif code:
                    unknown_edges.add(code)
            vals_list.append({
                'project_id': self.project_id.id,
                'sequence': line_number,
                'cabinet': (row.get('Kast') or '').strip(),
                'name': row['Onderdeel'].strip(),
                'topsolid_material': (row.get('Materiaal') or '').strip(),
                'length': int(self._mc_float(row.get('Lengte'), line_number, 'Lengte')),
                'width': int(self._mc_float(row.get('Breedte'), line_number, 'Breedte')),
                'thickness': self._mc_float(row.get('Dikte'), line_number, 'Dikte'),
                'quantity': int(self._mc_float(row.get('Aantal') or '1', line_number, 'Aantal')) or 1,
                'grain': (row.get('Nerf') or '').strip().lower() in ('1', 'ja', 'yes', 'true', 'x'),
                'cnc_program': (row.get('CNC') or '').strip() or False,
                **edge_ids,
            })
        if not vals_list:
            raise UserError(self.env._("Het bestand bevat geen onderdelen."))
        return vals_list, sorted(unknown_edges)

    def action_import(self):
        self.ensure_one()
        project = self.project_id
        if project.piece_ids:
            raise UserError(self.env._(
                "Dit project is al in productie (er zijn etiketten). De materiaallijst kan niet meer vervangen worden."))
        vals_list, unknown_edges = self._mc_parse()
        if self.replace_existing:
            project.part_ids.unlink()
        parts = self.env['mc.part'].create(vals_list)
        project.parts_imported_on = fields.Datetime.now()
        attachment = self.env['ir.attachment'].create({
            'name': self.parts_filename or 'topsolid.csv',
            'raw': self.parts_file.content,
            'res_model': 'mc.project',
            'res_id': project.id,
        })
        unmapped = sorted(set(parts.filtered(lambda p: not p.product_id).mapped('topsolid_material')))
        body = self.env._("TopSolid-materiaallijst ingelezen: %s onderdelen.", len(parts))
        if unmapped:
            body += " " + self.env._("Nog te koppelen aan een Ardis-code: %s.", unmapped)
        if unknown_edges:
            body += " " + self.env._("Onbekende kantenband: %s.", unknown_edges)
        project.message_post(body=body, attachment_ids=attachment.ids)
        return {'type': 'ir.actions.act_window_close'}
