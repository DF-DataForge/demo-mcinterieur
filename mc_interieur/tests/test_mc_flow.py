from odoo.exceptions import UserError
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tools import file_open
from odoo.tools.binary import BinaryBytes


@tagged('post_install', '-at_install')
class TestMcFlow(TransactionCase):

    def test_approval_blocked_while_customer_questions_open(self):
        project = self.env.ref('mc_interieur.project_maes_keuken')
        version = project.version_ids.filtered(lambda v: v.state == 'pending')
        self.assertEqual(project.stage, 'validation')
        self.assertTrue(version.sale_order_id, "The quote is shared together with the drawing")
        with self.assertRaises(UserError):
            version._mc_customer_approve("Karen Maes")
        for question in project.question_ids.filtered('to_customer'):
            question._mc_customer_answer("Ja")
        version._mc_customer_approve("Karen Maes")
        self.assertEqual(version.state, 'approved')
        self.assertEqual(project.stage, 'prep')
        self.assertEqual(version.sale_order_id.state, 'sale')
        self.assertTrue(project.piece_ids)

    def test_quote_needs_material_mapping(self):
        project = self.env.ref('mc_interieur.project_peeters_inkomkast')
        with self.assertRaises(UserError):
            project.action_generate_quote()
        mapping = self.env['mc.material.mapping'].search([('name', '=', 'Eiken fineer 19')])
        mapping.product_id = self.env.ref('mc_interieur.product_fin_eik_19')
        project.part_ids._mc_apply_mapping()
        project.action_generate_quote()
        quote = project.sale_order_ids.filtered(lambda o: o.state == 'draft')
        self.assertEqual(len(quote), 1)
        self.assertGreater(quote.amount_untaxed, 0)

    def _demo_file(self, name):
        with file_open(f'mc_interieur/static/demo_files/{name}', 'rb') as demo_file:
            return BinaryBytes(demo_file.read(), filename=name)

    def test_topsolid_import_then_quote(self):
        project = self.env.ref('mc_interieur.project_peeters_keuken')
        self.assertFalse(project.part_ids)
        wizard = self.env['mc.topsolid.import'].create({
            'project_id': project.id,
            'parts_file': self._demo_file('topsolid_keuken_peeters.csv'),
            'parts_filename': 'topsolid_keuken_peeters.csv',
        })
        wizard.action_import()
        self.assertEqual(len(project.part_ids), 14)
        self.assertTrue(all(project.part_ids.mapped('product_id')), "All kitchen materials are linked")
        self.assertTrue(project.part_ids.filtered(lambda p: p.cabinet == 'O1-O5').edge_l1_id)
        project.action_generate_quote()
        self.assertTrue(project.sale_order_ids)

    def test_ardis_result_file(self):
        tv_wall = self.env.ref('mc_interieur.project_vandamme_tv')
        batch = self.env['mc.cutting.batch'].search([('project_ids', 'in', tv_wall.ids), ('state', '=', 'draft')])
        self.assertEqual(len(batch), 1)
        batch.action_export_ardis()
        self.assertTrue(batch.export_file)
        self.env['mc.ardis.result'].create({
            'batch_id': batch.id,
            'mode': 'file',
            'result_file': self._demo_file('ardis_resultaat_tv_wand_vandamme.csv'),
        }).action_apply()
        self.assertIn(batch.state, ('ready', 'waiting'))
        self.assertEqual(batch.sheets_used, 4)
        self.assertEqual(tv_wall.stage, 'sawing')

    def test_scan_saw_and_cnc(self):
        Piece = self.env['mc.piece']
        dressing = self.env.ref('mc_interieur.project_vandamme_dressing')
        piece = dressing.piece_ids.filtered(lambda p: not p.sawn)[:1]
        self.assertTrue(piece)
        result = Piece.mc_scan('cnc', piece.barcode)
        self.assertEqual(result['kind'], 'warning', "Not sawn yet: the CNC refuses it")
        result = Piece.mc_scan('saw', piece.barcode)
        self.assertEqual(result['kind'], 'success')
        self.assertTrue(piece.sawn)
        result = Piece.mc_scan('saw', piece.barcode)
        self.assertEqual(result['kind'], 'warning', "Scanning twice is reported")
        self.assertEqual(Piece.mc_scan('saw', 'NOPE-123')['kind'], 'warning')

    def test_installation_sign_off(self):
        desk = self.env.ref('mc_interieur.project_desmet_bureau')
        installation = desk.installation_ids[:1]
        self.assertEqual(installation.state, 'planned')
        with file_open('mc_interieur/static/description/icon.png', 'rb') as image:
            signature = BinaryBytes(image.read(), filename='signature.png')
        installation.write({'signed_by': "An De Smet", 'signature': signature})
        with self.assertRaises(UserError):
            installation.action_sign_off()
        installation.check_ids.write({'done': True})
        installation.action_sign_off()
        self.assertEqual(desk.stage, 'delivered')


@tagged('post_install', '-at_install')
class TestMcPortal(HttpCase):

    def test_portal_pages(self):
        self.authenticate('karen', 'demo')
        response = self.url_open('/my/interieur')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Keuken Maes', response.text)
        self.assertIn('Badkamermeubel Maes', response.text)
        self.assertNotIn('Dressing Van Damme', response.text)
        project = self.env.ref('mc_interieur.project_maes_keuken')
        response = self.url_open(f'/my/interieur/{project.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Vragen van ons', response.text)
        self.assertIn('Offerte', response.text)

    def test_portal_other_customer_is_redirected(self):
        self.authenticate('tom', 'demo')
        project = self.env.ref('mc_interieur.project_maes_keuken')
        response = self.url_open(f'/my/interieur/{project.id}')
        self.assertNotIn('Vragen van ons', response.text)
