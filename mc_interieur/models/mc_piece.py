from odoo import api, fields, models

STATIONS = ('saw', 'cnc', 'assembly')


class McPiece(models.Model):
    _name = 'mc.piece'
    _description = "Onderdeel met etiket (barcode)"
    _order = 'project_id, barcode, id'
    _rec_name = 'barcode'

    barcode = fields.Char(required=True, index=True, copy=False)
    part_id = fields.Many2one('mc.part', required=True, ondelete='cascade', index=True)
    project_id = fields.Many2one(related='part_id.project_id', store=True, index=True)
    name = fields.Char(related='part_id.name', string="Onderdeel")
    cabinet = fields.Char(related='part_id.cabinet')
    cnc_program = fields.Char(related='part_id.cnc_program')
    needs_cnc = fields.Boolean(compute='_compute_needs_cnc', store=True)
    sawn = fields.Boolean(string="Gezaagd")
    sawn_on = fields.Datetime(readonly=True)
    cnc_done = fields.Boolean(string="CNC klaar")
    cnc_done_on = fields.Datetime(readonly=True)
    kitted = fields.Boolean(string="Verzameld voor montage")
    assembled = fields.Boolean(string="Kast gemonteerd")

    _barcode_uniq = models.Constraint('UNIQUE(barcode)', "Deze barcode bestaat al.")

    @api.depends('part_id.cnc_program')
    def _compute_needs_cnc(self):
        for piece in self:
            piece.needs_cnc = bool(piece.part_id.cnc_program)

    # ------------------------------------------------------------------
    # Scan station (called by the mc_scan_station client action)
    # ------------------------------------------------------------------
    def _mc_piece_info(self):
        self.ensure_one()
        part = self.part_id
        return {
            'id': self.id,
            'barcode': self.barcode,
            'name': part.name,
            'cabinet': part.cabinet or '',
            'project': self.project_id.display_name,
            'size': f"{part.length} x {part.width} x {part.thickness:g}",
            'material': part.product_id.default_code or part.topsolid_material,
            'cnc_program': part.cnc_program or '',
            'edges': part._mc_edge_label(),
        }

    @api.model
    def mc_station_data(self, station):
        """Queue shown at a station: what still has to be done there."""
        if station not in STATIONS:
            return {'queue': []}
        if station == 'saw':
            domain = [('sawn', '=', False), ('project_id.stage', '=', 'sawing')]
        elif station == 'cnc':
            domain = [('sawn', '=', True), ('needs_cnc', '=', True), ('cnc_done', '=', False)]
        else:
            domain = [('kitted', '=', False), ('project_id.stage', '=', 'assembly')]
        pieces = self.search(domain, limit=80)
        cabinets = []
        if station == 'assembly':
            projects = self.env['mc.project'].search([('stage', '=', 'assembly')])
            for project in projects:
                groups = project.piece_ids.grouped('cabinet')
                for cabinet, cabinet_pieces in groups.items():
                    cabinets.append({
                        'project_id': project.id,
                        'project': project.display_name,
                        'cabinet': cabinet or '-',
                        'kitted': len(cabinet_pieces.filtered('kitted')),
                        'total': len(cabinet_pieces),
                        'assembled': all(cabinet_pieces.mapped('assembled')),
                    })
        return {'queue': [piece._mc_piece_info() for piece in pieces], 'cabinets': cabinets}

    @api.model
    def mc_scan(self, station, code):
        """Process one scanned label at a station and return the feedback to show."""
        code = (code or '').strip().upper()
        if station not in STATIONS or not code:
            return {'kind': 'warning', 'title': self.env._("Geen barcode ontvangen.")}
        piece = self.search([('barcode', '=', code)], limit=1)
        if not piece:
            return {'kind': 'warning', 'title': self.env._("Onbekende barcode: %s", code),
                    'detail': self.env._("Controleer het etiket of scan opnieuw.")}
        info = piece._mc_piece_info()
        project = piece.project_id
        now = fields.Datetime.now()
        if station == 'saw':
            if piece.sawn:
                return {'kind': 'warning', 'title': self.env._("Al gezaagd: %s", piece.name), 'piece': info}
            if project.stage not in ('sawing', 'prep'):
                return {'kind': 'warning', 'title': self.env._("%s zit in geen open zaagbatch", code),
                        'detail': self.env._("Project staat in fase %s.", dict(project._fields['stage'].selection)[project.stage]),
                        'piece': info}
            piece.write({'sawn': True, 'sawn_on': now})
            project._mc_check_progress()
            next_step = self.env._("CNC") if piece.needs_cnc else self.env._("rechtstreeks naar montage")
            return {'kind': 'success', 'title': self.env._("Gezaagd: %s", piece.name),
                    'detail': self.env._("%(project)s, %(cabinet)s. Volgende stap: %(next)s.",
                                         project=project.display_name, cabinet=piece.cabinet or '-', next=next_step),
                    'piece': info}
        if station == 'cnc':
            if not piece.sawn:
                return {'kind': 'warning', 'title': self.env._("Nog niet gezaagd: %s", piece.name),
                        'detail': self.env._("Dit onderdeel moet eerst langs de paneelzaag."), 'piece': info}
            if not piece.needs_cnc:
                return {'kind': 'info', 'title': self.env._("Geen CNC-bewerking: %s", piece.name),
                        'detail': self.env._("Rechtstreeks naar montage."), 'piece': info}
            if piece.cnc_done:
                return {'kind': 'warning', 'title': self.env._("Al bewerkt: %s", piece.name), 'piece': info}
            return {'kind': 'success', 'title': self.env._("Programma geladen: %s", piece.cnc_program),
                    'detail': self.env._("Start de bewerking en bevestig wanneer ze klaar is."),
                    'piece': info, 'awaiting_cnc': True}
        # assembly
        if project.stage != 'assembly':
            return {'kind': 'warning', 'title': self.env._("%s is nog niet klaar voor montage", piece.name),
                    'detail': self.env._("Project staat in fase %s.", dict(project._fields['stage'].selection)[project.stage]),
                    'piece': info}
        if piece.kitted:
            return {'kind': 'info', 'title': self.env._("Al verzameld: %s", piece.name), 'piece': info}
        piece.kitted = True
        cabinet_pieces = project.piece_ids.filtered(lambda p: p.cabinet == piece.cabinet)
        done = len(cabinet_pieces.filtered('kitted'))
        detail = self.env._("%(done)s/%(total)s onderdelen voor deze kast.", done=done, total=len(cabinet_pieces))
        if done == len(cabinet_pieces):
            detail += " " + self.env._("Kast is compleet: monteren.")
        return {'kind': 'success', 'title': self.env._("Leg bij %(cabinet)s: %(name)s", cabinet=piece.cabinet or '-', name=piece.name),
                'detail': detail, 'piece': info}

    @api.model
    def mc_confirm_cnc(self, piece_id):
        piece = self.browse(piece_id).exists()
        if not piece or not piece.sawn:
            return {'kind': 'warning', 'title': self.env._("Onderdeel niet gevonden of nog niet gezaagd.")}
        piece.write({'cnc_done': True, 'cnc_done_on': fields.Datetime.now()})
        piece.project_id._mc_check_progress()
        return {'kind': 'success', 'title': self.env._("Klaar: %s", piece.name),
                'detail': self.env._("Volgende stap: montage. Scan het volgende onderdeel.")}

    @api.model
    def mc_cabinet_assembled(self, project_id, cabinet):
        project = self.env['mc.project'].browse(project_id).exists()
        pieces = project.piece_ids.filtered(lambda p: (p.cabinet or '-') == cabinet)
        if not pieces or not all(pieces.mapped('kitted')):
            return {'kind': 'warning', 'title': self.env._("Nog niet alle onderdelen van %s zijn verzameld.", cabinet)}
        pieces.write({'assembled': True})
        project.message_post(body=self.env._("Kast %s gemonteerd.", cabinet))
        return {'kind': 'success', 'title': self.env._("%s gemonteerd", cabinet)}
