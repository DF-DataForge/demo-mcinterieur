from datetime import timedelta

from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class McInstallation(models.Model):
    _name = 'mc.installation'
    _description = "Plaatsing"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(compute='_compute_name', store=True, string="Plaatsing")
    project_id = fields.Many2one('mc.project', required=True, ondelete='cascade', index=True, tracking=True)
    partner_id = fields.Many2one(related='project_id.partner_id', store=True, string="Klant")
    team_id = fields.Many2one('mc.team', string="Ploeg", tracking=True)
    user_ids = fields.Many2many(related='team_id.user_ids', string="Plaatsers")
    date_start = fields.Datetime(string="Start", tracking=True)
    date_stop = fields.Datetime(string="Einde")
    state = fields.Selection([
        ('draft', "In te plannen"),
        ('planned', "Ingepland"),
        ('done', "Opgeleverd"),
    ], default='draft', required=True, tracking=True, string="Status")
    color = fields.Integer(related='team_id.color')

    # Site information from the intake
    site_city = fields.Char(related='project_id.city', string="Gemeente")
    site_street = fields.Char(related='project_id.street', string="Adres")
    access_info = fields.Char(related='project_id.access_info')
    parking = fields.Char(related='project_id.parking')
    dismantle = fields.Selection(related='project_id.dismantle')
    disposal = fields.Selection(related='project_id.disposal')
    utilities = fields.Char(related='project_id.utilities')

    check_ids = fields.One2many('mc.installation.check', 'installation_id', string="Controlelijst")
    open_check_count = fields.Integer(compute='_compute_open_check_count')
    punch_ids = fields.One2many('mc.installation.punch', 'installation_id', string="Nazorgpunten")
    photo_ids = fields.Many2many('ir.attachment', string="Foto's van het resultaat")
    signed_by = fields.Char(string="Ondertekend door", tracking=True)
    signed_on = fields.Datetime(string="Ondertekend op", readonly=True)
    signature = fields.Image(string="Handtekening klant", max_width=1024, max_height=1024)

    @api.depends('project_id.name', 'project_id.ref')
    def _compute_name(self):
        for installation in self:
            installation.name = installation.project_id.display_name or self.env._("Plaatsing")

    @api.depends('check_ids.done')
    def _compute_open_check_count(self):
        for installation in self:
            installation.open_check_count = len(installation.check_ids.filtered(lambda c: not c.done))

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.date_start and not self.date_stop:
            days = self.project_id.quote_install_days or 1
            self.date_stop = self.date_start + timedelta(days=days - 1, hours=8)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('date_start') and not vals.get('state'):
                vals['state'] = 'planned'
        installations = super().create(vals_list)
        for installation in installations.filtered(lambda i: not i.check_ids):
            installation.check_ids = [Command.create({'name': label}) for label in installation._mc_default_checks()]
        return installations

    def write(self, vals):
        result = super().write(vals)
        if vals.get('date_start'):
            self.filtered(lambda i: i.state == 'draft').write({'state': 'planned'})
        return result

    def _mc_default_checks(self):
        project = self.project_id
        checks = [self.env._("Alle kasten geleverd en gecontroleerd")]
        if project.dismantle == 'yes':
            checks.append(self.env._("Oude meubels gedemonteerd"))
        checks += [self.env._("Kasten geplaatst, waterpas en verankerd"), self.env._("Deuren en lades afgesteld")]
        if project.project_type == 'kitchen':
            checks.append(self.env._("Toestellen ingebouwd en getest"))
        if project.worktop in ('stone', 'ceramic'):
            checks.append(self.env._("Werkblad opgemeten voor de steenhouwer"))
        if project.lighting and project.lighting != 'none':
            checks.append(self.env._("Verlichting aangesloten en getest"))
        checks.append(self.env._("Werf proper achtergelaten"))
        if project.disposal == 'yes':
            checks.append(self.env._("Oud meubilair afgevoerd"))
        return checks

    def action_sign_off(self):
        """Customer signs the handover on the tablet. All checks must be done; open snags stay open."""
        for installation in self:
            if installation.open_check_count:
                raise UserError(self.env._("Nog %s controlepunten open. Vink alles af voordat de klant tekent.",
                                           installation.open_check_count))
            if not installation.signed_by or not installation.signature:
                raise UserError(self.env._("Laat de klant zijn naam invullen en tekenen."))
            open_punches = installation.punch_ids.filtered(lambda p: not p.done)
            installation.write({'state': 'done', 'signed_on': fields.Datetime.now()})
            installation.project_id.stage = 'delivered'
            installation.project_id.message_post(body=self.env._(
                "Oplevering ondertekend door %(name)s. %(count)s nazorgpunt(en) open.",
                name=installation.signed_by, count=len(open_punches)))
            for punch in open_punches:
                installation.project_id.activity_schedule(
                    'mail.mail_activity_data_todo', user_id=installation.project_id.user_id.id,
                    summary=self.env._("Nazorg: %s", punch.name))
        return True
