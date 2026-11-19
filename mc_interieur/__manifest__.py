{
    'name': 'MC Interieur - Maatwerkflow',
    'version': '20.0.1.0.0',
    'summary': 'Intake, TopSolid-offertes, klantportaal, Ardis-export, werkvloer, montage en plaatsing voor interieurbouw',
    'description': """
Maatwerkflow voor een interieurbouwer / schrijnwerker
=====================================================

* Intake door de verkoper (niet-verplichte vragen, foto's en schetsen)
* Overdracht naar de tekenaar (TopSolid) met open vragen
* Offerte genereren uit de TopSolid-materiaallijst (verkoopofferte)
* Klantportaal: tekening + offerte samen goedkeuren, vragen beantwoorden
* Werkvoorbereiding: zaagbatches, Ardis-export (CSV), materiaal en tekorten bestellen
* Werkvloer: scannen aan zaag, CNC en montage
* Planning en oplevering van de plaatsing
""",
    'author': 'BP IT Consulting',
    'category': 'Manufacturing',
    'license': 'LGPL-3',
    'depends': [
        'contacts',
        'portal',
        'sale_management',
        'stock',
        'purchase',
    ],
    'data': [
        'security/mc_interieur_security.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/product_data.xml',
        'data/portal_entry_data.xml',
        'views/mc_project_views.xml',
        'views/mc_part_views.xml',
        'views/mc_cutting_batch_views.xml',
        'views/mc_installation_views.xml',
        'views/mc_team_views.xml',
        'views/mc_material_mapping_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/mc_scan_station_views.xml',
        'wizard/mc_ardis_result_views.xml',
        'views/mc_interieur_menus.xml',
        'views/mc_portal_templates.xml',
    ],
    'demo': [
        'demo/res_users_demo.xml',
        'demo/product_demo.xml',
        'demo/mc_project_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mc_interieur/static/src/scan_station/**/*',
        ],
        'web.assets_frontend': [
            'mc_interieur/static/src/portal/**/*',
        ],
    },
    'application': True,
}
