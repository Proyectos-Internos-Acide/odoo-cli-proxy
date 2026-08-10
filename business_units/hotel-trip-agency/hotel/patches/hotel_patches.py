#!/usr/bin/env python3
"""Parches del modulo Hotel tras el upgrade a Odoo saas~19.2.

Cada parche sabe comprobarse a si mismo y reaplicarse. Es idempotente:
ejecutarlo dos veces no hace dano.

    uv run python hotel_patches.py              # comprueba produccion
    uv run python hotel_patches.py --apply      # reaplica lo que falte
    uv run python hotel_patches.py --target     # comprueba la instancia de TARGET_MIGRATION_*
    uv run python hotel_patches.py --target --apply

Contexto completo en ../docs/UPGRADE_19.2_INCIDENCIAS.md
"""
import sys, os, re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
from odoo_cli import OdooClient
from odoo_cli.target import get_target_client

COMERCIAL_WEB = 'ayfdestinyeirl@gmail.com'   # comercial por defecto de los leads de la web
CAL_HABITACIONES = 'Rental 24/7'


# ---------------------------------------------------------------- utilidades
def ref(c, module, name):
    """xmlid -> res_id, o None."""
    r = c.search_read('ir.model.data', [['module', '=', module], ['name', '=', name]],
                      fields=['res_id'])
    return r[0]['res_id'] if r else None


def accion_por_nombre(c, nombre):
    r = c.search_read('ir.actions.server', [['name', '=', nombre]], fields=['id'])
    return r[0]['id'] if r else None


def campo(c, model, name):
    r = c.search_read('ir.model.fields', [['model', '=', model], ['name', '=', name]],
                      fields=['id'])
    return r[0]['id'] if r else None


def habitaciones(c):
    """Recursos materiales con rol asignado, es decir las habitaciones."""
    return [x['id'] for x in c.search_read(
        'resource.resource', [['role_ids', '!=', False], ['resource_type', '=', 'material']],
        fields=['id'])]


CAMPO_VIEJO = re.compile(r'(?<![\w])resource_id(?!s)')


# ------------------------------------------------------------------ parches
# 1. vista gantt del hotel
def chk_gantt(c):
    vid = ref(c, 'booking_engine', 'booking_engine_planning_gantt_view')
    if not vid:
        return False, "no existe la vista"
    arch = c.search_read('ir.ui.view', [['id', '=', vid]], fields=['arch_db'])[0]['arch_db']
    gb = re.search(r'default_group_by">([^<]*)<', arch)
    ok = gb and gb.group(1) == 'resource_ids' and 'form_view_id' not in arch
    return ok, f"id={vid} default_group_by={gb and gb.group(1)!r} form_view_id={'si' if 'form_view_id' in arch else 'no'}"


def fix_gantt(c):
    vid = ref(c, 'booking_engine', 'booking_engine_planning_gantt_view')
    arch = c.search_read('ir.ui.view', [['id', '=', vid]], fields=['arch_db'])[0]['arch_db']
    arch = arch.replace('<attribute name="default_group_by">resource_id</attribute>',
                        '<attribute name="default_group_by">resource_ids</attribute>')
    arch = re.sub(r'\s*<attribute name="form_view_id">\d+</attribute>', '', arch)
    c.execute('ir.ui.view', 'write', [vid], {'arch_db': arch})


# 2. vista kanban de planning
def chk_kanban(c):
    vid = ref(c, 'booking_engine', 'planning_kanban_view')
    if not vid:
        return False, "no existe la vista"
    arch = c.search_read('ir.ui.view', [['id', '=', vid]], fields=['arch_db'])[0]['arch_db']
    ok = 'position="after"' in arch and 'position="replace"' not in arch
    return ok, f"id={vid} xpath={'after' if ok else 'replace'}"


def fix_kanban(c):
    vid = ref(c, 'booking_engine', 'planning_kanban_view')
    arch = c.search_read('ir.ui.view', [['id', '=', vid]], fields=['arch_db'])[0]['arch_db']
    c.execute('ir.ui.view', 'write', [vid],
              {'arch_db': arch.replace('<xpath expr="//field[@name=\'sale_line_id\']" position="replace">',
                                       '<xpath expr="//field[@name=\'sale_line_id\']" position="after">')})


# 3. compute de x_sol_resource_ids (formulario de huespedes)
COMPUTE_HUESPEDES = ("for record in self: record['x_sol_resource_ids'] = "
                     "record.x_sale_order_id.order_line.planning_slot_ids.resource_ids")
DEPENDS_HUESPEDES = 'x_sale_order_id.order_line.planning_slot_ids.resource_ids'


def chk_huespedes(c):
    fid = campo(c, 'x_guests_line', 'x_sol_resource_ids')
    if not fid:
        return True, "el modelo x_guests_line no existe aqui"
    f = c.execute('ir.model.fields', 'read', [fid], ['compute'])[0]
    ok = 'x_resource_id' not in (f['compute'] or '')
    return ok, f"id={fid} {'no pasa por x_resource_id' if ok else 'SIGUE usando order_line.x_resource_id'}"


def fix_huespedes(c):
    fid = campo(c, 'x_guests_line', 'x_sol_resource_ids')
    c.execute('ir.model.fields', 'write', [fid],
              {'compute': COMPUTE_HUESPEDES, 'depends': DEPENDS_HUESPEDES})


# 4. campos manuales muertos (many2one con related a un many2many)
MUERTOS = [('sale.order.line', 'x_resource_id'), ('rental.order.wizard.line', 'x_resource_id')]


def chk_muertos(c):
    vivos = [f"{m}.{n}" for m, n in MUERTOS if campo(c, m, n)]
    return not vivos, ("ninguno" if not vivos else f"han reaparecido: {vivos}")


def fix_muertos(c):
    ids = [campo(c, m, n) for m, n in MUERTOS]
    ids = [i for i in ids if i]
    if ids:
        c.execute('ir.model.fields', 'unlink', ids)


# 5. acciones de House Keeping
HK = {
    'HouseKeeping: Set resources as occupied': '''
if slots := record.order_line.planning_slot_ids:
    for slot in slots:
        for res in slot.resource_ids:
            if res.role_ids and any(role.x_is_a_room_offer for role in res.role_ids):
                res['x_occupancy'] = 'occupied'
'''.strip(),
    'HouseKeeping: Set resources as vacant': '''
if slots := record.order_line.planning_slot_ids:
    for slot in slots:
        for res in slot.resource_ids:
            if res.role_ids and any(role.x_is_a_room_offer for role in res.role_ids):
                res['x_occupancy'] = 'vacant'
'''.strip(),
    'HouseKeeping: Daily room update': '''
if (project := env['project.project'].search([('x_is_house_keeping_project', '=', True)], limit=1)):
    newtasks = []
    last_midnight = datetime.datetime.today().replace(hour=0, minute=0)
    for slot in env['planning.slot'].search([('start_datetime', '<', last_midnight),('end_datetime', '>', last_midnight)]):
        for res in slot.resource_ids:
            if not any(role.x_is_a_room_offer for role in res.role_ids):
                continue
            end_today = slot.end_datetime < last_midnight + datetime.timedelta(hours=24)
            if (end_today and not slot.role_id.x_has_checkout_cleaning) or (not end_today and not slot.role_id.x_has_stayover_cleaning):
                continue
            res.write({'x_occupancy': 'due_out' if end_today else 'stayover'})
            newtasks.append({
                'name': "HK " + res.name,
                'project_id': project.id,
                'partner_id': slot.sale_line_id.order_id.partner_id.id,
                'description': "Automatically generated house keeping task.",
                'date_deadline': (last_midnight + datetime.timedelta(hours=24)),
                'x_resource_id': res.id,
                'x_cleaning': 'checkout' if end_today else 'stayover',
                'user_ids': [(5,0)],
            })
    env['project.task'].create(newtasks)
'''.strip(),
}


def chk_hk(c):
    malas = []
    for nombre in HK:
        aid = accion_por_nombre(c, nombre)
        if not aid:
            continue
        code = c.execute('ir.actions.server', 'read', [aid], ['code'])[0]['code'] or ''
        n = len(CAMPO_VIEJO.findall(code))
        if n:
            malas.append(f"{aid}({n})")
    return not malas, ("las 3 usan resource_ids" if not malas
                       else f"siguen con slot.resource_id: {malas}")


def fix_hk(c):
    for nombre, code in HK.items():
        aid = accion_por_nombre(c, nombre)
        if aid:
            c.execute('ir.actions.server', 'write', [aid], {'code': code})


# 6. comercial por defecto de los leads de la web
def chk_lead(c):
    w = c.search_read('website', [['id', '=', 1]], fields=['crm_default_user_id'])[0]
    return bool(w['crm_default_user_id']), f"crm_default_user_id={w['crm_default_user_id']}"


def fix_lead(c):
    u = c.search_read('res.users', [['login', '=', COMERCIAL_WEB]], fields=['id'])
    if u:
        c.execute('website', 'write', [1], {'crm_default_user_id': u[0]['id']})


# 7. accion y boton para confirmar pedidos de hotel
NOMBRE_ACCION = 'Confirmar pedido de hotel'
NOMBRE_VISTA = 'sale.order.form.hotel.confirm'
CODE_CONFIRMAR = '''
for order in records:
    slots = env["planning.slot"].search([("sale_order_id", "=", order.id)])
    for s in slots:
        if not s.resource_ids or not s.start_datetime or not s.end_datetime:
            continue
        choques = env["planning.slot"].search([
            ("id", "!=", s.id),
            ("resource_ids", "in", s.resource_ids.ids),
            ("start_datetime", "<", s.end_datetime),
            ("end_datetime", ">", s.start_datetime),
        ])
        if choques:
            detalle = ", ".join(
                "%s (%s)" % (ch.resource_ids[:1].name or "?", ch.sale_order_id.name or "sin pedido")
                for ch in choques)
            raise UserError(
                "No se puede confirmar: la habitacion ya esta ocupada en esas fechas por %s" % detalle)
    guardado = {s.id: s.resource_ids.ids for s in slots}
    con_recurso = slots.filtered(lambda s: s.resource_ids)
    if con_recurso:
        con_recurso.write({"resource_ids": [(5, 0, 0)]})
    order.action_confirm()
    for s in slots:
        ids = guardado.get(s.id) or []
        if ids:
            s.write({"resource_ids": [(6, 0, ids)]})
'''.strip()


def chk_confirmar(c):
    aid = accion_por_nombre(c, NOMBRE_ACCION)
    vid = c.search_read('ir.ui.view', [['name', '=', NOMBRE_VISTA]], fields=['id'])
    return bool(aid and vid), f"accion={aid} vista={vid[0]['id'] if vid else None}"


def fix_confirmar(c):
    modelo = c.search_read('ir.model', [['model', '=', 'sale.order']], fields=['id'])[0]['id']
    aid = accion_por_nombre(c, NOMBRE_ACCION)
    if aid:
        c.execute('ir.actions.server', 'write', [aid], {'code': CODE_CONFIRMAR})
    else:
        aid = c.execute('ir.actions.server', 'create', [{
            'name': NOMBRE_ACCION, 'model_id': modelo, 'state': 'code', 'code': CODE_CONFIRMAR,
            'binding_model_id': modelo, 'binding_view_types': 'form,list'}])
        aid = aid[0] if isinstance(aid, list) else aid
    arch = f'''<data>
  <xpath expr="//button[@id='action_confirm']" position="before">
    <button string="Confirmar" name="{aid}" type="action" class="btn-primary" data-hotkey="q"
            invisible="not is_rental_order or state not in ('draft', 'sent')"/>
  </xpath>
  <xpath expr="//button[@id='action_confirm']" position="attributes">
    <attribute name="invisible">state != 'sent' or is_rental_order</attribute>
  </xpath>
  <xpath expr="//button[@name='action_confirm'][not(@id)]" position="attributes">
    <attribute name="invisible">state != 'draft' or is_rental_order</attribute>
  </xpath>
</data>'''
    base = c.search_read('ir.ui.view', [['model', '=', 'sale.order'], ['type', '=', 'form'],
                                        ['mode', '=', 'primary']], fields=['id'])[0]['id']
    vid = c.search_read('ir.ui.view', [['name', '=', NOMBRE_VISTA]], fields=['id'])
    if vid:
        c.execute('ir.ui.view', 'write', [vid[0]['id']], {'arch_db': arch})
    else:
        c.execute('ir.ui.view', 'create', [{
            'name': NOMBRE_VISTA, 'model': 'sale.order', 'inherit_id': base,
            'mode': 'extension', 'priority': 99, 'arch_db': arch}])


# 8. habitaciones en el calendario 24/7
def chk_calendarios(c):
    hab = habitaciones(c)
    if not hab:
        return True, "no hay habitaciones"
    mal = [x['name'] for x in c.search_read('resource.resource', [['id', 'in', hab]],
                                            fields=['name', 'calendar_id'])
           if x['calendar_id'] and x['calendar_id'][1] != CAL_HABITACIONES]
    return not mal, (f"las {len(hab)} en {CAL_HABITACIONES}" if not mal else f"fuera del 24/7: {mal}")


def fix_calendarios(c):
    cal = c.search_read('resource.calendar', [['name', '=', CAL_HABITACIONES]], fields=['id'])
    if cal:
        c.execute('resource.resource', 'write', habitaciones(c), {'calendar_id': cal[0]['id']})


# 9. recurso duplicado
def chk_duplicado(c):
    dups = c.search_read('resource.resource',
                         [['resource_type', '=', 'material'], ['role_ids', '=', False],
                          ['name', 'in', ['301', '401', '501', '601', '701', '702']]],
                         fields=['name'])
    return not dups, ("ninguno visible" if not dups
                      else f"habitaciones sin rol activas: {[(d['id'], d['name']) for d in dups]}")


def fix_duplicado(c):
    dups = c.search_read('resource.resource',
                         [['resource_type', '=', 'material'], ['role_ids', '=', False],
                          ['name', 'in', ['301', '401', '501', '601', '701', '702']]],
                         fields=['id'])
    if dups:
        c.execute('resource.resource', 'write', [d['id'] for d in dups], {'active': False})


PARCHES = [
    ('gantt',       'Vista gantt del hotel: default_group_by=resource_ids', chk_gantt, fix_gantt, 'booking_engine'),
    ('kanban',      'Vista kanban de planning: xpath position=after',       chk_kanban, fix_kanban, 'booking_engine'),
    ('huespedes',   'Compute de x_sol_resource_ids sin x_resource_id',      chk_huespedes, fix_huespedes, 'booking_engine'),
    ('muertos',     'Campos manuales x_resource_id borrados',               chk_muertos, fix_muertos, 'booking_engine'),
    ('housekeeping', 'Acciones House Keeping con resource_ids',             chk_hk, fix_hk, '__cloc_exclude__'),
    ('leads',       'Comercial por defecto de los leads de la web',         chk_lead, fix_lead, 'dato propio'),
    ('confirmar',   'Accion y boton para confirmar pedidos de hotel',       chk_confirmar, fix_confirmar, 'nuestro'),
    ('calendarios', 'Habitaciones en el calendario Rental 24/7',            chk_calendarios, fix_calendarios, 'dato propio'),
    ('duplicado',   'Recurso de habitacion duplicado archivado',            chk_duplicado, fix_duplicado, 'dato propio'),
]


def main():
    aplicar = '--apply' in sys.argv
    if '--target' in sys.argv:
        c = get_target_client()
        if c is None:
            sys.exit("TARGET_MIGRATION_* no configurado en el .env")
    else:
        c = OdooClient()
    c.connect()
    print(f"base: {c.db}\n")

    fallan = []
    for clave, titulo, chk, fix, duenio in PARCHES:
        try:
            ok, detalle = chk(c)
        except Exception as e:
            ok, detalle = False, f"error al comprobar: {str(e)[:90]}"
        print(f"  [{'OK ' if ok else 'FALTA'}] {clave:13} {titulo:52} {detalle}")
        if not ok:
            fallan.append((clave, titulo, chk, fix))

    if not fallan:
        print("\nTodos los parches estan aplicados.")
        return
    if not aplicar:
        print(f"\n{len(fallan)} parche(s) sin aplicar. Re-ejecutar con --apply.")
        return

    print(f"\n=== aplicando {len(fallan)} parche(s) ===")
    for clave, titulo, chk, fix in fallan:
        try:
            fix(c)
            ok, detalle = chk(c)
            print(f"  [{'OK ' if ok else 'FALLO'}] {clave:13} {detalle}")
        except Exception as e:
            print(f"  [ERROR] {clave:13} {str(e)[:140]}")


main()
