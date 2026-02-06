# Guia de Atributos de Producto en Odoo 19

## Que son los atributos de producto

Los atributos de producto definen caracteristicas como WiFi, numero de camas, tipo de bano, etc.
Se muestran en la seccion de "Especificaciones" del ecommerce y pueden o no crear variantes.

---

## Modos de creacion de variantes

### `no_variant` (Nunca crear variante)
- El atributo aparece como **especificacion tecnica** en el ecommerce
- **No crea** productos adicionales (variantes)
- Ideal para: WiFi, Air Conditioning, TV, amenidades fijas
- Cada producto (habitacion) tiene un solo valor por atributo

**Ejemplo**: Apartment 301 tiene WiFi=Si, AC=Si, TV=Si
→ Aparece en specs del ecommerce pero sigue siendo 1 solo producto

### `always` (Siempre crear variante)
- Crea una **variante** por cada combinacion de valores
- Cada variante puede tener precio diferente
- Ideal para: opciones que cambian el precio (ej. Desayuno incluido vs no)

**Ejemplo**: Si Hotel tiene atributo "Breakfast" con valores [Incluido, No incluido]
→ Se crean 2 variantes: "Hotel (Breakfast Incluido)" y "Hotel (Breakfast No incluido)"
→ Cada una puede tener precio diferente

### `dynamic` (Crear bajo demanda)
- Similar a `always` pero las variantes se crean solo cuando se necesitan
- Util cuando hay muchas combinaciones posibles pero pocas se usan

---

## Restriccion importante

**No se puede cambiar `create_variant` si el atributo ya esta asignado a productos con variantes.**

Si necesitas cambiar un atributo de `always` a `no_variant`:
1. Ir a cada producto que usa el atributo
2. Eliminar el atributo del producto (Configurar Variantes > eliminar la linea)
3. Cambiar el modo del atributo
4. Volver a agregar el atributo al producto

Esto se debe hacer desde la UI (Productos > [Producto] > Configurar Variantes).

---

## Tipos de atributos segun uso

### Atributos de Hotel/Stay (recomendado: no_variant)
Caracteristicas fijas de habitaciones como WiFi, AC, TV, amenidades.
Se muestran como especificaciones tecnicas en el ecommerce sin crear variantes.

### Atributos de Tours (recomendado: always o no_variant segun caso)
Informacion variable por tour como punto de partida, hora de salida, que incluye.
Si el valor cambia el precio, usar `always`. Si es solo informativo, usar `no_variant`.

### Atributos con variantes de precio (recomendado: always)
Opciones que modifican el precio del producto, como tipo de desayuno o numero de huespedes.
Usar `always` para que cada combinacion tenga su precio propio.

> **Nota**: Para el estado actual de los atributos en la instancia de prueba,
> ver `incidencies/ATTR_CREATE_VARIANT_BLOCKED.md`

---

## Como corregir atributos con restriccion (desde UI)

Para cambiar un atributo de `always` a `no_variant` cuando ya esta en uso:

1. **Ir a Inventario > Productos > [Producto que usa el atributo]**
2. **Pestana "Atributos y Variantes"**
3. **Eliminar** la linea del atributo problematico
4. **Guardar** el producto
5. Repetir para todos los productos que usen ese atributo
6. **Ir a Configuracion > Atributos > [Atributo]**
7. Cambiar "Modo de creacion de variantes" a **"Nunca (no_variant)"**
8. **Volver a agregar** el atributo a los productos

> **Importante**: Al eliminar el atributo del producto, se eliminan las variantes
> asociadas. Si hay ordenes de venta o facturas vinculadas a esas variantes,
> considerar si es necesario hacer el cambio.

---

## Recomendacion para nuevos atributos

Al crear un nuevo atributo, decidir segun este criterio:

| Situacion | Modo recomendado |
|-----------|------------------|
| Caracteristica fija (WiFi, AC, TV) | `no_variant` |
| Opcion que cambia el precio (Desayuno, Guests) | `always` |
| Muchas combinaciones, pocas usadas | `dynamic` |
| Informacion descriptiva (Incluye, No incluye) | `no_variant` o `always` segun necesidad |
