{
    'name': 'MC Interieur website',
    'version': '20.0.1.0.0',
    'summary': "Website for MC Interieur: custom kitchens, bathrooms, dressings and interiors",
    'description': """
Website for MC Interieur, built with the standard Odoo Website app:

* house colours (walnut brown, leaf green) and Open Sans as the website palette and font
* homepage, a page per service, about us with the workshop, and a contact form
* menu, header button and footer in Dutch, MC Interieur logo

Everything stays editable in the website editor.
""",
    'category': 'Website',
    'author': 'BP IT Consulting',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'views/website_layout.xml',
        'views/website_pages.xml',
        'data/website_setup_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_mc_interieur/static/src/scss/website_mc.scss',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
}
