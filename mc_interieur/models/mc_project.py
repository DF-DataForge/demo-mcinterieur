import math
from html import escape

from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from .mc_intake_template import INTAKE_SECTIONS

STAGES = [
    ('intake', "Intake"),
    ('drawing', "Tekening"),
    ('validation', "Klantvalidatie"),
    ('prep', "Werkvoorbereiding"),
    ('sawing', "Zagen"),
    ('cnc', "CNC"),
    ('assembly', "Montage & plaatsing"),
    ('delivered', "Opgeleverd"),
]

CABINET_PREFIX = {
    'O': "Onderkasten", 'B': "Bovenkasten", 'H': "Kolomkast", 'E': "Eiland",
    'K': "Kasten", 'D': "Dressing",
}

SHEET_YIELD = 0.82


class McProject(models.Model):
    _name = 'mc.project'
    _description = "Interieurproject"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # ------------------------------------------------------------------
    # General
    # ------------------------------------------------------------------
    name = fields.Char(string="Project", required=True, tracking=True)
    ref = fields.Char(string="Referentie", readonly=True, copy=False, default="/", index='trigram')
    stage = fields.Selection(
        STAGES, string="Fase", default='intake', required=True, tracking=True,
        group_expand=True, copy=False)
    partner_id = fields.Many2one('res.partner', string="Klant", required=True, tracking=True, index=True)
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id', store=True, index=True, string="Klant (bedrijf)")
    city = fields.Char(string="Gemeente werf")
    street = fields.Char(string="Adres werf")
    user_id = fields.Many2one(
        'res.users', string="Verkoper", default=lambda self: self.env.user, tracking=True,
        domain=[('share', '=', False)])
    drawer_id = fields.Many2one(
        'res.users', string="Tekenaar", tracking=True, domain=[('share', '=', False)])
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    color = fields.Integer(string="Kleur")
    notes = fields.Html(string="Notities intakegesprek")
    attachment_ids = fields.Many2many(
        'ir.attachment', string="Foto's en plannen",
        help="Foto's van de ruimte, schetsen op papier, architectenplannen.")

    # ------------------------------------------------------------------
    # Intake: all optional, nothing blocks the flow. The questions and their options are
    # configured in Odoo (Configuratie > Intakevragen) and stored as properties.
    # ------------------------------------------------------------------
    project_type_id = fields.Many2one('mc.project.type', string="Type project", tracking=True, index='btree_not_null')
    show_appliances = fields.Boolean(related='project_type_id.show_appliances')
    desired_date = fields.Date(string="Gewenste plaatsing")
    intake_template_id = fields.Many2one(
        'mc.intake.template', string="Intakesjabloon", required=True,
        default=lambda self: self.env.ref('mc_interieur.intake_template_default', raise_if_not_found=False))
    intake_general = fields.Properties("Algemeen", definition='intake_template_id.general_definition', copy=True)
    intake_space = fields.Properties("Ruimte & opmeting", definition='intake_template_id.space_definition', copy=True)
    intake_materials = fields.Properties(
        "Materialen & afwerking", definition='intake_template_id.materials_definition', copy=True)
    intake_hardware = fields.Properties("Beslag & indeling", definition='intake_template_id.hardware_definition', copy=True)
    intake_appliances = fields.Properties(
        "Werkblad & toestellen", definition='intake_template_id.appliances_definition', copy=True)
    intake_installation = fields.Properties(
        "Plaatsing", definition='intake_template_id.installation_definition', copy=True)

    intake_progress = fields.Integer(string="Intake ingevuld (%)", compute='_compute_intake_progress')
    intake_missing = fields.Integer(string="Lege intakevragen", compute='_compute_intake_progress')
    intake_answered = fields.Integer(string="Beantwoorde intakevragen", compute='_compute_intake_progress')
    intake_total = fields.Integer(string="Intakevragen", compute='_compute_intake_progress')
    attachment_count = fields.Integer(string="Foto's en plannen ", compute='_compute_attachment_count')
    topsolid_folder = fields.Char(string="TopSolid-projectmap", compute='_compute_topsolid_folder')
    intake_hidden_keys = fields.Json(
        string="Verborgen intakevragen", compute='_compute_intake_hidden_keys',
        help="Vragen die door een voorwaarde niet getoond worden.")
    intake_summary_html = fields.Html(
        string="Samenvatting intake", compute='_compute_intake_summary_html', sanitize=True)

    # ------------------------------------------------------------------
    # Questions, drawings, quotes
    # ------------------------------------------------------------------
    question_ids = fields.One2many('mc.project.question', 'project_id', string="Open vragen")
    open_question_count = fields.Integer(compute='_compute_question_counts', string="Open vragen ")
    customer_question_count = fields.Integer(compute='_compute_question_counts', string="Open vragen klant")
    version_ids = fields.One2many('mc.drawing.version', 'project_id', string="Tekeningversies")
    current_version_id = fields.Many2one('mc.drawing.version', compute='_compute_current_version', string="Huidige versie")
    sale_order_ids = fields.One2many('sale.order', 'mc_project_id', string="Offertes")
    quote_count = fields.Integer(compute='_compute_quote_count')

    quote_margin = fields.Float(string="Marge eigen productie (%)", default=35.0)
    quote_margin_external = fields.Float(string="Marge extern (%)", default=10.0)
    quote_discount = fields.Float(string="Korting (%)")
    quote_install_days = fields.Integer(
        string="Plaatsing (dagen)", compute='_compute_quote_defaults', store=True, readonly=False)
    quote_worktop_amount = fields.Monetary(
        string="Werkblad (raming)", compute='_compute_quote_defaults', store=True, readonly=False)
    quote_appliance_amount = fields.Monetary(
        string="Toestellen (budget)", compute='_compute_quote_defaults', store=True, readonly=False)
    quote_vat = fields.Selection(
        [('6', "6 % (renovatie woning ouder dan 10 jaar)"), ('21', "21 %")], string="Btw",
        compute='_compute_quote_defaults', store=True, readonly=False)
    quote_deposit = fields.Float(string="Voorschot (%)", default=30.0)
    quote_preview_html = fields.Html(string="Calculatie", compute='_compute_quote_preview', sanitize=False)

    # ------------------------------------------------------------------
    # Production
    # ------------------------------------------------------------------
    part_ids = fields.One2many('mc.part', 'project_id', string="Onderdelen (TopSolid)")
    part_count = fields.Integer(compute='_compute_part_count')
    parts_imported_on = fields.Datetime(string="Materiaallijst ingelezen op")
    piece_ids = fields.One2many('mc.piece', 'project_id', string="Etiketten")
    piece_progress = fields.Char(compute='_compute_piece_progress', string="Productie")
    batch_ids = fields.Many2many('mc.cutting.batch', string="Zaagbatches", copy=False)
    hardware_html = fields.Html(string="Picklijst beslag", compute='_compute_hardware_html', sanitize=False)
    installation_ids = fields.One2many('mc.installation', 'project_id', string="Plaatsingen")

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('project_type_id', 'intake_template_id', 'intake_template_id.condition_ids.when_option',
                 *[section[0] for section in INTAKE_SECTIONS])
    def _compute_intake_progress(self):
        for project in self:
            items = project._mc_intake_items()
            done = sum(1 for item in items if item['filled']) + (1 if project.project_type_id else 0)
            total = len(items) + 1
            project.intake_progress = round(done * 100 / total)
            project.intake_missing = total - done
            project.intake_answered = done
            project.intake_total = total

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for project in self:
            project.attachment_count = len(project.attachment_ids)

    @api.depends('ref', 'partner_id.name')
    def _compute_topsolid_folder(self):
        for project in self:
            customer = ''.join((project.partner_id.name or 'klant').split())
            project.topsolid_folder = f"\\\\server\\TopSolid\\Projecten\\{project.ref}_{customer}"

    @api.depends('intake_template_id.condition_ids.question_key', 'intake_template_id.condition_ids.when_option',
                 *[section[0] for section in INTAKE_SECTIONS])
    def _compute_intake_hidden_keys(self):
        for project in self:
            project.intake_hidden_keys = sorted(project._mc_intake_hidden_keys())

    @api.depends('project_type_id', 'intake_template_id', *[section[0] for section in INTAKE_SECTIONS])
    def _compute_intake_summary_html(self):
        for project in self:
            rows = []
            current_tab = None
            for item in project._mc_intake_items():
                if not item['filled']:
                    continue
                tab = dict((s[0], s[2]) for s in INTAKE_SECTIONS)[item['field']]
                if tab != current_tab:
                    rows.append(f"<tr><th colspan='2' class='pt-3'>{escape(tab)}</th></tr>")
                    current_tab = tab
                rows.append(f"<tr><td class='text-muted'>{escape(item['string'])}</td>"
                            f"<td>{escape(project._mc_intake_label(item))}</td></tr>")
            project.intake_summary_html = (
                f"<table class='table table-sm o_mc_table'><tbody>{''.join(rows)}</tbody></table>" if rows
                else f"<p class='text-muted'>{escape(self.env._('Nog niets ingevuld.'))}</p>")

    def _mc_intake_label(self, item):
        """Readable answer: the option label for a choice, the value otherwise."""
        if item['type'] == 'selection':
            for field_name, definition_field, _label in INTAKE_SECTIONS:
                if field_name == item['field']:
                    for definition in self.intake_template_id[definition_field] or []:
                        if definition['name'] == item['name']:
                            return dict(definition.get('selection') or []).get(item['value'], item['value'])
        if item['type'] == 'boolean':
            return self.env._("Ja") if item['value'] else self.env._("Nee")
        return str(item['value'])

    @api.depends('question_ids.done', 'question_ids.to_customer')
    def _compute_question_counts(self):
        for project in self:
            open_questions = project.question_ids.filtered(lambda q: not q.done)
            project.open_question_count = len(open_questions)
            project.customer_question_count = len(open_questions.filtered('to_customer'))

    @api.depends('version_ids.number')
    def _compute_current_version(self):
        for project in self:
            project.current_version_id = project.version_ids.sorted('number')[-1:] if project.version_ids else False

    @api.depends('sale_order_ids')
    def _compute_quote_count(self):
        for project in self:
            project.quote_count = len(project.sale_order_ids)

    @api.depends('part_ids')
    def _compute_part_count(self):
        for project in self:
            project.part_count = len(project.part_ids)

    @api.depends('piece_ids.sawn', 'piece_ids.cnc_done', 'piece_ids.kitted')
    def _compute_piece_progress(self):
        for project in self:
            pieces = project.piece_ids
            if not pieces:
                project.piece_progress = False
                continue
            project.piece_progress = self.env._(
                "%(sawn)s/%(total)s gezaagd, %(cnc)s/%(cnc_total)s CNC, %(kit)s/%(total)s verzameld",
                sawn=len(pieces.filtered('sawn')), total=len(pieces),
                cnc=len(pieces.filtered('cnc_done')), cnc_total=len(pieces.filtered('needs_cnc')),
                kit=len(pieces.filtered('kitted')),
            )

    @api.depends('project_type_id', 'intake_general', 'intake_appliances')
    def _compute_quote_defaults(self):
        for project in self:
            project.quote_install_days = project.project_type_id.default_install_days or 1
            project.quote_worktop_amount = 2400.0 if project._mc_intake('worktop') in ('stone', 'ceramic') else 0.0
            project.quote_appliance_amount = (
                4800.0 if project.project_type_id.code == 'kitchen' and project._mc_intake('appliance_supply') == 'us'
                else 0.0)
            project.quote_vat = '21' if project._mc_intake('situation') == 'new' else '6'

    @api.depends('part_ids', 'quote_margin', 'quote_margin_external', 'quote_discount', 'quote_install_days',
                 'quote_worktop_amount', 'quote_appliance_amount', 'quote_vat', 'quote_deposit')
    def _compute_quote_preview(self):
        for project in self:
            if not project.part_ids:
                project.quote_preview_html = False
                continue
            calc = project._mc_quote_calc()
            project.quote_preview_html = project._mc_render_calc(calc)

    @api.depends('part_ids', 'intake_hardware')
    def _compute_hardware_html(self):
        for project in self:
            lines = project._mc_hardware_lines()
            if not lines:
                project.hardware_html = False
                continue
            rows = ''.join(
                f"<tr><td>{qty:g}</td><td>{product.display_name}</td></tr>" for product, qty in lines)
            project.hardware_html = (
                "<table class='table table-sm o_mc_table'><thead><tr><th>Aantal</th><th>Beslag</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>")

    def _compute_access_url(self):
        super()._compute_access_url()
        for project in self:
            project.access_url = f'/my/interieur/{project.id}'

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', '/') == '/':
                vals['ref'] = self.env['ir.sequence'].next_by_code('mc.project') or '/'
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if any(section[0] in vals for section in INTAKE_SECTIONS) or vals.get('project_type_id'):
            for project in self:
                filled = {item['key'] for item in project._mc_intake_items() if item['filled']}
                if project.project_type_id:
                    filled.add('project_type_id')
                project.question_ids.filtered(lambda q: not q.done and q.field_name in filled).write({'done': True})
            self._mc_sync_hidden_questions()
        return result

    def _mc_sync_hidden_questions(self):
        """Open questions follow the conditions: a question that is hidden is closed as not applicable,
        and reopened when it shows again while still unanswered."""
        not_applicable = self.env._("Niet van toepassing")
        for project in self:
            hidden = project._mc_intake_hidden_keys()
            questions = project.question_ids.filtered(lambda q: q.field_name)
            questions.filtered(lambda q: not q.done and q.field_name in hidden).write(
                {'done': True, 'answer': not_applicable})
            filled = {item['key'] for item in project._mc_intake_items() if item['filled']}
            questions.filtered(
                lambda q: q.done and q.answer == not_applicable and q.field_name not in hidden
                and q.field_name not in filled and not q.answered_by_customer
            ).write({'done': False, 'answer': False})

    @api.model
    def _mc_sync_all_hidden_questions(self):
        """Called on every module update (data/mc_intake_sync_data.xml) and when conditions change."""
        self.search([('question_ids', '!=', False)])._mc_sync_hidden_questions()
        return True

    # ------------------------------------------------------------------
    # Intake helpers
    # ------------------------------------------------------------------
    def _mc_intake_sections(self):
        """Intake tabs that apply to this project (the appliances tab only for some project types)."""
        self.ensure_one()
        return [section for section in INTAKE_SECTIONS
                if section[0] != 'intake_appliances' or self.project_type_id.show_appliances]

    def _mc_intake_hidden_keys(self):
        """Questions hidden by a condition (Configuratie > Intakevragen > Voorwaarden) for this project."""
        self.ensure_one()
        wanted = {}
        for condition in self.intake_template_id.condition_ids:
            wanted.setdefault(condition.question_key, []).append(condition.when_option)
        hidden = set()
        for question_key, options in wanted.items():
            for option in options:
                question, _sep, value = (option or '').partition('|')
                field_name, _dot, name = question.partition('.')
                values = self[field_name] if field_name in self._fields else None
                if values and values.get(name) == value:
                    break
            else:
                hidden.add(question_key)
        return hidden

    def _mc_intake_items(self, include_hidden=False):
        """Every intake question shown for this project: key (field.name), label, type, value, filled."""
        self.ensure_one()
        items = []
        template = self.intake_template_id
        hidden = set() if include_hidden else self._mc_intake_hidden_keys()
        for field_name, definition_field, _label in self._mc_intake_sections():
            values = self[field_name]
            for definition in template[definition_field] or []:
                if definition.get('type') == 'separator':
                    continue
                if f"{field_name}.{definition['name']}" in hidden:
                    continue
                value = values.get(definition['name']) if values else None
                items.append({
                    'key': f"{field_name}.{definition['name']}",
                    'field': field_name,
                    'name': definition['name'],
                    'string': definition.get('string') or definition['name'],
                    'type': definition.get('type'),
                    'value': value,
                    'filled': value not in (None, False, '', 0, []),
                })
        return items

    def _mc_intake(self, name):
        """Value of an intake question by its technical name, on any tab (False when empty or removed)."""
        self.ensure_one()
        for field_name, _definition, _label in INTAKE_SECTIONS:
            values = self[field_name]
            if values and name in values:
                return values.get(name) or False
        return False

    def _mc_set_intake(self, key, value):
        """Write one intake answer, given its key "field.name"."""
        self.ensure_one()
        field_name, name = key.split('.', 1)
        values = dict(self[field_name] or {})
        values[name] = value
        self[field_name] = values

    def _mc_notify_customer_questions(self):
        for project in self:
            project.message_post(
                body=self.env._("Er staan nieuwe vragen voor u klaar in het klantportaal."),
                partner_ids=project.partner_id.ids,
                subtype_xmlid='mail.mt_comment',
            )

    @api.depends('ref', 'name')
    def _compute_display_name(self):
        for project in self:
            project.display_name = f"{project.ref} {project.name}" if project.ref and project.ref != '/' else project.name

    # ------------------------------------------------------------------
    # Actions: intake and drawing
    # ------------------------------------------------------------------
    def action_handoff_drawer(self):
        """Send the intake to the drawer. Empty intake questions become open questions."""
        for project in self:
            if not project.drawer_id:
                raise UserError(self.env._("Kies eerst een tekenaar voor %s.", project.display_name))
            existing = set(project.question_ids.filtered(lambda q: not q.done).mapped('field_name'))
            new_questions = []
            for item in project._mc_intake_items():
                if not item['filled'] and item['key'] not in existing:
                    new_questions.append(Command.create({
                        'name': self.env._("%s?", item['string']),
                        'field_name': item['key'],
                    }))
            if not project.project_type_id and 'project_type_id' not in existing:
                new_questions.append(Command.create({'name': self.env._("Type project?"), 'field_name': 'project_type_id'}))
            project.write({'stage': 'drawing', 'question_ids': new_questions})
            project.activity_schedule(
                'mail.mail_activity_data_todo', user_id=project.drawer_id.id,
                summary=self.env._("Tekening maken in TopSolid"),
                note=self.env._("Gebruik projectreferentie %s als naam van het TopSolid-project.", project.ref))
            project.message_post(body=self.env._(
                "Intake doorgestuurd naar %(drawer)s. %(count)s lege vragen toegevoegd als open vragen.",
                drawer=project.drawer_id.name, count=len(new_questions)))
        return True

    def action_send_to_customer(self):
        """Share the newest drawing version together with the draft quote in the customer portal."""
        self.ensure_one()
        version = self.version_ids.filtered(lambda v: v.state == 'draft').sorted('number')[-1:]
        if not version:
            raise UserError(self.env._("Voeg eerst een tekeningversie toe (tab Tekening)."))
        quote = self.sale_order_ids.filtered(lambda o: o.state == 'draft' and not o.mc_version_id)[-1:]
        if not quote:
            raise UserError(self.env._(
                "Genereer eerst de offerte uit de TopSolid-materiaallijst: tekening en offerte gaan samen naar de klant."))
        previous = self.sale_order_ids.filtered(lambda o: o.state in ('draft', 'sent') and o.mc_version_id)
        previous._action_cancel()
        self.version_ids.filtered(lambda v: v.state == 'pending').write({'state': 'superseded'})
        version.write({'state': 'pending', 'shared_on': fields.Datetime.now()})
        quote.write({'mc_version_id': version.id, 'state': 'sent'})
        self.stage = 'validation'
        self._portal_ensure_token()
        self.message_post(
            body=self.env._(
                "Tekening versie %(version)s en offerte %(quote)s (%(amount)s) gedeeld in het klantportaal.",
                version=version.number, quote=quote.name,
                amount=quote.currency_id.format(quote.amount_total)),
            partner_ids=self.partner_id.ids,
            subtype_xmlid='mail.mt_comment',
        )
        return True

    def action_view_portal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': self.get_portal_url(),
        }

    def action_view_questions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Open vragen"),
            'res_model': 'mc.project.question',
            'view_mode': 'list',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id, 'search_default_open': 1},
        }

    def action_view_quotes(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('sale.action_quotations_with_onboarding')
        action['domain'] = [('mc_project_id', '=', self.id)]
        action['context'] = {'default_mc_project_id': self.id, 'default_partner_id': self.partner_id.id}
        return action

    # ------------------------------------------------------------------
    # Quote from the TopSolid material list
    # ------------------------------------------------------------------
    def _mc_rate(self, key, default):
        return self.env['ir.config_parameter'].sudo().get_float(f'mc_interieur.{key}', default)

    def _mc_cabinet_label(self, cabinet):
        cabinet = (cabinet or '').strip()
        words = cabinet.split(' ', 1)
        if len(words) == 2 and words[0][:1].isalpha() and words[0][1:2].isdigit() and words[1][:1].isalpha():
            return words[1][:1].upper() + words[1][1:]
        return CABINET_PREFIX.get(cabinet[:1].upper(), self.env._("Meubel %s", cabinet))

    def _mc_find_hardware(self, code):
        return self.env['product.product'].search([('default_code', '=', code)], limit=1)

    def _mc_hardware_lines(self):
        """Hardware pick list derived from the parts list and the intake choices."""
        self.ensure_one()
        totals = {}

        def add(code, qty):
            totals[code] = totals.get(code, 0) + qty

        handles = self._mc_intake('handles')
        grip = {'handles': 'HW-GREEP', 'knobs': 'HW-KNOP'}.get(handles)
        drawer = {'premium': 'HW-LADE-PREM', 'wood': 'HW-LADE-HOUT'}.get(self._mc_intake('drawers'), 'HW-LADE-STD')
        for part in self.part_ids:
            name = (part.name or '').lower()
            if any(key in name for key in ('deur', 'klep', 'front kolom', 'front boven')):
                hinges = 4 if part.length > 1800 else 3 if part.length > 900 else 2
                add('HW-SCHARNIER', hinges * part.quantity)
                if grip:
                    add(grip, part.quantity)
            if 'front lade' in name:
                add(drawer, part.quantity)
                if grip:
                    add(grip, part.quantity)
            if 'legplank' in name:
                add('HW-PLANKDRAGER', 4 * part.quantity)
            if 'bodem onderkast' in name or name == 'bodem':
                add('HW-STELPOOT', 4 * part.quantity)
            if 'zijwand bovenkast' in name:
                add('HW-OPHANG', part.quantity / 2)
            if 'zijwand' in name:
                add('HW-EXCENTER', 4 * part.quantity)
        lighting = self._mc_intake('lighting')
        if lighting and lighting != 'none' and self.part_ids:
            add('HW-LED', 1)
        lines = []
        for code, qty in totals.items():
            product = self._mc_find_hardware(code)
            if product:
                lines.append((product, math.ceil(qty)))
        return lines

    def _mc_quote_calc(self):
        """Cost price and selling price per furniture group, based on the TopSolid parts."""
        self.ensure_one()
        rate_lacquer = self._mc_rate('rate_lacquer_m2', 85.0)
        rate_machine = self._mc_rate('rate_machine_hour', 95.0)
        rate_labour = self._mc_rate('rate_labour_hour', 62.0)
        rate_day = self._mc_rate('rate_install_day', 992.0)
        saw_min = self._mc_rate('saw_minutes_piece', 2.0)
        cnc_min = self._mc_rate('cnc_minutes_piece', 4.0)
        assembly_h = self._mc_rate('assembly_hours_cabinet', 1.5)
        margin = 1 + self.quote_margin / 100
        margin_ext = 1 + self.quote_margin_external / 100

        groups = {}
        cost = {'material': 0.0, 'lacquer': 0.0, 'edge': 0.0, 'machine': 0.0, 'assembly': 0.0}
        missing = set()
        for part in self.part_ids:
            area = part.area
            part_cost = 0.0
            plate = part.product_id
            if not plate or not plate.standard_price:
                missing.add(part.topsolid_material or part.name)
            else:
                sheet_m2 = (plate.mc_sheet_length or 2800) * (plate.mc_sheet_width or 2070) / 1e6
                value = area * plate.standard_price / (sheet_m2 * SHEET_YIELD)
                cost['material'] += value
                part_cost += value
            if plate and plate.default_code and 'LAK' in plate.default_code:
                value = area * 2 * rate_lacquer
                cost['lacquer'] += value
                part_cost += value
            for edge, length in part._mc_edges():
                value = length * part.quantity / 1000 * 1.1 * edge.standard_price
                cost['edge'] += value
                part_cost += value
            minutes = (saw_min + (cnc_min if part.cnc_program else 0)) * part.quantity
            value = minutes / 60 * rate_machine
            cost['machine'] += value
            part_cost += value
            group = groups.setdefault(part.cabinet or '-', {'cost': 0.0, 'names': [], 'side_panels': 0})
            group['cost'] += part_cost
            if part.name not in group['names']:
                group['names'].append(part.name)
            if 'zijwand' in (part.name or '').lower():
                group['side_panels'] += part.quantity
        for group in groups.values():
            hours = max(1, round(group['side_panels'] / 2)) * assembly_h
            group['cost'] += hours * rate_labour
            cost['assembly'] += hours * rate_labour

        sections = {}
        for cabinet, group in groups.items():
            label = self._mc_cabinet_label(cabinet)
            section = sections.setdefault(label, {'amount': 0.0, 'names': []})
            section['amount'] += group['cost'] * margin
            section['names'] += [n.lower() for n in group['names'] if n.lower() not in section['names']]
        lines = [{
            'label': label, 'description': ", ".join(data['names'][:5]), 'amount': data['amount'],
            'product': 'mc_interieur.product_mc_furniture',
        } for label, data in sections.items()]

        hardware = self._mc_hardware_lines()
        hardware_cost = sum(product.standard_price * qty for product, qty in hardware)
        if hardware_cost:
            lines.append({
                'label': self.env._("Beslag en verlichting"),
                'description': ", ".join(p.name.lower() for p, _qty in hardware[:3]),
                'amount': hardware_cost * margin, 'product': 'mc_interieur.product_mc_hardware',
            })
        install_cost = self.quote_install_days * rate_day
        if install_cost:
            lines.append({
                'label': self.env._("Levering en plaatsing"),
                'description': self.env._("%s dag(en), ploeg van 2", self.quote_install_days),
                'amount': install_cost * margin, 'product': 'mc_interieur.product_mc_installation',
            })
        if self.quote_worktop_amount:
            lines.append({
                'label': self.env._("Werkblad"), 'description': self.env._("via steenhouwer, raming op basis van plan"),
                'amount': self.quote_worktop_amount * margin_ext, 'product': 'mc_interieur.product_mc_worktop',
            })
        if self.quote_appliance_amount:
            lines.append({
                'label': self.env._("Inbouwtoestellen"), 'description': self.env._("budget volgens gekozen toestellen"),
                'amount': self.quote_appliance_amount * margin_ext, 'product': 'mc_interieur.product_mc_appliances',
            })
        subtotal = sum(line['amount'] for line in lines)
        discount = subtotal * self.quote_discount / 100
        net = subtotal - discount
        vat = net * int(self.quote_vat or '21') / 100
        total_cost = (sum(cost.values()) + hardware_cost + install_cost
                      + self.quote_worktop_amount + self.quote_appliance_amount)
        return {
            'lines': lines, 'cost': cost, 'hardware_cost': hardware_cost, 'install_cost': install_cost,
            'total_cost': total_cost, 'subtotal': subtotal, 'discount': discount, 'net': net,
            'vat': vat, 'total': net + vat, 'missing': sorted(missing),
        }

    def _mc_render_calc(self, calc):
        fmt = self.currency_id.format
        rows = ''.join(
            f"<tr><td><b>{line['label']}</b><br/><small class='text-muted'>{line['description']}</small></td>"
            f"<td class='text-end'>{fmt(line['amount'])}</td></tr>" for line in calc['lines'])
        cost_rows = ''.join(
            f"<tr><td>{label}</td><td class='text-end'>{fmt(value)}</td></tr>" for label, value in [
                ("Plaatmateriaal", calc['cost']['material']), ("Lakwerk", calc['cost']['lacquer']),
                ("Kantenband", calc['cost']['edge']), ("Machinetijd zaag + CNC", calc['cost']['machine']),
                ("Montage werkplaats", calc['cost']['assembly']), ("Beslag", calc['hardware_cost']),
                ("Plaatsing", calc['install_cost']),
                ("Extern (werkblad, toestellen)", self.quote_worktop_amount + self.quote_appliance_amount),
            ] if value)
        margin = calc['net'] - calc['total_cost']
        margin_pct = round(margin / calc['net'] * 100) if calc['net'] else 0
        warning = ''
        if calc['missing']:
            warning = (
                "<div class='alert alert-warning'>Geen prijs voor: " + ", ".join(calc['missing'])
                + ". Koppel het materiaal in Configuratie &gt; Materiaalkoppeling of geef het artikel een kostprijs.</div>")
        return (
            f"{warning}<div class='row'><div class='col-lg-6'><h5>Zo ziet de klant het</h5>"
            f"<table class='table table-sm o_mc_table'><tbody>{rows}</tbody><tfoot>"
            f"<tr><td>Subtotaal excl. btw</td><td class='text-end'>{fmt(calc['subtotal'])}</td></tr>"
            + (f"<tr><td>Korting {self.quote_discount:g} %</td><td class='text-end'>- {fmt(calc['discount'])}</td></tr>"
               if calc['discount'] else '')
            + f"<tr><td>Btw {self.quote_vat} %</td><td class='text-end'>{fmt(calc['vat'])}</td></tr>"
            f"<tr><td><b>Totaal incl. btw</b></td><td class='text-end'><b>{fmt(calc['total'])}</b></td></tr>"
            f"<tr><td class='text-muted'>Voorschot {self.quote_deposit:g} %</td>"
            f"<td class='text-end text-muted'>{fmt(calc['total'] * self.quote_deposit / 100)}</td></tr>"
            f"</tfoot></table></div><div class='col-lg-6'><h5>Calculatie (intern)</h5>"
            f"<table class='table table-sm o_mc_table'><tbody>{cost_rows}</tbody><tfoot>"
            f"<tr><td>Totale kost</td><td class='text-end'>{fmt(calc['total_cost'])}</td></tr>"
            f"<tr><td><b>Brutomarge</b></td><td class='text-end'><b>{fmt(margin)} ({margin_pct} %)</b></td></tr>"
            f"</tfoot></table></div></div>")

    def _mc_find_tax(self):
        Tax = self.env['account.tax']
        return Tax.search([
            *Tax._check_company_domain(self.company_id),
            ('type_tax_use', '=', 'sale'), ('amount_type', '=', 'percent'),
            ('amount', '=', float(self.quote_vat or 21)),
        ], limit=1)

    def action_generate_quote(self):
        """Create (or refresh) the draft quotation from the TopSolid material list."""
        for project in self:
            if not project.part_ids:
                raise UserError(self.env._("Er is nog geen TopSolid-materiaallijst ingelezen voor %s.", project.display_name))
            calc = project._mc_quote_calc()
            if calc['missing']:
                raise UserError(self.env._(
                    "Geen prijs voor: %s. Koppel het materiaal aan een voorraadartikel met kostprijs.", calc['missing']))
            tax = project._mc_find_tax()
            order_lines = []
            for line in calc['lines']:
                values = {
                    'product_id': self.env.ref(line['product']).id,
                    'name': f"{line['label']}\n{line['description']}",
                    'product_uom_qty': 1,
                    'price_unit': round(line['amount'], 2),
                }
                if tax:
                    values['tax_ids'] = [Command.set(tax.ids)]
                order_lines.append(Command.create(values))
            if project.quote_discount:
                for command in order_lines:
                    command[2]['discount'] = project.quote_discount
            note = self.env._(
                "Voorschot %(pct)s %% bij goedkeuring van tekening en offerte. Offerte opgemaakt op basis van "
                "de TopSolid-materiaallijst van project %(ref)s.", pct=f"{project.quote_deposit:g}", ref=project.ref)
            draft = project.sale_order_ids.filtered(lambda o: o.state == 'draft' and not o.mc_version_id)[-1:]
            if draft:
                draft.order_line.unlink()
                draft.write({'order_line': order_lines, 'note': note})
                order = draft
            else:
                order = self.env['sale.order'].create({
                    'partner_id': project.partner_id.id,
                    'mc_project_id': project.id,
                    'origin': project.ref,
                    'user_id': project.user_id.id,
                    'note': note,
                    'order_line': order_lines,
                })
            message = self.env._(
                "Offerte %(quote)s gegenereerd uit de TopSolid-materiaallijst: %(amount)s incl. btw.",
                quote=order.name, amount=order.currency_id.format(order.amount_total))
            if not tax:
                message += " " + self.env._(
                    "Geen verkoopbtw van %s %% gevonden: de standaardbtw van het artikel is gebruikt. "
                    "Installeer de Belgische boekhouding (l10n_be) voor 6 en 21 %%.", project.quote_vat)
            project.message_post(body=message)
        return True

    # ------------------------------------------------------------------
    # Production
    # ------------------------------------------------------------------
    def action_open_topsolid_import(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('mc_interieur.mc_topsolid_import_action')
        action['context'] = {'default_project_id': self.id}
        return action

    def action_print_labels(self):
        """Fallback label printing from Odoo (label printer, 100 x 50 mm)."""
        self.ensure_one()
        if not self.piece_ids:
            raise UserError(self.env._("Er zijn nog geen etiketten: die worden aangemaakt bij de goedkeuring door de klant."))
        return self.env.ref('mc_interieur.action_report_mc_piece_label').report_action(self.piece_ids, config=False)

    def action_relink_materials(self):
        """Apply the TopSolid to Ardis material links again, after a link was added or changed."""
        self.part_ids._mc_apply_mapping()
        return True

    def _mc_generate_pieces(self):
        """One labelled piece per unit of each part. Barcode = project reference, part number, piece number."""
        Piece = self.env['mc.piece']
        vals_list = []
        for project in self:
            if project.piece_ids:
                continue
            for index, part in enumerate(project.part_ids.sorted(lambda p: (p.sequence, p.id)), start=1):
                for piece_number in range(1, part.quantity + 1):
                    vals_list.append({
                        'part_id': part.id,
                        'barcode': f"{project.ref}-{index:03d}.{piece_number}",
                    })
        return Piece.create(vals_list)

    def _mc_check_progress(self):
        """Move projects forward when every piece passed the saw, the CNC and the assembly bench."""
        for project in self:
            pieces = project.piece_ids
            if not pieces:
                continue
            if project.stage == 'sawing' and all(pieces.mapped('sawn')):
                project.stage = 'cnc'
                project.message_post(body=self.env._("Alle onderdelen gezaagd. Project staat nu in CNC."))
            if project.stage == 'cnc' and all(pieces.filtered('needs_cnc').mapped('cnc_done')):
                project.stage = 'assembly'
                project.message_post(body=self.env._("Alle CNC-bewerkingen klaar. Project staat nu in Montage & plaatsing."))

    def action_plan_installation(self):
        self.ensure_one()
        installation = self.installation_ids.filtered(lambda i: i.state != 'done')[:1]
        if not installation:
            installation = self.env['mc.installation'].create({'project_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mc.installation',
            'res_id': installation.id,
            'view_mode': 'form',
            'target': 'current',
        }
