from datetime import datetime, time, timedelta

from odoo import api, fields, models

# Demo parts lists as they would come out of TopSolid:
# (cabinet, part, TopSolid material, length, width, thickness, quantity, grain, edge code, edge sides, CNC)
DEMO_PARTS = {
    'project_peeters_inkomkast': [
        ('K1 inkomkast', 'Zijwand', 'Melamine Wit 18', 2450, 600, 18, 2, False, 'ABS-WIT-1', 'L1', True),
        ('K1 inkomkast', 'Bodem / top', 'Melamine Wit 18', 1764, 580, 18, 2, False, 'ABS-WIT-1', 'L1', True),
        ('K1 inkomkast', 'Legplank', 'Melamine Wit 18', 1760, 560, 18, 4, False, 'ABS-WIT-1', 'L1', False),
        ('K1 inkomkast', 'Rug', 'HDF Wit 3', 2440, 1790, 3, 1, False, '', '', False),
        ('K1 inkomkast', 'Deur', 'Eiken fineer 19', 2440, 896, 19, 2, True, 'ABS-EIK-1', 'L1L2B1B2', True),
    ],
    'project_maes_keuken': [
        ('O1-O4', 'Zijwand onderkast', 'Melamine Wit 18', 720, 560, 18, 8, False, 'ABS-WIT-1', 'L1', True),
        ('O1-O4', 'Bodem onderkast', 'Melamine Wit 18', 764, 560, 18, 4, False, 'ABS-WIT-1', 'L1', True),
        ('O1-O4', 'Regel', 'Melamine Wit 18', 764, 100, 18, 8, False, '', '', False),
        ('O1-O4', 'Rug onderkast', 'HDF Wit 3', 716, 796, 3, 4, False, '', '', False),
        ('H1', 'Zijwand kolomkast', 'Melamine Wit 18', 2300, 580, 18, 2, False, 'ABS-WIT-1', 'L1', True),
        ('H1', 'Legplank kolomkast', 'Melamine Wit 18', 564, 540, 18, 4, False, 'ABS-WIT-1', 'L1', False),
        ('B1, B2', 'Zijwand bovenkast', 'Melamine Wit 18', 740, 320, 18, 4, False, 'ABS-WIT-1', 'L1L2', True),
        ('O1, O2', 'Front lade', 'MDF 19 lak', 796, 236, 19, 6, False, '', '', True),
        ('O3, O4', 'Front deur', 'MDF 19 lak', 396, 716, 19, 4, False, '', '', True),
        ('H1', 'Front kolomkast', 'MDF 19 lak', 596, 1450, 19, 1, False, '', '', True),
        ('B1, B2', 'Front bovenkast', 'MDF 19 lak', 596, 736, 19, 2, False, '', '', True),
        ('E1', 'Afdekpaneel eiland', 'MDF 19 lak', 2400, 900, 19, 2, False, '', '', True),
    ],
    'project_maes_badkamer': [
        ('K1 wastafelmeubel', 'Zijwand', 'Melamine Wit 18', 500, 450, 18, 2, False, 'ABS-WIT-1', 'L1', True),
        ('K1 wastafelmeubel', 'Bodem', 'Melamine Wit 18', 1164, 450, 18, 1, False, 'ABS-WIT-1', 'L1', True),
        ('K1 wastafelmeubel', 'Front lade', 'MDF 19 lak', 596, 246, 19, 2, False, '', '', True),
        ('K1 wastafelmeubel', 'Rug', 'HDF Wit 3', 1180, 480, 3, 1, False, '', '', False),
        ('K2 spiegelkast', 'Zijwand', 'Melamine Wit 18', 700, 150, 18, 2, False, 'ABS-WIT-1', 'L1', True),
        ('K2 spiegelkast', 'Front deur', 'MDF 19 lak', 596, 696, 19, 2, False, '', '', True),
    ],
    'project_vandamme_dressing': [
        ('D1 kast 1200', 'Zijwand', 'Melamine Eiken 18', 2450, 620, 18, 3, True, 'ABS-EIK-1', 'L1', True),
        ('D1 kast 1200', 'Bodem / top', 'Melamine Eiken 18', 1164, 600, 18, 4, True, 'ABS-EIK-1', 'L1', True),
        ('D1 kast 1200', 'Legplank', 'Melamine Eiken 18', 1160, 580, 18, 6, True, 'ABS-EIK-1', 'L1', False),
        ('D1 kast 1200', 'Rug', 'HDF Wit 3', 2440, 1190, 3, 2, False, '', '', False),
        ('D2 schoenenkast', 'Zijwand', 'Melamine Eiken 18', 2450, 620, 18, 2, True, 'ABS-EIK-1', 'L1', True),
        ('D2 schoenenkast', 'Legplank schuin', 'Melamine Eiken 18', 1164, 350, 18, 6, True, 'ABS-EIK-1', 'L1', True),
        ('D1 + D2', 'Deur', 'MDF 19 lak', 2440, 596, 19, 3, False, '', '', True),
    ],
    'project_vandamme_tv': [
        ('K1 lowboard', 'Zijwand', 'Melamine Antraciet 18', 600, 400, 18, 2, False, 'ABS-ANT-1', 'L1', True),
        ('K1 lowboard', 'Bodem', 'Melamine Antraciet 18', 1800, 400, 18, 1, False, 'ABS-ANT-1', 'L1', True),
        ('K1 lowboard', 'Top', 'Melamine Antraciet 18', 1800, 400, 18, 1, False, 'ABS-ANT-1', 'L1', True),
        ('K1 lowboard', 'Legplank', 'Melamine Antraciet 18', 590, 370, 18, 3, False, 'ABS-ANT-1', 'L1', False),
        ('K1 lowboard', 'Rug', 'HDF Wit 3', 1790, 590, 3, 1, False, '', '', False),
        ('K1 lowboard', 'Front lade', 'MDF 19 lak', 896, 296, 19, 2, False, '', '', True),
        ('K2 wand', 'Wandpaneel', 'MDF 19 lak', 2400, 1200, 19, 2, False, '', '', True),
        ('K2 wand', 'Front klep', 'MDF 19 lak', 596, 296, 19, 2, False, '', '', True),
    ],
    'project_desmet_bureau': [
        ('K1 bureau', 'Zijwand', 'Melamine Eiken 18', 720, 600, 18, 2, True, 'ABS-EIK-1', 'L1', True),
        ('K1 bureau', 'Blad', 'Melamine Eiken 18', 1600, 700, 18, 1, True, 'ABS-EIK-1', 'L1L2B1B2', True),
        ('K1 bureau', 'Front lade', 'Melamine Eiken 18', 446, 146, 18, 2, True, 'ABS-EIK-1', 'L1L2B1B2', True),
        ('K2 boekenkast', 'Zijwand', 'Melamine Eiken 18', 2000, 350, 18, 2, True, 'ABS-EIK-1', 'L1', True),
        ('K2 boekenkast', 'Legplank', 'Melamine Eiken 18', 764, 330, 18, 5, True, 'ABS-EIK-1', 'L1', False),
        ('K2 boekenkast', 'Rug', 'HDF Wit 3', 1996, 796, 3, 1, False, '', '', False),
    ],
}

DEMO_STOCK = {
    'MEL-WIT-18': 30, 'MEL-ANT-18': 2, 'MEL-EIK-18': 14, 'MDF-LAK-19': 3, 'FIN-EIK-19': 1, 'HDF-WIT-3': 15,
    'ABS-WIT-1': 450, 'ABS-ANT-1': 60, 'ABS-EIK-1': 160,
    'HW-SCHARNIER': 200, 'HW-LADE-STD': 40, 'HW-LADE-PREM': 20, 'HW-GREEP': 60, 'HW-KNOP': 40,
    'HW-PLANKDRAGER': 1000, 'HW-STELPOOT': 200, 'HW-OPHANG': 30, 'HW-EXCENTER': 1000, 'HW-LED': 6,
}


class McProject(models.Model):
    # Demo data loader, called once from demo/mc_project_demo.xml. Kept apart from the business code.
    _inherit = 'mc.project'

    @api.model
    def _mc_demo_setup(self):
        ref = self.env.ref
        maes_keuken = ref('mc_interieur.project_maes_keuken', raise_if_not_found=False)
        if not maes_keuken or maes_keuken.part_ids:
            return True  # demo records missing, or the setup already ran
        Product = self.env['product.product']
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        for code, qty in DEMO_STOCK.items():
            product = Product.search([('default_code', '=', code)], limit=1)
            if product and warehouse:
                self.env['stock.quant']._update_available_quantity(product, warehouse.lot_stock_id, qty)

        edges = {p.default_code: p for p in Product.search([('mc_kind', '=', 'edge')])}
        part_vals = []
        for xmlid, rows in DEMO_PARTS.items():
            project = ref(f'mc_interieur.{xmlid}')
            for sequence, row in enumerate(rows, start=1):
                cabinet, name, material, length, width, thickness, qty, grain, edge_code, sides, cnc = row
                edge = edges.get(edge_code, Product)
                part_vals.append({
                    'project_id': project.id, 'sequence': sequence, 'cabinet': cabinet, 'name': name,
                    'topsolid_material': material, 'length': length, 'width': width, 'thickness': thickness,
                    'quantity': qty, 'grain': grain,
                    'edge_l1_id': edge.id if 'L1' in sides else False,
                    'edge_l2_id': edge.id if 'L2' in sides else False,
                    'edge_w1_id': edge.id if 'B1' in sides else False,
                    'edge_w2_id': edge.id if 'B2' in sides else False,
                    'cnc_program': f"{project.ref}_{sequence:03d}.tsw" if cnc else False,
                })
        self.env['mc.part'].create(part_vals)
        projects_with_parts = [ref(f'mc_interieur.{xmlid}') for xmlid in DEMO_PARTS]
        for project in projects_with_parts:
            project.parts_imported_on = fields.Datetime.now() - timedelta(days=2)

        # Approved by the customer through the portal
        signers = {
            'project_maes_badkamer': "Karen Maes",
            'project_desmet_bureau': "An De Smet",
            'project_vandamme_dressing': "Tom Van Damme",
            'project_vandamme_tv': "Tom Van Damme",
        }
        for xmlid, signer in signers.items():
            project = ref(f'mc_interieur.{xmlid}')
            project.action_generate_quote()
            project.action_send_to_customer()
            project.current_version_id._mc_customer_approve(signer)

        # Waiting for the customer: quote generated and shared with version 2
        maes_keuken = ref('mc_interieur.project_maes_keuken')
        maes_keuken.action_generate_quote()
        maes_keuken.action_send_to_customer()

        Batch = self.env['mc.cutting.batch']
        Result = self.env['mc.ardis.result']
        # Batch already sawn: bathroom (now at the CNC) and desk (in assembly)
        maes_badkamer = ref('mc_interieur.project_maes_badkamer')
        desmet = ref('mc_interieur.project_desmet_bureau')
        batch_done = Batch.create({'project_ids': [(6, 0, (maes_badkamer | desmet).ids)]})
        batch_done.action_export_ardis()
        Result.create({'batch_id': batch_done.id, 'mode': 'simulate'}).action_apply()
        (maes_badkamer | desmet).piece_ids.write({'sawn': True, 'sawn_on': fields.Datetime.now() - timedelta(days=3)})
        (maes_badkamer | desmet)._mc_check_progress()
        desmet.piece_ids.filtered('needs_cnc').write({'cnc_done': True})
        bathroom_cnc = maes_badkamer.piece_ids.filtered('needs_cnc')
        bathroom_cnc[:len(bathroom_cnc) // 2].write({'cnc_done': True})
        (maes_badkamer | desmet)._mc_check_progress()
        batch_done.action_mark_sawn()
        desk_pieces = desmet.piece_ids.filtered(lambda p: p.cabinet == 'K1 bureau')
        desk_pieces.write({'kitted': True, 'assembled': True})
        bookcase = desmet.piece_ids - desk_pieces
        bookcase[:len(bookcase) // 2].write({'kitted': True})

        # Batch at the saw: dressing half sawn
        dressing = ref('mc_interieur.project_vandamme_dressing')
        batch_saw = Batch.create({'project_ids': [(6, 0, dressing.ids)]})
        batch_saw.action_export_ardis()
        Result.create({'batch_id': batch_saw.id, 'mode': 'simulate'}).action_apply()
        dressing_pieces = dressing.piece_ids
        dressing_pieces[:len(dressing_pieces) * 2 // 5].write({'sawn': True})

        # Draft batch for the TV wall: shows the shortage and the order button
        Batch.create({'project_ids': [(6, 0, ref('mc_interieur.project_vandamme_tv').ids)]})

        # Installation planning (relative to today, 08:00)
        today = fields.Date.context_today(self)
        monday = today - timedelta(days=today.weekday())

        def at(day, hour=7):
            return datetime.combine(day, time(hour, 0))

        Installation = self.env['mc.installation']
        desk_installation = Installation.create({
            'project_id': desmet.id, 'team_id': ref('mc_interieur.team_1').id,
            'date_start': at(monday + timedelta(days=3)), 'date_stop': at(monday + timedelta(days=3), 16),
        })
        desk_installation.check_ids[:2].write({'done': True})
        Installation.create({
            'project_id': dressing.id, 'team_id': ref('mc_interieur.team_2').id,
            'date_start': at(monday + timedelta(days=8)), 'date_stop': at(monday + timedelta(days=9), 16),
        })
        Installation.create({'project_id': maes_badkamer.id})
        return True
