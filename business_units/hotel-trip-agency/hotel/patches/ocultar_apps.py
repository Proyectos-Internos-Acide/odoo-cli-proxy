#!/usr/bin/env python3
"""Oculta de la pantalla de aplicaciones las apps que no se usan.

Archiva el menu raiz (active=False). El modulo sigue instalado y sus datos
intactos; solo desaparece del grid de apps y del selector.

    uv run python ocultar_apps.py            # comprobar
    uv run python ocultar_apps.py --apply    # ocultarlas
    uv run python ocultar_apps.py --mostrar  # volver a mostrarlas todas
    uv run python ocultar_apps.py --target   # contra TARGET_MIGRATION_*

Un upgrade de plataforma normalmente respeta el archivado, pero si un modulo
reescribe su menu en su XML lo resucita (nos paso con 'hr' al pasar a 19.3).
Por eso conviene reejecutar la comprobacion despues de cada actualizacion.

NO es un control de acceso: ocultar el menu no impide llegar al modelo por URL
ni desde enlaces en otros registros. Para eso hacen falta grupos y permisos.
"""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
from odoo_cli import OdooClient
from odoo_cli.target import get_target_client

# modulo -> como se llama la app en la interfaz
OCULTAR = {
    'point_of_sale': 'Punto de venta',
    'pos_enterprise': 'Pantalla para cocina',
    'hr_timesheet':   'Registro de horas',
    'social':         'Redes sociales',
    'stock':          'Inventario',
    'stock_barcode':  'Codigo de barras',
    'planning':       'Planeacion',
    'project_todo':   'Actividades pendientes',
    'accountant':     'Contabilidad',
    'data_recycle':   'Limpieza de datos',
    'documents':      'Documentos',
    'hr':             'Empleados',
    'utm':            'Rastreador de enlaces',
}


def menu_raiz(c, modulo):
    """El menu de primer nivel que pertenece a ese modulo."""
    imd = c.search_read('ir.model.data', [['module', '=', modulo], ['model', '=', 'ir.ui.menu']],
                        fields=['res_id'])
    if not imd:
        return None
    ids = [r['res_id'] for r in imd]
    raiz = c.execute('ir.ui.menu', 'search_read', [['id', 'in', ids], ['parent_id', '=', False]],
                     ['name', 'active'], 0, 5, 'id')
    return raiz[0] if raiz else None


def main():
    aplicar = '--apply' in sys.argv
    mostrar = '--mostrar' in sys.argv
    if '--target' in sys.argv:
        c = get_target_client()
        if c is None:
            sys.exit("TARGET_MIGRATION_* no configurado en el .env")
    else:
        c = OdooClient()
    c.connect()
    print(f"base: {c.db}\n")

    objetivo = not mostrar          # True = queremos que este oculta
    pendientes = []
    for modulo, etiqueta in sorted(OCULTAR.items(), key=lambda x: x[1]):
        m = menu_raiz(c, modulo)
        if not m:
            print(f"  [n/a  ] {etiqueta:24} ({modulo}) no tiene menu raiz")
            continue
        oculta = not m['active']
        ok = oculta == objetivo
        estado = 'oculta' if oculta else 'visible'
        print(f"  [{'OK   ' if ok else 'CAMBIA'}] {etiqueta:24} ({modulo:15}) menu {m['id']:4} {estado}")
        if not ok:
            pendientes.append((m['id'], etiqueta))

    if not pendientes:
        print(f"\nNada que hacer: todas {'visibles' if mostrar else 'ocultas'}.")
        return
    if not (aplicar or mostrar):
        print(f"\n{len(pendientes)} app(s) por ocultar. Re-ejecutar con --apply.")
        return

    c.execute('ir.ui.menu', 'write', [i for i, _ in pendientes], {'active': objetivo is False})
    print(f"\n{'Mostradas' if mostrar else 'Ocultadas'} {len(pendientes)} app(s): "
          f"{', '.join(e for _, e in pendientes)}")

    visibles = c.execute('ir.ui.menu', 'search_read', [['parent_id', '=', False]],
                         ['name'], 0, 100, 'sequence,name')
    print(f"\napps visibles ahora: {len(visibles)}")
    print("  " + " · ".join(v['name'] for v in visibles))


main()
