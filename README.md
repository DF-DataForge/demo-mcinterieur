# MC Interieur: custom-furniture flow for Odoo 20.0

Odoo 20.0 module `mc_interieur` for a cabinet maker / interior builder. It follows the flow from the
clickable mockup in [`mockup/intake-odoo.html`](mockup/intake-odoo.html):

intake by the sales rep → drawing in TopSolid → quote generated from the TopSolid material list →
customer approves drawing **and** quote in the portal → work preparation and Ardis export →
scanning at the panel saw, CNC and assembly bench → installation planning and signed handover.

The user interface is in Dutch (Flemish), like the mockup.

## Prerequisites

Odoo **20.0** (Community or Enterprise). The module only uses Community apps.

| Odoo app | Technical name | Why |
|---|---|---|
| Contacts | `contacts` | Customers, suppliers |
| Sales | `sale_management` | Quotes generated from the TopSolid material list, confirmed on approval |
| Inventory | `stock` | Sheet material, edge banding, hardware, consumption after the Ardis run |
| Purchase | `purchase` | Ordering materials the cutting batch is short of |
| Customer portal | `portal` | Customer validation of drawing and quote |

Installing `mc_interieur` installs these automatically (they are in `depends`).

Recommended, not required:

* **Belgium - Accounting** (`l10n_be`): gives the 6 % and 21 % sales VAT the quotes look for.
  Without it the quote uses the product's default sales tax and says so in the project chatter.

Not used on purpose: Manufacturing (MRP), Planning (Enterprise), Barcode (Enterprise). Planning uses the
standard calendar view; scanning uses the module's own scan station, which works with any USB or
Bluetooth scanner that types the code and ends with Enter.

## Install

```bash
# addons path: Odoo's own addons plus the root of this repository
odoo-bin --addons-path=/path/to/odoo/addons,/path/to/MCInterieur \
         -d mc_demo -i mc_interieur --with-demo
```

Or in an existing database: *Apps → Update Apps List → search "MC Interieur" → Activate*.
Demo data only loads in a database created with demo data (`--with-demo`, or the "Demo data" box in the
database manager).

## Demo logins

Demo users log in with their e-mail address; all demo passwords are `demo`. Change or remove these users on a real database.

### Employees (backend, `/odoo`)

| Login | Name | Role | What to show |
|---|---|---|---|
| `admin` | Administrator | Everything | |
| `sofie@interieur-demo.example.com` | Sofie Verhaeghe | Sales | Projects, intake, quotes |
| `jonas@interieur-demo.example.com` | Jonas De Vos | Drawer | Drawing versions, open questions, send drawing + quote |
| `lien@interieur-demo.example.com` | Lien Martens | Work preparation, manager | Cutting batches, Ardis export, ordering, material mapping |
| `kevin@interieur-demo.example.com` | Kevin Desmet | Shop floor + installation team 1 | *Interieur → Werkvloer* (saw, CNC, assembly), *Plaatsing → Mijn planning* |
| `bart@interieur-demo.example.com` | Bart Vandenberghe | Installer, team 1 | *Plaatsing → Mijn planning*, sign-off on site |
| `jens@interieur-demo.example.com` | Jens Coppens | Installer, team 2 | *Plaatsing → Mijn planning* |

### Customers (portal, `/my/interieur`)

| Login | Customer | Projects in the portal |
|---|---|---|
| `karen.maes@example.com` | Karen Maes | **Keuken Maes** (drawing v2 + quote waiting for approval, 2 open questions) and **Badkamermeubel Maes** (approved, at the CNC) |
| `tom.vandamme@example.com` | Tom Van Damme | **Dressing Van Damme** (at the saw) and **TV-wand Van Damme** (approved, in work preparation) |
| `jan.peeters@example.com` | Jan Peeters | **Keuken Peeters** (intake) and **Inkomkast Peeters** (being drawn) |
| `an.desmet@example.com` | An De Smet | **Bureau-kast De Smet** (assembly, installation planned this week) |

## Demo script

1. **Intake** (`sofie@interieur-demo.example.com`): *Interieur → Projecten → Keuken Peeters*. Nothing is mandatory; the banner shows
   how much is filled in. Pick a drawer and click *Doorsturen naar tekenaar*: empty questions become open
   questions and the drawer gets an activity.
2. **Quote from TopSolid** (`jonas@…` or `lien@interieur-demo.example.com`): *Inkomkast Peeters → Offerte*. Generating fails because
   "Eiken fineer 19" has no Ardis code yet. Link it in *Configuratie → Materiaalkoppeling* (product
   *FIN-EIK-19*), then *Offerte genereren*. Add a drawing version and click
   *Tekening + offerte naar klant*.
3. **Customer portal** (`karen.maes@example.com`): *Mijn interieurprojecten → Keuken Maes*. Approval is blocked until both
   questions are answered. Answer them, type a name, tick the box, approve: the drawing is approved, the
   quote becomes a sales order and the project goes to work preparation. Or send change requests: each
   line becomes an open question for the drawer.
4. **Work preparation** (`lien@interieur-demo.example.com`): *Werkvoorbereiding → Zaagbatches*. The draft batch for TV-wand Van Damme
   is short of MDF; *Bestellen voor tekorten* creates and confirms a purchase order per supplier. Then
   *Exporteer naar Ardis* (CSV download) and *Resultaat Ardis inlezen* (simulate, or upload Ardis' CSV with
   columns `Materiaal;Verbruik`). Stock is consumed and the projects move to *Zagen*.
5. **Shop floor** (`kevin@interieur-demo.example.com`): *Werkvloer → Paneelzaag*: scan (or click *Scan volgend etiket*) to mark
   parts sawn. *CNC*: scanning loads the TopSolid program name; confirm when done. *Montage werkplaats*:
   scanned parts are collected per cabinet, then *Kast gemonteerd*. Projects move forward automatically.
6. **Installation** (`bart@interieur-demo.example.com`): *Plaatsing → Mijn planning* (calendar). Open Bureau-kast De Smet: site
   details from the intake, checklist, snag list, photos, customer signature. Signing is blocked while
   checklist items are open; after signing the project is *Opgeleverd*.

## Configuring the intake

The intake questions and their options are managed in Odoo, no code needed (manager rights):

* **Interieur → Configuratie → Intakevragen**: one tab per intake tab. Add a question (text, number,
  choice with options, yes/no, date, ...), rename it, change its options or drag it to another position.
  Changes apply to all projects at once. Managers can also add a question straight from a project form.
* **Interieur → Configuratie → Projecttypes**: the project types, whether the *Werkblad & toestellen* tab is
  shown, and the default number of installation days on the quote.

Nothing is mandatory: an empty question becomes an open question for the drawer when the intake is handed
over, and it closes by itself once it is answered. A few questions drive logic by their technical name
(`situation`, `worktop`, `appliance_supply`, `handles`, `handle_model`, `drawers`, `lighting`, `dismantle`,
`disposal`, `access_info`, `parking`, `utilities`): rename their label freely, but do not delete them.

## Demo TopSolid and Ardis files

Sample files are in [`mc_interieur/static/demo_files/`](mc_interieur/static/demo_files/) and are also
attached to the demo projects (download them from the project chatter):

* `topsolid_keuken_peeters.csv`: read it into *Keuken Peeters* (tab *Onderdelen (TopSolid)* →
  *TopSolid-materiaallijst inlezen*), then generate the quote.
* `topsolid_inkomkast_peeters_v2.csv`: revised list for *Inkomkast Peeters*; still needs the Ardis code
  for "Eiken fineer 19".
* `ardis_export_voorbeeld.csv`: what Odoo writes for Ardis, to set up the Ardis import profile.
* `ardis_resultaat_tv_wand_vandamme.csv`: upload it in *Resultaat Ardis inlezen* for the TV-wand batch.

The [demo files README](mc_interieur/static/demo_files/README.md) describes the columns.

## Repository layout

```
mc_interieur/          Odoo 20.0 module
  controllers/         customer portal routes (/my/interieur)
  data/                sequences, quote service products, portal card
  demo/                demo users, materials, projects (loaded with --with-demo)
  models/              projects, intake, questions, drawing versions, parts, labels,
                       cutting batches, installations, quote calculation
  security/            groups + ir.access.csv (Odoo 20 access rules)
  static/src/          scan station (Owl client action), portal styles
  tests/               flow and portal tests
  views/               backend views, menus, portal templates
  wizard/              Ardis result import
mockup/                intake-odoo.html: clickable HTML mockup the module is based on
                       klant-traject.html: the project in 8 steps, for customers
                       interne-flow.html: the internal flow in 9 phases, for the team
.github/workflows/     installs the module with demo data on Odoo 20.0 and runs the tests
```

## What is simulated

* **TopSolid**: there is no live link. The material list is stored on the project as parts
  (*Onderdelen (TopSolid)* tab); the demo data plays the role of the TopSolid export. Reading the real
  export file is the next integration step and depends on what TopSolid 6 can export.
* **Ardis**: the CSV columns are an assumption. Get a sample import file and import profile from Ardis
  or the reseller, then adjust `CSV_HEADER` in `models/mc_cutting_batch.py`.
* **CNC**: the scan station shows the program name that the TopSolid plugin produced; it does not load
  the program on the machine.
* **Prices and rates**: sheet, edge banding and hardware prices are the products' cost prices. Machine,
  labour, lacquer and installation rates have defaults in code and can be overridden with system
  parameters `mc_interieur.rate_machine_hour`, `rate_labour_hour`, `rate_lacquer_m2`,
  `rate_install_day`, `saw_minutes_piece`, `cnc_minutes_piece`, `assembly_hours_cabinet`.
