"""Generates website_mc_interieur/views/website_pages.xml from the content below.

Run from the repository root:  python scripts/gen_website_pages.py
After installation the pages can also be edited in the Odoo website editor; edits made there are stored per
website and are not overwritten by a module upgrade.
"""
from pathlib import Path
from xml.sax.saxutils import escape as e

IMG = '/website_mc_interieur/static/img/'
OUT = Path(__file__).resolve().parent.parent / 'website_mc_interieur' / 'views' / 'website_pages.xml'

# key, url, title, card text, lead, paragraphs, bullets, images (first = header), meta description
SERVICES = [
    ('keukens', '/keukens', "Keukens",
     "Een keuken die past bij hoe u kookt, leeft en ontvangt.",
     "Uw keuken is de plek waar alles samenkomt: koken, praten, werken en genieten.",
     ["Daarom laten we een mooi ontwerp en een slimme indeling hand in hand gaan. Modern, landelijk of klassiek: "
      "we tekenen, maken en plaatsen de keuken die bij u en uw woning past.",
      "Geen standaardmodules, maar kasten die tot op de millimeter in uw ruimte passen. Werkblad, toestellen en "
      "verlichting nemen we mee in het ontwerp, zodat alles klopt op de dag van de plaatsing."],
     ["Ontwerp en technische tekening op maat", "Werkblad, toestellen en verlichting geïntegreerd",
      "Gemaakt in ons eigen atelier", "Plaatsing en aansluiting door ons team"],
     ['keuken_2.jpg', 'keuken_1.jpg', 'keuken_3.jpg', 'keuken_4.jpg'],
     "Keukens op maat: ontworpen, gemaakt en geplaatst door MC Interieur."),
    ('badkamers', '/badkamers', "Badkamers",
     "Rust, comfort en slimme bergruimte, in vochtbestendig maatwerk.",
     "Rust, comfort en harmonie: een badkamer waar u echt tot uzelf komt.",
     ["Van een snelle douche tot een eigen wellness: in de badkamer staat uw comfort centraal. Een goede badkamer "
      "is makkelijk te onderhouden, heeft voldoende bergruimte en een warme sfeer.",
      "We tekenen badkamermeubels en lavabokasten op maat, werken verlichting mee in en nemen de totaalaanpak "
      "op ons, met één aanspreekpunt van ontwerp tot plaatsing."],
     ["Badkamermeubels en lavabokasten op maat", "Geïntegreerde ledverlichting",
      "Vochtbestendige materialen", "Eén aanspreekpunt voor het hele project"],
     ['badkamer_3.jpg', 'badkamer_1.jpg', 'badkamer_2.jpg'],
     "Badkamermeubels op maat met verlichting en slimme bergruimte."),
    ('slaapkamers', '/slaapkamers', "Slaapkamers & dressings",
     "Dressings, wandkasten en kasten onder het dak, tot op de millimeter benut.",
     "Uw slaapkamer is uw cocon. Wij zorgen dat alles er zijn plaats krijgt.",
     ["Een wandkast met schuifdeuren, een inloopdressing of kasten onder de dakhelling: u kiest de indeling, "
      "wij benutten elke millimeter, zodat u maximale bergruimte krijgt.",
      "Laat u inspireren door de vele kleuren en afwerkingen en creëer de sfeer die bij u past."],
     ["Dressings en inloopkasten", "Kasten onder schuine daken", "Schuifdeuren en handige lades",
      "Ruime keuze in kleur en afwerking"],
     ['slaapkamer_1.jpg', 'slaapkamer_2.jpg', 'slaapkamer_3.jpg'],
     "Dressings, inbouwkasten en slaapkamers op maat."),
    ('interieur', '/interieur', "Interieur & bureaus",
     "Een thuiswerkplek of kantoor, tv-meubels en kasten voor uw hele woning.",
     "Een professionele kantoorinrichting of een gezellige thuiswerkplek, op maat van uw werk.",
     ["In een bureau draait alles om ergonomie en overzicht. We richten uw werkplek volledig in, met bergruimte "
      "die alles netjes wegwerkt en een kast die de ruimte meteen karakter geeft.",
      "Ook in de rest van uw woning maken we het verschil: tv-meubels, boekenkasten, binnendeuren of de "
      "volledige inrichting van een renovatie."],
     ["Kantoor- en thuiswerkplekken", "Schuifdeuren die uw klassement verbergen", "Tv-meubels en boekenkasten",
      "Volledige inrichting bij renovatie"],
     ['interieur_1.jpg', 'interieur_2.jpg', 'about_kitchen.jpg'],
     "Bureaus, thuiswerkplekken en interieur op maat."),
    ('buitenschrijnwerk', '/buitenschrijnwerk', "Buitenschrijnwerk",
     "Tuinhuizen, terrasoverkappingen en poolhouses in duurzaam hout.",
     "Uw tuin als verlengstuk van uw woonkamer.",
     ["Gebruik uw tuin als extra kamer. Een tuinhuis voor extra bergruimte, een terrasoverkapping om gasten te "
      "ontvangen, een poolhouse met buitenkeuken of een stevige afsluiting voor privacy en veiligheid.",
      "We werken in duurzame houtsoorten zoals padoek en voorzien verlichting waar u dat wilt."],
     ["Tuinhuizen en terrasoverkappingen", "Poolhouses en buitenkeukens", "Poorten, afsluitingen en gevelbekleding",
      "Geïntegreerde ledverlichting"],
     ['buiten_1.jpg', 'buiten_2.jpg', 'buiten_3.jpg'],
     "Tuinhuizen, terrasoverkappingen en buitenschrijnwerk op maat."),
    ('winkelinrichting', '/winkelinrichting', "Winkelinrichting",
     "Een winkel die uw merk uitstraalt, van A tot Z ingericht.",
     "Een winkelinrichting die uw producten laat schitteren.",
     ["Toonbanken, wandsystemen, rekken en presentatiemeubels: we ontwerpen en plaatsen een inrichting die past "
      "bij uw merk en die vlot werkt voor uw team.",
      "We plannen de plaatsing zo dat uw winkel zo kort mogelijk dicht moet."],
     ["Ontwerp op maat van uw merk", "Toonbanken, wandsystemen en rekken", "Eigen productie en plaatsing",
      "Planning rond uw openingsuren"],
     ['winkel_1.jpg', 'winkel_2.jpg'],
     "Winkelinrichting op maat, van ontwerp tot plaatsing."),
    ('isoleren', '/isoleren', "Isoleren",
     "Meer comfort en een lagere energiefactuur met een goed geïsoleerd dak.",
     "Een goed geïsoleerd dak verhoogt uw comfort en verlaagt uw energiefactuur.",
     ["Isoleren betaalt zich snel terug: minder energieverbruik, meer comfort, minder geluid van buiten en een "
      "hogere waarde voor uw woning. Vraag ons gerust naar de premies die van toepassing zijn.",
      "We plaatsen dakisolatie en superisolerende ramen en deuren, volgens de regels van de kunst."],
     ["Dakisolatie en afwerking van zolders", "Isolatie rond dakramen", "Superisolerende ramen en deuren",
      "Advies over premies"],
     ['isoleren_1.jpg'],
     "Dakisolatie en isolerende ramen en deuren door MC Interieur."),
]

STEPS = [
    ("Kennismaking", "We komen bij u langs, meten op en luisteren naar uw wensen. Niets hoeft al vast te liggen."),
    ("Ontwerp en offerte", "Onze tekenaar werkt alles uit tot op de millimeter. De prijs berekenen we uit het ontwerp zelf."),
    ("Uw beslissing", "Tekening en offerte staan samen in uw klantportaal. U keurt online goed, of vraagt een aanpassing."),
    ("Productie", "Uw meubels worden gemaakt in ons eigen atelier: zagen, CNC-bewerking en montage."),
    ("Plaatsing en nazorg", "Ons team plaatst alles, overloopt het resultaat samen met u en volgt de nazorg op."),
]

MACHINES = [
    ("CNC-bewerkingscentrum", "Morbidelli 4415TV, 4 assen met automatisch gereedschapsmagazijn, werkveld 4,20 x 1,53 m."),
    ("Paneelzaag", "Casadei AX0300, zaagt platen tot 4,10 m breed, tot vier platen tegelijk."),
    ("Kantenlijmmachine", "BI-Matic CH7.5RA57 voor kantenband in PVC en laminaat."),
    ("Vlaktepers", "ItalPRESSE, verwarmde pers voor eigen laminaten en fineer."),
]

BTN_APPOINTMENT = '<p class="mb-0"><a href="/contactus" class="btn btn-lg btn-primary">Afspraak maken</a></p>'


def card(url, title, text, image):
    return f'''
                            <div class="col-md-6 col-lg-4">
                                <a href="{url}" class="o_mcw_card">
                                    <img src="{IMG}{image}" class="img img-fluid o_mcw_card_img" alt="{e(title)}" loading="lazy"/>
                                    <span class="o_mcw_card_body">
                                        <span class="h4 d-block mb-1">{e(title)}</span>
                                        <span class="d-block">{e(text)}</span>
                                        <span class="o_mcw_more">Ontdek meer</span>
                                    </span>
                                </a>
                            </div>'''


def cta(title="Klaar om uw project te starten?",
        text="Vertel ons wat u voor ogen hebt. We maken graag een afspraak bij u thuis."):
    return f'''
                <section class="s_call_to_action o_cc o_cc4 pt56 pb56 o_mcw_cta" data-snippet="s_call_to_action" data-name="Call to Action">
                    <div class="container">
                        <div class="row align-items-center g-3">
                            <div class="col-lg-8">
                                <h2 class="mb-1">{e(title)}</h2>
                                <p class="lead mb-0">{e(text)}</p>
                            </div>
                            <div class="col-lg-4 text-lg-end">
                                <a href="/contactus" class="btn btn-lg btn-light">Neem contact op</a>
                            </div>
                        </div>
                    </div>
                </section>'''


def hero(image, eyebrow, title, lead, buttons, big=False):
    size = ' o_mcw_hero_big' if big else ''
    return f'''
                <section class="s_cover o_cc o_cc5 oe_img_bg o_bg_img_center o_mcw_hero{size}" data-snippet="s_cover" data-name="Cover"
                         style="background-image: url('{IMG}{image}');">
                    <div class="o_we_bg_filter o_mcw_hero_filter"/>
                    <div class="container">
                        <div class="o_mcw_hero_text">
                            <p class="o_mcw_eyebrow">{e(eyebrow)}</p>
                            <h1 class="display-4 fw-bold">{e(title)}</h1>
                            <p class="lead">{e(lead)}</p>
                            {buttons}
                        </div>
                    </div>
                </section>'''


def homepage():
    services = ''.join(card(s[1], s[2], s[3], s[7][0]) for s in SERVICES)
    steps = ''.join(f'''
                            <li class="col-md-6 col-lg">
                                <span class="o_mcw_step_nr">{i}</span>
                                <h3 class="h5">{e(t)}</h3>
                                <p>{e(d)}</p>
                            </li>''' for i, (t, d) in enumerate(STEPS, 1))
    machines = ''.join(f'<li><b>{e(n)}</b><br/>{e(d)}</li>' for n, d in MACHINES[:3])
    buttons = '''<p class="d-flex flex-wrap gap-2 mb-0">
                                <a href="/contactus" class="btn btn-lg btn-primary">Afspraak maken</a>
                                <a href="#realisaties" class="btn btn-lg btn-outline-light">Bekijk wat we maken</a>
                            </p>'''
    head = hero('badkamer_3.jpg', "Interieur & maatmeubelen", "Interieur op maat, van eerste schets tot plaatsing",
                "Keukens, badkamers, dressings, kasten en buitenschrijnwerk: ontworpen voor uw ruimte, gemaakt in ons "
                "eigen atelier en geplaatst door ons eigen team.", buttons, big=True)
    return f'''
    <template id="homepage" inherit_id="website.homepage" name="MC Interieur: homepage">
        <xpath expr="//div[@id='wrap']" position="replace">
            <div id="wrap" class="oe_structure o_mcw">{head}
                <section class="s_text_block pt80 pb64" data-snippet="s_text_block" data-name="Intro">
                    <div class="container">
                        <div class="row g-5 align-items-center">
                            <div class="col-lg-6">
                                <p class="o_mcw_eyebrow">Over MC Interieur</p>
                                <h2>Eén aanspreekpunt voor uw hele project</h2>
                                <p class="lead">MC Interieur ontwikkelt, maakt en plaatst interieur op maat. Of het nu gaat om een tv-meubel,
                                    een nieuwe keuken of de inrichting van uw hele woning: we begeleiden u van het eerste idee tot de oplevering
                                    en de service daarna.</p>
                                <p>Volledig op maat, binnen uw budget, en met de afwerking die u van vakmensen mag verwachten.</p>
                                <a href="/over-ons" class="btn btn-outline-primary">Meer over ons</a>
                            </div>
                            <div class="col-lg-6">
                                <div class="row g-3 o_mcw_facts">
                                    <div class="col-6"><div class="o_mcw_fact"><span class="o_mcw_fact_k">Eigen atelier</span><span>Zagen, CNC en montage onder één dak</span></div></div>
                                    <div class="col-6"><div class="o_mcw_fact"><span class="o_mcw_fact_k">Op de millimeter</span><span>Elk meubel ontworpen voor uw ruimte</span></div></div>
                                    <div class="col-6"><div class="o_mcw_fact"><span class="o_mcw_fact_k">Eigen plaatsers</span><span>Ons team plaatst en werkt af</span></div></div>
                                    <div class="col-6"><div class="o_mcw_fact"><span class="o_mcw_fact_k">Online opvolging</span><span>Tekening, offerte en planning in uw klantportaal</span></div></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
                <section class="s_text_block o_cc o_cc2 pt80 pb80" id="realisaties" data-snippet="s_text_block" data-name="Wat we maken">
                    <div class="container">
                        <p class="o_mcw_eyebrow">Wat we maken</p>
                        <h2 class="mb-4">Maatwerk voor elke ruimte, binnen en buiten</h2>
                        <div class="row g-4">{services}
                            <div class="col-md-6 col-lg-4">
                                <a href="/contactus" class="o_mcw_card o_mcw_card_cta">
                                    <span class="o_mcw_card_body">
                                        <span class="h4 d-block mb-1">Iets anders in gedachten?</span>
                                        <span class="d-block">Vertel ons over uw project. Maatwerk is wat we doen.</span>
                                        <span class="o_mcw_more">Neem contact op</span>
                                    </span>
                                </a>
                            </div>
                        </div>
                    </div>
                </section>
                <section class="s_text_block pt80 pb64" id="werkwijze" data-snippet="s_text_block" data-name="Werkwijze">
                    <div class="container">
                        <p class="o_mcw_eyebrow">Werkwijze</p>
                        <h2 class="mb-4">Zo gaan we te werk</h2>
                        <ol class="row g-4 list-unstyled o_mcw_steps">{steps}
                        </ol>
                    </div>
                </section>
                <section class="s_text_block o_cc o_cc5 pt80 pb80 o_mcw_atelier" data-snippet="s_text_block" data-name="Atelier">
                    <div class="container">
                        <div class="row g-5 align-items-center">
                            <div class="col-lg-6">
                                <img src="{IMG}atelier_4.jpg" class="img img-fluid rounded-3" alt="Het atelier van MC Interieur" loading="lazy"/>
                            </div>
                            <div class="col-lg-6">
                                <p class="o_mcw_eyebrow">Ons atelier</p>
                                <h2>Gemaakt bij ons, niet ingekocht</h2>
                                <p class="lead">Dankzij investeringen in moderne machines en goed opgeleide mensen maken we elk meubel zelf,
                                    met een strakke afwerking en een vakkundige plaatsing.</p>
                                <ul class="list-unstyled o_mcw_machines">{machines}</ul>
                                <a href="/over-ons#atelier" class="btn btn-primary">Bekijk het atelier</a>
                            </div>
                        </div>
                    </div>
                </section>
                <section class="s_text_block pt80 pb80" data-snippet="s_text_block" data-name="Klantportaal">
                    <div class="container">
                        <div class="row g-5 align-items-center">
                            <div class="col-lg-7">
                                <p class="o_mcw_eyebrow">Klantportaal</p>
                                <h2>Uw project, altijd online</h2>
                                <p class="lead">In uw persoonlijke klantportaal vindt u de tekening en de offerte, beantwoordt u onze vragen,
                                    keurt u het ontwerp goed en volgt u de productie, de plaatsingsdatum en de facturen op.</p>
                                <a href="/my" class="btn btn-outline-primary">Naar het klantportaal</a>
                            </div>
                            <div class="col-lg-5">
                                <ul class="list-unstyled o_mcw_checks">
                                    <li>Tekening en offerte samen</li>
                                    <li>Vragen en antwoorden op één plek</li>
                                    <li>Online goedkeuren</li>
                                    <li>Planning en facturen per project</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </section>{cta()}
            </div>
        </xpath>
    </template>
'''


def page_record(key, url, title, meta):
    return f'''
    <record id="page_{key}_page" model="website.page">
        <field name="url">{url}</field>
        <field name="view_id" ref="page_{key}"/>
        <field name="is_published" eval="True"/>
        <field name="website_indexed" eval="True"/>
        <field name="website_meta_title">{e(title)} | MC Interieur</field>
        <field name="website_meta_description">{e(meta)}</field>
    </record>
'''


def service_page(key, url, title, card_text, lead, paragraphs, bullets, images, meta):
    paras = ''.join(f'\n                                <p>{e(p)}</p>' for p in paragraphs)
    checks = ''.join(f'<li>{e(b)}</li>' for b in bullets)
    gallery = ''.join(f'''
                            <div class="col-sm-6 col-lg-4"><img src="{IMG}{img}" class="img img-fluid o_mcw_gallery_img" alt="{e(title)}" loading="lazy"/></div>'''
                      for img in images[1:])
    gallery_section = f'''
                <section class="s_text_block o_cc o_cc2 pt64 pb64" data-snippet="s_text_block" data-name="Realisaties">
                    <div class="container">
                        <h2 class="h3 mb-4">Realisaties</h2>
                        <div class="row g-3 o_mcw_gallery">{gallery}
                        </div>
                    </div>
                </section>''' if gallery else ''
    return f'''
    <template id="page_{key}" name="{e(title)}">
        <t t-call="website.layout">
            <div id="wrap" class="oe_structure o_mcw">{hero(images[0], "Wat we maken", title, lead, BTN_APPOINTMENT)}
                <section class="s_text_block pt64 pb64" data-snippet="s_text_block" data-name="Tekst">
                    <div class="container">
                        <div class="row g-5">
                            <div class="col-lg-7 o_mcw_text">{paras}
                            </div>
                            <div class="col-lg-5">
                                <div class="o_mcw_box">
                                    <h2 class="h5">Wat u mag verwachten</h2>
                                    <ul class="list-unstyled o_mcw_checks mb-0">{checks}</ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>{gallery_section}{cta()}
            </div>
        </t>
    </template>''' + page_record(key, url, title, meta)


def about_page():
    machines = ''.join(f'''
                            <div class="col-md-6"><div class="o_mcw_box o_mcw_box_dark h-100"><h3 class="h5">{e(n)}</h3><p class="mb-0">{e(d)}</p></div></div>'''
                       for n, d in MACHINES)
    gallery = ''.join(f'''
                            <div class="col-sm-6 col-lg-4"><img src="{IMG}{img}" class="img img-fluid o_mcw_gallery_img" alt="Atelier MC Interieur" loading="lazy"/></div>'''
                      for img in ('atelier_1.jpg', 'atelier_2.jpg', 'atelier_3.jpg'))
    head = hero('keuken_4.jpg', "Over ons", "Vakmanschap op maat",
                "Een jong team met een eigen atelier, gespecialiseerd in het ontwerpen, maken en plaatsen van interieur op maat.",
                BTN_APPOINTMENT)
    return f'''
    <template id="page_over_ons" name="Over ons">
        <t t-call="website.layout">
            <div id="wrap" class="oe_structure o_mcw">{head}
                <section class="s_text_block pt64 pb64" data-snippet="s_text_block" data-name="Over ons">
                    <div class="container">
                        <div class="row g-5 align-items-center">
                            <div class="col-lg-7 o_mcw_text">
                                <h2>Van eerste idee tot oplevering</h2>
                                <p class="lead">MC Interieur ontwikkelt, maakt en plaatst keukens, badkamermeubels, dressings, interieurprojecten
                                    en buitenschrijnwerk, volledig op maat.</p>
                                <p>Dankzij onze investeringen in moderne machines en goed opgeleide medewerkers kunt u rekenen op een hoge
                                    kwaliteit, een strakke afwerking en een vakkundige plaatsing. Of u nu een eenvoudig tv-meubel zoekt, één
                                    ruimte wil laten renoveren of uw hele woning wil inrichten, inclusief ramen en binnendeuren: we begeleiden u
                                    van het eerste idee tot de oplevering en de service daarna.</p>
                                <p>We tekenen elk project in TopSolid en optimaliseren de zaagplannen met Ardis, zodat we zo weinig mogelijk
                                    materiaal verspillen. Via uw klantportaal volgt u alles mee.</p>
                            </div>
                            <div class="col-lg-5">
                                <img src="{IMG}about_kitchen.jpg" class="img img-fluid rounded-3" alt="Keuken van MC Interieur" loading="lazy"/>
                            </div>
                        </div>
                    </div>
                </section>
                <section class="s_text_block o_cc o_cc5 pt64 pb64 o_mcw_atelier" id="atelier" data-snippet="s_text_block" data-name="Atelier">
                    <div class="container">
                        <p class="o_mcw_eyebrow">Ons atelier</p>
                        <h2 class="mb-4">De machines achter ons maatwerk</h2>
                        <div class="row g-3 mb-4">{machines}
                        </div>
                        <div class="row g-3 o_mcw_gallery">{gallery}
                        </div>
                    </div>
                </section>{cta()}
            </div>
        </t>
    </template>''' + page_record('over_ons', '/over-ons', "Over ons en ons atelier",
                                  "MC Interieur: interieur op maat uit eigen atelier, met CNC, paneelzaag en eigen plaatsers.")


def form_field(nr, label, name, kind='text', required=False, col='col-lg-6', placeholder='', fill=None,
               model_required=False):
    classes = ['mb-3', col, 's_website_form_field']
    if not model_required:
        classes.append('s_website_form_custom')
    if required:
        classes.append('s_website_form_required')
    if model_required:
        classes.append('s_website_form_model_required')
    mark = '\n                                                        <span class="s_website_form_mark"> *</span>' if required else ''
    req = ' required=""' if required else ''
    fill_attr = f' data-fill-with="{fill}"' if fill else ''
    dtype = {'textarea': 'text', 'email': 'email'}.get(kind, 'char')
    if kind == 'textarea':
        widget = (f'<textarea id="mcw_contact{nr}" class="form-control s_website_form_input" name="{name}"{req} '
                  f'rows="5" placeholder="{e(placeholder)}"></textarea>')
    else:
        itype = {'email': 'email', 'tel': 'tel'}.get(kind, 'text')
        widget = (f'<input id="mcw_contact{nr}" type="{itype}" class="form-control s_website_form_input" name="{name}"'
                  f'{req} placeholder="{e(placeholder)}"{fill_attr}/>')
    return f'''
                                                <div class="{' '.join(classes)}" data-type="{dtype}" data-name="Field">
                                                    <label class="s_website_form_label" for="mcw_contact{nr}">
                                                        <span class="s_website_form_label_content">{e(label)}</span>{mark}
                                                    </label>
                                                    {widget}
                                                </div>'''


def contact_page():
    fields_xml = ''.join([
        form_field(1, "Naam", 'name', required=True, placeholder="Voornaam en naam", fill='name'),
        form_field(2, "Telefoon", 'phone', kind='tel', required=True, placeholder="04xx xx xx xx", fill='phone'),
        form_field(3, "E-mail", 'email_from', kind='email', required=True, model_required=True,
                   placeholder="naam@voorbeeld.be", fill='email'),
        form_field(4, "Gemeente", 'company', placeholder="Waar komt het project?"),
        form_field(5, "Onderwerp", 'subject', required=True, model_required=True, col='col-12',
                   placeholder="bv. Nieuwe keuken"),
        form_field(6, "Uw project", 'description', kind='textarea', required=True, col='col-12',
                   placeholder="Vertel kort wat u zoekt: ruimte, wensen, timing."),
    ])
    return f'''
    <template id="contactus" inherit_id="website.contactus" name="MC Interieur: contact">
        <xpath expr="//div[@id='wrap']" position="replace">
            <div id="wrap" class="oe_structure o_mcw">
                <section class="s_text_block o_cc o_cc5 pt64 pb48 o_mcw_page_head" data-snippet="s_text_block" data-name="Titel">
                    <div class="container">
                        <p class="o_mcw_eyebrow">Contact</p>
                        <h1 class="display-5 fw-bold">Neem contact op</h1>
                        <p class="lead mb-0">Vertel ons over uw project. We nemen zo snel mogelijk contact op om een afspraak te maken.</p>
                    </div>
                </section>
                <section class="s_text_block pt64 pb64" data-snippet="s_text_block" data-name="Formulier">
                    <div class="container">
                        <div class="row g-5">
                            <div class="col-lg-7">
                                <section class="s_website_form" data-vcss="001" data-snippet="s_website_form">
                                    <div class="container px-0">
                                        <form id="contactus_form" action="/website/form/" method="post" enctype="multipart/form-data"
                                              class="o_mark_required" data-mark="*" data-model_name="mail.mail" data-success-mode="redirect"
                                              data-success-page="/contactus-thank-you" data-pre-fill="true">
                                            <div class="s_website_form_rows row s_col_no_bgcolor">{fields_xml}
                                                <div class="mb-3 col-12 s_website_form_field s_website_form_dnone">
                                                    <div class="row s_col_no_resize s_col_no_bgcolor">
                                                        <label class="col-form-label col-sm-auto s_website_form_label" for="mcw_contact7">
                                                            <span class="s_website_form_label_content">Email To</span>
                                                        </label>
                                                        <div class="col-sm">
                                                            <input id="mcw_contact7" type="hidden" class="form-control s_website_form_input" name="email_to"/>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="mb-0 py-2 col-12 s_website_form_submit s_website_form_no_submit_label" data-name="Submit Button">
                                                    <div class="s_website_form_label"/>
                                                    <span id="s_website_form_result"></span>
                                                    <a href="#" role="button" class="btn btn-primary btn-lg s_website_form_send">Verstuur</a>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </section>
                            </div>
                            <div class="col-lg-5">
                                <div class="o_mcw_box mb-4">
                                    <h2 class="h5">MC Interieur</h2>
                                    <ul class="list-unstyled mb-0 o_mcw_footer_contact">
                                        <li t-if="res_company.street or res_company.city">
                                            <t t-out="res_company.street"/><t t-if="res_company.street and res_company.city">, </t>
                                            <t t-out="res_company.zip"/> <t t-out="res_company.city"/>
                                        </li>
                                        <li t-if="res_company.phone"><a t-attf-href="tel:#{{res_company.phone}}" t-out="res_company.phone"/></li>
                                        <li t-if="res_company.email"><a t-attf-href="mailto:#{{res_company.email}}" t-out="res_company.email"/></li>
                                    </ul>
                                </div>
                                <div class="o_mcw_box">
                                    <h2 class="h5">Wat gebeurt er daarna?</h2>
                                    <ol class="mb-0 ps-3">
                                        <li>We bellen u terug en plannen een afspraak.</li>
                                        <li>We komen langs om op te meten en uw wensen te bespreken.</li>
                                        <li>U krijgt tekening en offerte in uw eigen klantportaal.</li>
                                    </ol>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </xpath>
    </template>
'''


def main():
    parts = ['<?xml version="1.0" encoding="utf-8"?>',
             '<!-- Generated by scripts/gen_website_pages.py: change the content there and run it again. -->',
             '<odoo>', homepage()]
    parts += [service_page(*service) for service in SERVICES]
    parts += [about_page(), contact_page(), '</odoo>', '']
    OUT.write_text('\n'.join(parts), encoding='utf-8')
    print(f'written {OUT}')


if __name__ == '__main__':
    main()
