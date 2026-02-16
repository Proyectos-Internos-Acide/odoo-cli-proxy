# Incidencia: Atributos con create_variant bloqueado

**Instancia**: machupicchuafdestiny1 (test)
**Fecha**: 2026-02-06

## Problema

12 atributos de hotel no se pudieron cambiar de `create_variant=always` a `no_variant`
porque ya estan asignados a productos con variantes existentes.

Odoo error: "No puede cambiar el modo de creacion de variantes del atributo X,
se utiliza en los siguientes productos: Y"

## Atributos afectados

| ID | Nombre | Producto bloqueante |
|----|--------|-------------------|
| 24 | Adicionales | Lomo Saltado |
| 26 | Beds | (productos hotel) |
| 27 | Bathrooms | (productos hotel) |
| 28 | Room Service | (productos hotel) |
| 29 | Warm Water | (productos hotel) |
| 31 | Telefono | (productos hotel) |
| 32 | Servicio de Lavanderia | (productos hotel) |
| 33 | Estacionamiento Privado | (productos hotel) |
| 34 | Area | (productos hotel) |
| 35 | TV Cable | (productos hotel) |
| 36 | TVs | (productos hotel) |
| 37 | Habitaciones | (productos hotel) |

## Solucion manual

Para cada atributo:
1. Ir a cada producto que lo usa > Atributos y Variantes > eliminar la linea
2. Guardar el producto
3. Cambiar el atributo a `no_variant` desde Configuracion > Atributos
4. Volver a agregar el atributo al producto

## Estado

Pendiente. Se documenta para resolver manualmente desde la UI antes de pasar a produccion.
