from odoo import api, fields, models

# Intake tabs: (properties field on mc.project, definition field on this template, tab label)
INTAKE_SECTIONS = [
    ('intake_general', 'general_definition', "Algemeen"),
    ('intake_space', 'space_definition', "Ruimte & opmeting"),
    ('intake_materials', 'materials_definition', "Materialen & afwerking"),
    ('intake_hardware', 'hardware_definition', "Beslag & indeling"),
    ('intake_appliances', 'appliances_definition', "Werkblad & toestellen"),
    ('intake_installation', 'installation_definition', "Plaatsing"),
]


class McIntakeTemplate(models.Model):
    _name = 'mc.intake.template'
    _description = "Intakesjabloon"
    _order = 'id'

    name = fields.Char(required=True)
    general_definition = fields.PropertiesDefinition(string="Algemeen")
    space_definition = fields.PropertiesDefinition(string="Ruimte & opmeting")
    materials_definition = fields.PropertiesDefinition(string="Materialen & afwerking")
    hardware_definition = fields.PropertiesDefinition(string="Beslag & indeling")
    appliances_definition = fields.PropertiesDefinition(string="Werkblad & toestellen")
    installation_definition = fields.PropertiesDefinition(string="Plaatsing")

    # Preview of the intake on the configuration screen. Odoo edits question definitions from a form that shows
    # the questions themselves (menu "Edit Properties"), so the template shows its own questions as a preview.
    preview_template_id = fields.Many2one(
        'mc.intake.template', compute='_compute_preview_template_id', store=True)
    preview_general = fields.Properties("Algemeen", definition='preview_template_id.general_definition')
    preview_space = fields.Properties("Ruimte & opmeting", definition='preview_template_id.space_definition')
    preview_materials = fields.Properties(
        "Materialen & afwerking", definition='preview_template_id.materials_definition')
    preview_hardware = fields.Properties("Beslag & indeling", definition='preview_template_id.hardware_definition')
    preview_appliances = fields.Properties(
        "Werkblad & toestellen", definition='preview_template_id.appliances_definition')
    preview_installation = fields.Properties("Plaatsing", definition='preview_template_id.installation_definition')

    @api.depends('name')
    def _compute_preview_template_id(self):
        for template in self:
            template.preview_template_id = template._origin or template
