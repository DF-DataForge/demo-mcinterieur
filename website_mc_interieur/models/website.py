import logging

from odoo import api, models
from odoo.tools import file_open
from odoo.tools.binary import BinaryBytes

_logger = logging.getLogger(__name__)

# Website palette: o-color-1 buttons and accents, o-color-2 secondary, o-color-3 light sections,
# o-color-4 page background, o-color-5 dark sections and text.
MC_PALETTE = {
    'o-color-1': '#5F7D1C',   # leaf green (dark, readable on white)
    'o-color-2': '#574A36',   # walnut brown
    'o-color-3': '#F3EFE7',   # warm sand
    'o-color-4': '#FFFFFF',
    'o-color-5': '#2E271D',   # deep brown
    'menu': '1',
    'footer': '5',
    'copyright': '5',
}
MC_VALUES = {
    'color-palettes-name': "'base-1'",
    'font': "'Open Sans'",
    'headings-font': "'Open Sans'",
    'navbar-font': "'Open Sans'",
    'buttons-font': "'Open Sans'",
}

# (name, url, sequence, children)
MC_MENU = [
    ("Home", '/', 10, []),
    ("Wat we maken", '', 20, [
        ("Keukens", '/keukens', 1),
        ("Badkamers", '/badkamers', 2),
        ("Slaapkamers & dressings", '/slaapkamers', 3),
        ("Interieur & bureaus", '/interieur', 4),
        ("Buitenschrijnwerk", '/buitenschrijnwerk', 5),
        ("Winkelinrichting", '/winkelinrichting', 6),
        ("Isoleren", '/isoleren', 7),
    ]),
    ("Over ons & atelier", '/over-ons', 30, []),
    ("Contact", '/contactus', 40, []),
]


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def _mcw_setup_websites(self):
        params = self.env['ir.config_parameter'].sudo()
        for website in self.sudo().search([]):
            key = f'website_mc_interieur.setup_done.{website.id}'
            if params.get_bool(key):
                continue
            website._mcw_setup()
            params.set_bool(key, True)
        return True

    def _mcw_setup(self):
        self.ensure_one()
        Assets = self.env['website.assets'].with_context(website_id=self.id)
        Assets.make_scss_customization('/website/static/src/scss/options/user_values.scss', dict(MC_VALUES))
        Assets.make_scss_customization(
            '/website/static/src/scss/options/colors/user_color_palette.scss', dict(MC_PALETTE))
        with file_open('website_mc_interieur/static/img/logo.png', 'rb') as logo:
            self.logo = BinaryBytes(logo.read(), filename='mc_logo.png')
        if self.name in (False, '', 'My Website'):
            self.name = "MC Interieur"
        self._mcw_setup_menu()
        self._mcw_setup_language()

    def _mcw_setup_menu(self):
        Menu = self.env['website.menu']
        root = self.menu_id
        if not root:
            return
        existing = {menu.url: menu for menu in Menu.search([('website_id', '=', self.id), ('id', 'child_of', root.id)])}
        for name, url, sequence, children in MC_MENU:
            menu = existing.get(url) if url else Menu.search(
                [('website_id', '=', self.id), ('parent_id', '=', root.id), ('name', '=', name)], limit=1)
            vals = {'name': name, 'sequence': sequence, 'parent_id': root.id, 'website_id': self.id}
            if url:
                vals['url'] = url
            if menu:
                menu.write(vals)
            else:
                menu = Menu.create(dict(vals, url=url or '#'))
            for child_name, child_url, child_sequence in children:
                child_vals = {'name': child_name, 'url': child_url, 'sequence': child_sequence,
                              'parent_id': menu.id, 'website_id': self.id}
                if child_url in existing:
                    existing[child_url].write(child_vals)
                else:
                    Menu.create(child_vals)
        # Odoo's default "Contact us" entry is replaced by "Contact"
        for menu in Menu.search([('website_id', '=', self.id), ('parent_id', '=', root.id)]):
            if menu.url == '/contactus' and menu.name != "Contact":
                menu.unlink()

    def _mcw_setup_language(self):
        """Dutch (Belgium) as website language when it is installed."""
        lang = self.env['res.lang'].search([('code', 'in', ('nl_BE', 'nl_NL')), ('active', '=', True)], limit=1)
        if lang:
            self.write({'language_ids': [(4, lang.id)], 'default_lang_id': lang.id})
