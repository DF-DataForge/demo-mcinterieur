"""Move the fixed intake fields of 20.0.1.0.0 into the configurable intake (properties) of 20.0.1.1.0.

The old columns stay in the table (Odoo does not drop them); they are read with SQL and copied once.
"""
from odoo import SUPERUSER_ID, api

# question name -> properties field (same names as in data/mc_intake_data.xml)
SECTIONS = {
    'intake_general': ['room', 'situation', 'budget', 'third_party', 'third_party_contact', 'style'],
    'intake_space': ['space_width', 'space_height', 'space_depth', 'ceiling_height', 'measure_state', 'floor_state',
                     'walls_state', 'wall_type', 'obstacles', 'access_info'],
    'intake_materials': ['carcass_material', 'carcass_color', 'front_material', 'front_color', 'gloss', 'grain',
                         'edge_finish'],
    'intake_hardware': ['handles', 'handle_model', 'hinges', 'drawers', 'inner_drawers', 'layout_wishes', 'lighting'],
    'intake_appliances': ['worktop', 'appliances', 'fridge_niche', 'hood', 'sink', 'appliance_supply'],
    'intake_installation': ['installer', 'dismantle', 'disposal', 'utilities', 'parking'],
}


def migrate(cr, version):
    cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'mc_project'")
    columns = {row[0] for row in cr.fetchall()}
    old_names = [name for names in SECTIONS.values() for name in names if name in columns]
    has_type = 'project_type' in columns
    if not old_names and not has_type:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    select = ', '.join(['id'] + (['project_type'] if has_type else []) + old_names)
    cr.execute(f"SELECT {select} FROM mc_project")  # noqa: S608 - column names come from the list above
    rows = cr.dictfetchall()
    types = {t.code: t for t in env['mc.project.type'].with_context(active_test=False).search([('code', '!=', False)])}
    template = env.ref('mc_interieur.intake_template_default', raise_if_not_found=False)
    key_by_name = {name: f"{field}.{name}" for field, names in SECTIONS.items() for name in names}
    for row in rows:
        project = env['mc.project'].browse(row['id'])
        vals = {}
        if template and not project.intake_template_id:
            vals['intake_template_id'] = template.id
        if has_type and row.get('project_type') and not project.project_type_id:
            project_type = types.get(row['project_type'])
            if project_type:
                vals['project_type_id'] = project_type.id
        for field, names in SECTIONS.items():
            values = dict(project[field] or {})
            for name in names:
                value = row.get(name)
                if value not in (None, '', False) and not values.get(name):
                    values[name] = value
            if values:
                vals[field] = values
        if vals:
            project.write(vals)
    # open questions pointed to the old field names
    for question in env['mc.project.question'].search([('field_name', 'in', list(key_by_name))]):
        question.field_name = key_by_name[question.field_name]
    cr.execute("UPDATE mc_project_question SET field_name = 'project_type_id' WHERE field_name = 'project_type'")
