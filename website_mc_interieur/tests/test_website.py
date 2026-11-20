from odoo.tests import HttpCase, tagged

PAGES = {
    '/': "Interieur op maat, van eerste schets tot plaatsing",
    '/keukens': "Uw keuken is de plek waar alles samenkomt",
    '/badkamers': "een badkamer waar u echt tot uzelf komt",
    '/slaapkamers': "Uw slaapkamer is uw cocon",
    '/interieur': "gezellige thuiswerkplek",
    '/buitenschrijnwerk': "Uw tuin als verlengstuk van uw woonkamer",
    '/winkelinrichting': "Een winkelinrichting die uw producten laat schitteren",
    '/isoleren': "Een goed geïsoleerd dak",
    '/over-ons': "De machines achter ons maatwerk",
    '/contactus': "Neem contact op",
}


@tagged('post_install', '-at_install')
class TestMcWebsite(HttpCase):

    def test_pages(self):
        for url, text in PAGES.items():
            response = self.url_open(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertIn(text, response.text, url)
            self.assertIn('Afspraak maken', response.text, f"{url}: header button")
            self.assertIn('o_mcw_footer', response.text, f"{url}: footer")

    def test_setup(self):
        website = self.env['website'].get_current_website()
        self.assertTrue(website.logo)
        urls = set(self.env['website.menu'].search([('website_id', '=', website.id)]).mapped('url'))
        self.assertTrue({'/keukens', '/over-ons', '/contactus'} <= urls, urls)
        custom = self.env['ir.attachment'].search([('url', 'like', '/_custom/%user_color_palette.scss')])
        self.assertTrue(custom, "House colours stored as website palette")
        self.assertIn('#574A36', custom[0].raw.decode() if custom[0].raw else '')

    def test_homepage_in_browser(self):
        # compiles the frontend assets with the palette and the module's styles
        self.browser_js('/', "setTimeout(() => console.log('test successful'), 1500)")
