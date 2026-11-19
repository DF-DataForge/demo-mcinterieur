from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class McDrawingVersion(models.Model):
    _name = 'mc.drawing.version'
    _description = "Tekeningversie"
    _order = 'project_id, number desc, id desc'

    project_id = fields.Many2one('mc.project', required=True, ondelete='cascade', index=True)
    number = fields.Integer(string="Versie", required=True, default=1)
    state = fields.Selection([
        ('draft', "In voorbereiding"),
        ('pending', "Wacht op klant"),
        ('approved', "Goedgekeurd"),
        ('changes', "Wijzigingen gevraagd"),
        ('superseded', "Vervangen"),
    ], string="Status", default='draft', required=True)
    drawing_image = fields.Image(string="Tekening (afbeelding)", max_width=2400, max_height=2400)
    drawing_pdf = fields.Binary(string="Tekening (PDF uit TopSolid)", attachment=True)
    drawing_pdf_name = fields.Char()
    note = fields.Text(string="Wat is er gewijzigd")
    shared_on = fields.Datetime(string="Gedeeld op", readonly=True)
    approved_by = fields.Char(string="Goedgekeurd door", readonly=True)
    approved_on = fields.Datetime(string="Goedgekeurd op", readonly=True)
    customer_remarks = fields.Text(string="Opmerkingen klant", readonly=True)
    sale_order_id = fields.Many2one('sale.order', compute='_compute_sale_order_id', string="Offerte")

    _project_number_uniq = models.Constraint(
        'UNIQUE(project_id, number)', "Elk versienummer bestaat maar een keer per project.")

    @api.depends('number')
    def _compute_display_name(self):
        for version in self:
            version.display_name = self.env._("Versie %s", version.number)

    def _compute_sale_order_id(self):
        orders = self.env['sale.order'].search([('mc_version_id', 'in', self.ids)])
        for version in self:
            version.sale_order_id = orders.filtered(lambda o: o.mc_version_id == version)[:1]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'number' not in vals and vals.get('project_id'):
                project = self.env['mc.project'].browse(vals['project_id'])
                vals['number'] = max(project.version_ids.mapped('number') or [0]) + 1
        return super().create(vals_list)

    def _mc_customer_approve(self, signer_name):
        """Approval from the portal: drawing and quote together. Blocked while customer questions are open."""
        self.ensure_one()
        project = self.project_id
        if self.state != 'pending':
            raise UserError(self.env._("Deze tekeningversie wacht niet (meer) op goedkeuring."))
        if project.customer_question_count:
            raise UserError(self.env._("Beantwoord eerst alle open vragen."))
        if not (signer_name or '').strip():
            raise UserError(self.env._("Vul uw naam in om te ondertekenen."))
        now = fields.Datetime.now()
        self.write({'state': 'approved', 'approved_by': signer_name.strip(), 'approved_on': now})
        order = self.sale_order_id
        if order and order.state in ('draft', 'sent'):
            order.write({'signed_by': signer_name.strip(), 'signed_on': now})
            order.action_confirm()
        project.stage = 'prep'
        project._mc_generate_pieces()
        project.message_post(body=self.env._(
            "%(name)s keurde tekening versie %(version)s%(quote)s goed via het klantportaal.",
            name=signer_name.strip(), version=self.number,
            quote=self.env._(" en offerte %s", order.name) if order else ""))

    def _mc_customer_request_changes(self, remarks):
        """Change request from the portal: remarks become open questions for the drawer."""
        self.ensure_one()
        remarks = (remarks or '').strip()
        if self.state != 'pending':
            raise UserError(self.env._("Deze tekeningversie wacht niet (meer) op goedkeuring."))
        if not remarks:
            raise UserError(self.env._("Beschrijf wat u wilt laten aanpassen."))
        project = self.project_id
        self.write({'state': 'changes', 'customer_remarks': remarks})
        lines = [line.strip('-* ').strip() for line in remarks.splitlines() if line.strip()]
        project.write({
            'stage': 'drawing',
            'question_ids': [Command.create({
                'name': self.env._("Klant V%(version)s: %(remark)s", version=self.number, remark=line),
            }) for line in lines],
        })
        if self.sale_order_id and self.sale_order_id.state in ('draft', 'sent'):
            self.sale_order_id._action_cancel()
        if project.drawer_id:
            project.activity_schedule(
                'mail.mail_activity_data_todo', user_id=project.drawer_id.id,
                summary=self.env._("Opmerkingen klant verwerken (versie %s)", self.number))
        project.message_post(body=self.env._(
            "Klant vroeg wijzigingen op versie %(version)s: %(remarks)s", version=self.number, remarks=remarks))
