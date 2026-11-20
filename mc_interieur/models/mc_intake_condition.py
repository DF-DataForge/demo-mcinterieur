from odoo import api, fields, models

from .mc_intake_template import INTAKE_SECTIONS


class McIntakeCondition(models.Model):
    """Show an intake question only when another question has a given answer.

    Several lines for the same question are OR-ed: the question shows as soon as one of them matches.
    """
    _name = 'mc.intake.condition'
    _description = "Voorwaarde intakevraag"
    _order = 'template_id, question_key, id'

    template_id = fields.Many2one('mc.intake.template', required=True, ondelete='cascade', index=True)
    question_key = fields.Selection(
        selection='_selection_question_key', string="Toon vraag", required=True,
        help="Deze vraag verschijnt enkel als de voorwaarde klopt.")
    when_option = fields.Selection(
        selection='_selection_when_option', string="Als", required=True,
        help="Vraag en keuze die de vraag zichtbaar maakt.")

    @api.model_create_multi
    def create(self, vals_list):
        conditions = super().create(vals_list)
        self.env['mc.project']._mc_sync_all_hidden_questions()
        return conditions

    def write(self, vals):
        result = super().write(vals)
        self.env['mc.project']._mc_sync_all_hidden_questions()
        return result

    def unlink(self):
        result = super().unlink()
        self.env['mc.project']._mc_sync_all_hidden_questions()
        return result

    @api.model
    def _mc_all_definitions(self):
        """(field, label, definition) for every question of every intake template."""
        result = []
        for template in self.env['mc.intake.template'].sudo().search([]):
            for field_name, definition_field, label in INTAKE_SECTIONS:
                for definition in template[definition_field] or []:
                    if definition.get('type') != 'separator':
                        result.append((field_name, label, definition))
        return result

    @api.model
    def _selection_question_key(self):
        seen = {}
        for field_name, label, definition in self._mc_all_definitions():
            key = f"{field_name}.{definition['name']}"
            seen.setdefault(key, f"{label}: {definition.get('string') or definition['name']}")
        return list(seen.items())

    @api.model
    def _selection_when_option(self):
        seen = {}
        for field_name, _label, definition in self._mc_all_definitions():
            if definition.get('type') != 'selection':
                continue
            question = definition.get('string') or definition['name']
            for value, value_label in definition.get('selection') or []:
                seen.setdefault(f"{field_name}.{definition['name']}|{value}", f"{question} = {value_label}")
        return list(seen.items())
