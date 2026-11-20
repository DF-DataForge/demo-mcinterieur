from odoo import api, models

# Odoo colours the customer portal (links, buttons) with the company's e-mail button colours,
# set in Settings > General Settings > Document layout. These are MC Interieur's house colours.
MC_BUTTON_COLOR = '#574A36'
MC_BUTTON_TEXT = '#FFFFFF'
ODOO_DEFAULT_BUTTON_COLOR = '#875A7B'


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _mc_house_colours(self):
        """Give companies still on Odoo's purple the house colours; a colour chosen by hand is kept."""
        companies = self.sudo().search([])
        for company in companies:
            if (company.email_secondary_color or ODOO_DEFAULT_BUTTON_COLOR).upper() == ODOO_DEFAULT_BUTTON_COLOR:
                company.write({'email_secondary_color': MC_BUTTON_COLOR, 'email_primary_color': MC_BUTTON_TEXT})
        return True
