from odoo import fields, models

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
