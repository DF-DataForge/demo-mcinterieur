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

    def test_configurable_intake(self):
        template = self.env.ref('mc_interieur.intake_template_default')
        project = self.env.ref('mc_interieur.project_peeters_keuken')
        self.assertEqual(project._mc_intake('worktop'), 'stone', "Demo answers are stored as properties")
        self.assertEqual(project.quote_vat, '6', "Renovation in the intake gives 6 %")
        total_before = project.intake_total
        # a manager adds a question with options, straight from Odoo
        template.hardware_definition = template.hardware_definition + [{
            'name': 'soft_close_bins', 'string': 'Afvalsysteem', 'type': 'selection',
            'selection': [['yes', 'Ja'], ['no', 'Nee']],
        }]
        project.invalidate_recordset()
        self.assertEqual(project.intake_total, total_before + 1)
        project.drawer_id = self.env.ref('mc_interieur.user_jonas')
        project.action_handoff_drawer()
        question = project.question_ids.filtered(lambda q: q.field_name == 'intake_hardware.soft_close_bins')
        self.assertTrue(question, "An empty configured question becomes an open question for the drawer")
        project._mc_set_intake('intake_hardware.soft_close_bins', 'yes')
        project.write({'intake_hardware': dict(project.intake_hardware)})
        self.assertTrue(question.done, "Answering the intake closes the open question")
        self.assertIn('Afvalsysteem', project.intake_summary_html)

    def test_conditional_intake_question(self):
        Project = self.env['mc.project']
        project = Project.create({
            'name': "Test voorwaarde",
            'partner_id': self.env.ref('mc_interieur.partner_peeters').id,
            'project_type_id': self.env.ref('mc_interieur.project_type_wardrobe').id,
            'intake_general': {'third_party': 'none'},
            'drawer_id': self.env.ref('mc_interieur.user_jonas').id,
        })
        self.assertIn('intake_general.third_party_contact', project.intake_hidden_keys)
        total_hidden = project.intake_total
        project.action_handoff_drawer()
        self.assertFalse(
            project.question_ids.filtered(lambda q: q.field_name == 'intake_general.third_party_contact'),
            "A hidden question does not become an open question")
        project.write({'intake_general': {'third_party': 'architect'}})
        self.assertNotIn('intake_general.third_party_contact', project.intake_hidden_keys)
        self.assertEqual(project.intake_total, total_hidden + 1)
        # an open question for it follows the condition: closed when hidden, reopened when shown again
        question = self.env['mc.project.question'].create({
            'project_id': project.id, 'name': "Contact architect / aannemer?",
            'field_name': 'intake_general.third_party_contact',
        })
        project.write({'intake_general': {'third_party': 'none'}})
        self.assertTrue(question.done)
        self.assertEqual(question.answer, "Niet van toepassing")
        project.write({'intake_general': {'third_party': 'contractor'}})
        self.assertFalse(question.done, "Shown again and still empty: the question is open again")

    def test_demo_invoices_per_project(self):
        self.assertFalse(self.env.ref('base.main_company').uses_default_logo, "MC Interieur logo on the company")
        bathroom = self.env.ref('mc_interieur.project_maes_badkamer')
        invoices = bathroom._mc_portal_invoices()
        self.assertEqual(len(invoices), 1)
        self.assertIn(invoices.payment_state, ('paid', 'in_payment'))
        desk = self.env.ref('mc_interieur.project_desmet_bureau')
        self.assertEqual(desk.invoice_count, 2)
        self.assertEqual(len(desk._mc_portal_invoices().filtered(lambda m: m.payment_state == 'not_paid')), 1)
        self.assertFalse(self.env.ref('mc_interieur.project_maes_keuken').invoice_ids, "Not approved yet: no invoice")

    def test_label_reports_render(self):
        pieces = self.env.ref('mc_interieur.project_vandamme_dressing').piece_ids[:15]
        Report = self.env['ir.actions.report']
        for xmlid in ('mc_interieur.action_report_mc_piece_label', 'mc_interieur.action_report_mc_piece_label_a4'):
            html, _format = Report._render_qweb_html(xmlid, pieces.ids)
            html = html.decode() if isinstance(html, bytes) else str(html)
            self.assertIn(pieces[0].barcode, html)
            self.assertIn('o_mc_label_barcode', html)
        dressing = self.env.ref('mc_interieur.project_vandamme_dressing')
        batch = self.env['mc.cutting.batch'].search([('project_ids', 'in', dressing.ids)], limit=1)
        action = batch.action_print_labels()
        self.assertEqual(action['type'], 'ir.actions.report')

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
class TestMcBackendScreens(HttpCase):
    """Open the main screens in a browser: fails on asset, template or JS errors."""

    def _open(self, path):
        self.browser_js(path, "setTimeout(() => console.log('test successful'), 1500)", login='admin')

    def test_project_kanban(self):
        self._open('/odoo/action-mc_interieur.mc_project_action')

    def test_project_form(self):
        project = self.env.ref('mc_interieur.project_maes_keuken')
        self._open(f'/odoo/action-mc_interieur.mc_project_action/{project.id}')

    def test_scan_station(self):
        self._open('/odoo/action-mc_interieur.mc_scan_station_action_assembly')

    def test_conditional_question_hidden_in_form(self):
        hidden = self.env.ref('mc_interieur.project_maes_keuken')      # architect / aannemer: Geen
        shown = self.env.ref('mc_interieur.project_peeters_keuken')    # architect / aannemer: Aannemer
        for project, expected in ((hidden, False), (shown, True)):
            code = f"""setTimeout(() => {{
                const labels = [...document.querySelectorAll('.o_field_property_label')].map(e => e.textContent);
                const present = labels.some(t => t.includes('Contact architect'));
                if (present === {str(expected).lower()}) {{ console.log('test successful'); }}
                else {{ console.error('Contact question visible: ' + present + ', expected {str(expected).lower()}'); }}
            }}, 2500)"""
            self.browser_js(f'/odoo/action-mc_interieur.mc_project_action/{project.id}', code, login='admin')

    def test_intake_configuration_is_editable(self):
        code = """setTimeout(() => {
            const icons = document.querySelectorAll('.o_field_property_open_popover').length;
            if (icons) { console.log('test successful'); }
            else { console.error('No edit icons next to the intake questions'); }
        }, 3000)"""
        self.browser_js('/odoo/action-mc_interieur.mc_intake_template_action', code, login='admin')


@tagged('post_install', '-at_install')
class TestMcPortal(HttpCase):

    def test_portal_pages(self):
        self.authenticate('karen.maes@example.com', 'demo')
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

    def test_portal_invoices_per_project(self):
        self.authenticate('karen.maes@example.com', 'demo')
        bathroom = self.env.ref('mc_interieur.project_maes_badkamer')
        invoice = bathroom._mc_portal_invoices()
        response = self.url_open(f'/my/interieur/{bathroom.id}')
        self.assertIn('Facturen', response.text)
        self.assertIn(invoice.name, response.text)
        self.assertIn('Betaald', response.text)
        response = self.url_open(invoice.get_portal_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(invoice.name, response.text)

    def test_portal_in_house_colours(self):
        self.assertEqual(self.env.company.email_secondary_color.upper(), '#574A36')
        response = self.url_open('/web/login')
        self.assertIn('--portal-primary-color: #574A36', response.text)

    def test_portal_page_in_browser(self):
        # loads the frontend assets (portal styling) and the portal page as a customer
        project = self.env.ref('mc_interieur.project_maes_keuken')
        self.browser_js(f'/my/interieur/{project.id}', "setTimeout(() => console.log('test successful'), 1500)",
                        login='karen.maes@example.com')

    def test_portal_other_customer_is_redirected(self):
        self.authenticate('tom.vandamme@example.com', 'demo')
        project = self.env.ref('mc_interieur.project_maes_keuken')
        response = self.url_open(f'/my/interieur/{project.id}')
        self.assertNotIn('Vragen van ons', response.text)
