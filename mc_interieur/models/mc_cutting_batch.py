import csv
import io
import math

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.binary import BinaryBytes

from .mc_project import SHEET_YIELD

CSV_HEADER = [
    'PartID', 'Project', 'Klant', 'Kast', 'Onderdeel', 'Materiaal', 'Lengte', 'Breedte', 'Dikte', 'Aantal',
    'Nerf', 'Kant_L1', 'Kant_L2', 'Kant_B1', 'Kant_B2', 'CNC_programma',
]


class McCuttingBatch(models.Model):
    _name = 'mc.cutting.batch'
    _description = "Zaagbatch (Ardis)"
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string="Zaagbatch", readonly=True, copy=False, default="/")
    state = fields.Selection([
        ('draft', "Concept"),
        ('exported', "Geexporteerd naar Ardis"),
        ('waiting', "Wacht op levering"),
        ('ready', "Klaar om te zagen"),
        ('sawn', "Gezaagd"),
    ], string="Status", default='draft', required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    project_ids = fields.Many2many(
        'mc.project', string="Projecten", domain=[('stage', 'in', ('prep', 'sawing'))],
        help="Ardis optimaliseert over alle projecten van de batch heen.")
    part_ids = fields.One2many('mc.part', compute='_compute_part_ids', string="Onderdelen")
    unmapped_count = fields.Integer(compute='_compute_part_ids', string="Lijnen zonder Ardis-materiaal")
    material_html = fields.Html(compute='_compute_material_html', sanitize=False, string="Materiaal en voorraad")
    shortage_count = fields.Integer(compute='_compute_material_html', string="Tekorten")
    export_file = fields.Binary(string="Ardis-exportbestand", readonly=True, attachment=True)
    export_filename = fields.Char(readonly=True)
    exported_on = fields.Datetime(readonly=True)
    sheets_used = fields.Integer(string="Platen verbruikt", readonly=True)
    yield_percent = fields.Float(string="Rendement (%)", readonly=True)
    purchase_ids = fields.Many2many('purchase.order', string="Bestellingen", readonly=True, copy=False)
    purchase_count = fields.Integer(compute='_compute_purchase_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('mc.cutting.batch') or '/'
        return super().create(vals_list)

    @api.depends('project_ids.part_ids.product_id')
    def _compute_part_ids(self):
        for batch in self:
            batch.part_ids = batch.project_ids.part_ids
            batch.unmapped_count = len(batch.part_ids.filtered(lambda p: not p.product_id))

    @api.depends('purchase_ids')
    def _compute_purchase_count(self):
        for batch in self:
            batch.purchase_count = len(batch.purchase_ids)

    def _mc_needs(self):
        """Material needed by the batch: {product: quantity} for sheets (pieces) and edge banding (metres)."""
        self.ensure_one()
        sheets_area = {}
        edges = {}
        for part in self.project_ids.part_ids:
            if part.product_id:
                sheets_area[part.product_id] = sheets_area.get(part.product_id, 0.0) + part.area
            for edge, length in part._mc_edges():
                edges[edge] = edges.get(edge, 0.0) + length * part.quantity / 1000
        needs = {}
        for product, area in sheets_area.items():
            sheet_m2 = (product.mc_sheet_length or 2800) * (product.mc_sheet_width or 2070) / 1e6
            needs[product] = {'qty': math.ceil(area / (sheet_m2 * SHEET_YIELD)), 'area': area}
        for product, metres in edges.items():
            needs[product] = {'qty': math.ceil(metres * 1.1), 'area': 0.0}
        return needs

    @api.depends('project_ids.part_ids.product_id', 'project_ids.part_ids.quantity', 'state')
    def _compute_material_html(self):
        for batch in self:
            needs = batch._mc_needs()
            if not needs:
                batch.material_html = False
                batch.shortage_count = 0
                continue
            rows = []
            shortages = 0
            for product, need in needs.items():
                available = product.qty_available
                incoming = product.incoming_qty
                unit = 'm' if product.mc_kind == 'edge' else ''
                if batch.state != 'draft':
                    status = "<span class='badge text-bg-info'>Gereserveerd voor deze batch</span>"
                elif need['qty'] <= available:
                    status = "<span class='badge text-bg-success'>Op voorraad</span>"
                elif need['qty'] <= available + incoming:
                    status = "<span class='badge text-bg-info'>Besteld, dekt nood</span>"
                else:
                    shortages += 1
                    short = need['qty'] - available - incoming
                    status = f"<span class='badge text-bg-warning'>Tekort {short:g} {unit or 'st.'}</span>"
                rows.append(
                    f"<tr><td>{product.default_code or ''}</td><td>{product.name}</td>"
                    f"<td class='text-end'>{need['area']:.1f} m2</td><td class='text-end'><b>{need['qty']:g} {unit}</b></td>"
                    f"<td class='text-end'>{available:g} {unit}</td><td class='text-end'>{incoming:g} {unit}</td>"
                    f"<td>{status}</td></tr>")
            batch.shortage_count = shortages
            batch.material_html = (
                "<table class='table table-sm o_mc_table'><thead><tr><th>Ardis-code</th><th>Materiaal</th>"
                "<th class='text-end'>Oppervlakte</th><th class='text-end'>Nodig</th><th class='text-end'>Op voorraad</th>"
                "<th class='text-end'>Besteld</th><th>Status</th></tr></thead><tbody>"
                + ''.join(rows) + "</tbody></table>"
                "<p class='text-muted small'>Platen nodig = oppervlakte / plaat bij 82 % verwacht rendement. "
                "Ardis berekent het exacte aantal. Kantenband + 10 % snijverlies.</p>")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_export_ardis(self):
        """Write the CSV import file for Ardis and mark the batch as exported."""
        for batch in self:
            if not batch.project_ids:
                raise UserError(self.env._("Voeg eerst projecten toe aan de zaagbatch."))
            unmapped = batch.part_ids.filtered(lambda p: not p.product_id)
            if unmapped:
                raise UserError(self.env._(
                    "Deze TopSolid-materialen hebben nog geen Ardis-code: %s. "
                    "Koppel ze in Configuratie > Materiaalkoppeling.", sorted(set(unmapped.mapped('topsolid_material')))))
            batch.project_ids.filtered(lambda p: not p.piece_ids)._mc_generate_pieces()
            buffer = io.StringIO()
            writer = csv.writer(buffer, delimiter=';', lineterminator='\n')
            writer.writerow(CSV_HEADER)
            for piece in batch.project_ids.piece_ids:
                part = piece.part_id
                writer.writerow([
                    piece.barcode, part.project_id.ref, part.project_id.partner_id.name, part.cabinet or '',
                    part.name, part.product_id.default_code, part.length, part.width, f"{part.thickness:g}", 1,
                    1 if part.grain else 0,
                    part.edge_l1_id.default_code or '', part.edge_l2_id.default_code or '',
                    part.edge_w1_id.default_code or '', part.edge_w2_id.default_code or '',
                    part.cnc_program or '',
                ])
            filename = f"{batch.name}.csv"
            batch.write({
                'export_file': BinaryBytes(buffer.getvalue().encode('utf-8'), filename=filename),
                'export_filename': filename,
                'exported_on': fields.Datetime.now(),
                'state': 'exported',
            })
            for project in batch.project_ids:
                project.message_post(body=self.env._(
                    "Onderdelen geexporteerd naar Ardis in zaagbatch %s.", batch.name))
            batch.message_post(body=self.env._(
                "Exportbestand %(file)s klaargezet voor Ardis (%(count)s etiketten).",
                file=filename, count=len(batch.project_ids.piece_ids)))
        return True

    def action_open_ardis_result(self):
        self.ensure_one()
        if self.state != 'exported':
            raise UserError(self.env._("Exporteer de batch eerst naar Ardis."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mc.ardis.result',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_batch_id': self.id},
        }

    def action_order_shortages(self):
        """Create one purchase order per supplier for the materials the batch is short of."""
        self.ensure_one()
        lines_by_vendor = {}
        for product, need in self._mc_needs().items():
            short = need['qty'] - product.qty_available - product.incoming_qty
            if short <= 0:
                continue
            seller = product.seller_ids[:1]
            if not seller:
                raise UserError(self.env._("Geen leverancier ingesteld voor %s.", product.display_name))
            qty = math.ceil(short / 50) * 50 if product.mc_kind == 'edge' else math.ceil(short)
            lines_by_vendor.setdefault(seller.partner_id, []).append(Command.create({
                'product_id': product.id,
                'product_qty': qty,
            }))
        if not lines_by_vendor:
            raise UserError(self.env._("Er zijn geen tekorten voor deze zaagbatch."))
        orders = self.env['purchase.order'].create([{
            'partner_id': vendor.id,
            'origin': self.name,
            'order_line': lines,
        } for vendor, lines in lines_by_vendor.items()])
        orders.button_confirm()
        self.purchase_ids = [Command.link(order.id) for order in orders]
        self.message_post(body=self.env._("Bestellingen geplaatst: %s", orders.mapped('name')))
        return self.action_view_purchases()

    def action_view_purchases(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Bestellingen"),
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.purchase_ids.ids)],
        }

    def _mc_consume(self, quantities):
        """Book the consumption reported by Ardis out of stock: {product: quantity}."""
        self.ensure_one()
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
        if not warehouse:
            return self.env['stock.move']
        moves = self.env['stock.move'].create([{
            'product_id': product.id,
            'product_uom_qty': qty,
            'uom_id': product.uom_id.id,
            'location_id': warehouse.lot_stock_id.id,
            'location_dest_id': product.with_company(self.company_id).property_stock_production.id,
            'company_id': self.company_id.id,
        } for product, qty in quantities.items() if qty > 0])
        moves._action_confirm()
        moves._action_assign()
        for move in moves:
            move.quantity = move.product_uom_qty
        moves.picked = True
        moves._action_done()
        return moves

    def action_consume_after_delivery(self):
        """Material arrived: book the consumption and release the batch to the saw."""
        for batch in self.filtered(lambda b: b.state == 'waiting'):
            needs = {product: need['qty'] for product, need in batch._mc_needs().items()}
            missing = [p.display_name for p, q in needs.items() if p.qty_available < q]
            if missing:
                raise UserError(self.env._("Nog niet genoeg op voorraad: %s", missing))
            batch._mc_consume(needs)
            batch.state = 'ready'
            batch.message_post(body=self.env._("Materiaal geleverd. Verbruik geboekt, batch klaar om te zagen."))
        return True

    def action_mark_sawn(self):
        self.write({'state': 'sawn'})
