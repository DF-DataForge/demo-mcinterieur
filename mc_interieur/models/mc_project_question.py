from odoo import api, fields, models


class McProjectQuestion(models.Model):
    _name = 'mc.project.question'
    _description = "Open vraag bij een interieurproject"
    _order = 'done, sequence, id'

    project_id = fields.Many2one('mc.project', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Vraag", required=True)
    field_name = fields.Char(
        string="Gekoppelde intakevraag",
        help="Technische naam van het intakeveld. Wordt automatisch afgesloten zodra het veld ingevuld is.")
    to_customer = fields.Boolean(
        string="In klantportaal",
        help="Zichtbaar voor de klant in het portaal. Zolang zo'n vraag open staat, kan de klant niet goedkeuren.")
    answer = fields.Text(string="Antwoord")
    answered_by_customer = fields.Boolean(string="Beantwoord door klant", readonly=True)
    done = fields.Boolean(string="Afgehandeld")

    @api.model_create_multi
    def create(self, vals_list):
        questions = super().create(vals_list)
        questions.filtered('to_customer').project_id._mc_notify_customer_questions()
        return questions

    def action_mark_done(self):
        self.write({'done': True})

    def action_reopen(self):
        self.write({'done': False})

    def action_show_to_customer(self):
        self.write({'to_customer': True})

    def action_hide_from_customer(self):
        self.write({'to_customer': False})

    def _mc_customer_answer(self, answer):
        """Store the customer's answer and copy it to the linked intake field when it is free text."""
        self.ensure_one()
        self.write({'answer': answer, 'done': True, 'answered_by_customer': True})
        project = self.project_id
        field = project._fields.get(self.field_name) if self.field_name else None
        if field and field.type == 'char':
            project[self.field_name] = answer
        project.message_post(body=self.env._(
            "Klant beantwoordde \"%(question)s\": %(answer)s", question=self.name, answer=answer))
