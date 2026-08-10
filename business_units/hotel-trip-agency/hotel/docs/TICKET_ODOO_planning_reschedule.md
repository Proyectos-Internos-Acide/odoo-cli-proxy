# Ticket a Odoo - regresion al confirmar pedidos de alquiler

Texto listo para pegar en el formulario de soporte. Esta en ingles porque este
tipo de regresion acaba en R&D.

---

**Subject**

```
[Regression saas~19.2, still in 19.3] Confirming a rental sales order fails with
"Shift not rescheduled due to conflicts" when the linked planning slot has a resource
```

---

**Description**

```
DATABASE
  Production: machupicchu-afdestiny-production   (saas~19.2.1.3)
  Upgraded on 2026-07-29 04:36 from saas~19.1
  Test DB on saas~19.3.1.3: afdestiny-test-10-ago-2026-test-saas19-0810

APPS INVOLVED
  planning, sale_planning, sale_renting


SUMMARY

Since the upgrade to saas~19.2, confirming a rental sales order fails whenever
the sales order line already has a planning.slot linked AND that slot has a
resource assigned. The error is:

    Shift not rescheduled due to conflicts

There is no actual conflict. The only slot occupying that resource during that
period is the order's own slot. Odoo itself reports overlap_slot_count = 0 and
conflicting_slot_ids = [] on it.

The shift does not even need to move: in our reproduction the slot is already
at exactly the rental period, so the reschedule is a no-op, and it still fails.

This looks like the availability check not excluding the very shift being
rescheduled: it sees the resource as busy because of that same shift.


STEPS TO REPRODUCE

1. A planning.role with exactly one resource (e.g. a hotel room).
   The role has sync_shift_rental = True.
2. Create a planning.slot for that role and resource, for a free period.
3. Create a rental sales order for the product linked to that role, with the
   same period, quantity 1.
4. Link the slot to the sales order line (sale_line_id).
5. Confirm the order.

EXPECTED
  The order confirms and keeps its shift.

ACTUAL
  UserError: "Shift not rescheduled due to conflicts"
  The order stays in draft.


ISOLATION

We ran a controlled test varying one thing at a time. Same product, same
role, same resource, different free periods:

  A) line WITHOUT a pre-linked slot            -> confirms OK
                                                  (Odoo creates the slot itself)
  B) line WITH a pre-linked slot (has resource) -> ERROR
  D) line WITH a pre-linked slot, NO resource   -> confirms OK, keeps the slot,
     assigned (role only)                          no duplicate
  E) same as D but with the resource assigned   -> ERROR

So the trigger is precisely: the linked slot has a resource assigned.


THIS IS A REGRESSION

The exact same pattern worked before the upgrade. On 2026-07-02 (database still
on saas~19.1) four rental orders were confirmed successfully, and in all four
the planning slot had been created and linked BEFORE confirmation:

  SO AYF-VT-2026-07-0033  confirmed 14:06  slot 144 created 14:06
  SO AYF-VT-2026-07-0034  confirmed 14:07  slot 145 created 14:07
  SO AYF-VT-2026-07-0035  confirmed 14:09  slot 146 created 14:09
  SO AYF-VT-2026-07-0036  confirmed 14:16  slot 149 created 14:15

Since 2026-07-29 no rental order can be confirmed this way.


STILL PRESENT IN 19.3

We ran an upgrade test database to saas~19.3.1.3 and the behaviour is
identical. Same error, same trigger.


LIVE REPRODUCTION YOU CAN OPEN

In the 19.3 test database  afdestiny-test-10-ago-2026-test-saas19-0810 :

  AYF-VT-2026-08-0040 (id 51)  - draft, slot 152 with resource assigned
                                 -> pressing Confirm reproduces the error
  AYF-VT-2026-08-0039 (id 50)  - the control: identical but had no pre-linked
                                 slot, confirmed fine
  AYF-VT-2026-08-0042 (id 53)  - case D: pre-linked slot without resource,
                                 confirmed fine


UNRELATED, JUST TO AVOID CONFUSION

There is a second, different message we also hit while investigating:
"No enough resources are available for the shifts in: <role>". That one is
correct behaviour (the line asked for qty 2 of a role that has 1 resource) and
behaves the same in 19.2 and 19.3. It is not what this ticket is about.


IMPACT

Hotel bookings cannot be confirmed through the normal flow. Our operating
procedure is to block the room in the Planning gantt first and create the sales
order afterwards, which is exactly the case that breaks.


CURRENT WORKAROUND

We deployed a server action that, in a single transaction, checks for real
overlaps, clears the resource from the slots, calls action_confirm(), and puts
the resource back. It works, but it means we are bypassing and partially
reimplementing your availability check, which we would rather not maintain.
```

---

## Como enviarlo

Dos vias, cualquiera vale:

1. **Desde la propia base de datos**: clic en tu nombre de usuario, arriba a la
   derecha -> menu **Support**. Es la via recomendada, porque el ticket ya
   llega asociado a la suscripcion y a la base de datos correcta.
2. **Formulario web**: <https://www.odoo.com/help-form>, iniciando sesion con la
   cuenta titular de la suscripcion.

### Antes de enviar

- Comprobar que la base de test `afdestiny-test-10-ago-2026-test-saas19-0810`
  siga viva. Las bases de prueba de upgrade caducan; si ya no existe, quitar
  del ticket la seccion "LIVE REPRODUCTION" o generar una nueva.
- Marcar el ticket como **bug**, no como consulta.
- Si preguntan por acceso: al ser Odoo Online, soporte puede entrar a la base
  directamente.
