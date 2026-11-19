# Demo files

Sample files to show the TopSolid and Ardis steps of the flow. They are also attached to the demo
records in Odoo (chatter of the project or cutting batch), so you can download them from there.

| File | Where to use it | What it shows |
|---|---|---|
| `topsolid_keuken_peeters.csv` | Project *Keuken Peeters* → tab *Onderdelen (TopSolid)* → *TopSolid-materiaallijst inlezen* | A full kitchen parts list straight from TopSolid. After reading it in, generate the quote. |
| `topsolid_inkomkast_peeters_v2.csv` | Project *Inkomkast Peeters* → same button | A revised parts list (third door, middle panel). Uses "Eiken fineer 19", which still needs an Ardis code. |
| `ardis_export_voorbeeld.csv` | Reference only | What Odoo writes for Ardis: one line per labelled piece. Use it to set up the import profile in Ardis. |
| `ardis_resultaat_tv_wand_vandamme.csv` | Cutting batch of *TV-wand Van Damme* → *Exporteer naar Ardis* → *Resultaat Ardis inlezen* → "Exportbestand van Ardis opladen" | Sheets and edge banding Ardis reports as used. Odoo books them out of stock. |

## Formats

**TopSolid parts list** (semicolon, header on line 1):
`Kast;Onderdeel;Materiaal;Lengte;Breedte;Dikte;Aantal;Nerf;Kant_L1;Kant_L2;Kant_B1;Kant_B2;CNC`

* `Materiaal` is the material name as it appears in TopSolid; Odoo translates it to the Ardis code
  through *Configuratie → Materiaalkoppeling*.
* `Kant_*` are edge banding codes (the Ardis / stock code), `Nerf` is 1 or 0, `CNC` is the program
  file the TopSolid CNC plugin writes.

**Ardis result** (semicolon, header on line 1): `Materiaal;Verbruik`, other columns are ignored.
`Verbruik` is sheets for sheet material and metres for edge banding.

Both formats are assumptions for the demo. Replace them with the real TopSolid 6 export template and
the Ardis import/export profile once those are known.
