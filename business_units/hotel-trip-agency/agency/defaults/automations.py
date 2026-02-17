"""Automation code for agency tour operations.

Contains Python code executed by base.automation server actions.
All code runs server-side inside Odoo (not XML-RPC).
"""

# ── Automation 15: Validate Tour Dates ────────────────────────────────────
# Model: sale.order | Trigger: on_write | Fields: x_tour_start_date, x_tour_end_date

VALIDATE_TOUR_DATES = '''\
for record in records:
    if record.x_is_tour and record.x_tour_start_date and record.x_tour_end_date:
        if record.x_tour_end_date < record.x_tour_start_date:
            raise UserError("La Fecha Fin del Tour no puede ser anterior a la Fecha Inicio del Tour.")
'''

# ── Automation 16: Propagate Tour Data to Tasks ───────────────────────────
# Model: project.task | Trigger: on_create
# When a task is created (e.g. from SO confirmation via service_tracking),
# pull tour dates and passenger count from the linked sale order.
# Previous approach used on_state_set on sale.order but that fires BEFORE
# tasks are created by service_tracking, so tasks don't exist yet.

PROPAGATE_TOUR_DATA = '''\
for record in records:
    so = record.sale_order_id
    if not so or not so.x_is_tour:
        continue
    vals = {}
    if so.x_tour_start_date:
        vals['x_tour_start_date'] = so.x_tour_start_date
    if so.x_tour_end_date:
        vals['x_tour_end_date'] = so.x_tour_end_date
    if so.x_num_passengers:
        vals['x_seats_needed'] = so.x_num_passengers
    if vals:
        record.write(vals)
'''

# ── Automation 17: Warn Vehicle Date Conflict ─────────────────────────────
# Model: project.task | Trigger: on_write | Fields: x_seats_needed, x_tour_end_date, x_tour_start_date, x_vehicle_id

WARN_VEHICLE_CONFLICT = '''\
for record in records:
    if not record.x_is_fleet_task or not record.x_vehicle_id:
        record.write({"x_available_seats": 0})
        continue
    if not record.x_tour_start_date or not record.x_tour_end_date:
        record.write({"x_available_seats": 0})
        continue

    # Only check this task if its SO is confirmed (sale)
    my_so = record.sale_order_id
    if my_so and my_so.state != "sale":
        record.write({"x_available_seats": 0})
        continue

    # Block if vehicle has a fleet service "En proceso" (running = in the shop)
    services_in_progress = env["fleet.vehicle.log.services"].search([
        ("vehicle_id", "=", record.x_vehicle_id.id),
        ("state", "=", "running"),
    ])
    if services_in_progress:
        nl = chr(10)
        vehicle_name = record.x_vehicle_id.display_name
        svc_details = []
        for svc in services_in_progress:
            svc_desc = svc.description or "Sin descripcion"
            svc_date = str(svc.date) if svc.date else "Sin fecha"
            svc_details.append("- " + svc_desc + " (" + svc_date + ")")
        msg = "BLOQUEADO: El vehiculo " + vehicle_name + " esta en servicio/taller:" + nl
        msg += nl.join(svc_details) + nl + nl
        msg += "Complete o cancele el servicio antes de asignar el vehiculo a un tour."
        raise UserError(msg)

    # Only count conflicts from confirmed SOs
    conflicts = env["project.task"].search([
        ("id", "!=", record.id),
        ("x_vehicle_id", "=", record.x_vehicle_id.id),
        ("x_is_fleet_task", "=", True),
        ("x_tour_start_date", "!=", False),
        ("x_tour_end_date", "!=", False),
        ("x_tour_start_date", "<=", record.x_tour_end_date),
        ("x_tour_end_date", ">=", record.x_tour_start_date),
        ("sale_order_id.state", "=", "sale"),
    ])

    vehicle_capacity = record.x_vehicle_id.seats or 0
    other_seats = sum(c.x_seats_needed or 0 for c in conflicts)
    my_type = my_so.x_service_type if my_so else False
    is_private = my_type == "private"

    # Check if any conflict is private
    conflict_private = False
    for c in conflicts:
        if c.sale_order_id and c.sale_order_id.x_service_type == "private":
            conflict_private = True

    # Private tour: available = 0 if any conflict exists
    if is_private and conflicts:
        record.write({"x_available_seats": 0})
    elif conflict_private:
        record.write({"x_available_seats": 0})
    else:
        record.write({"x_available_seats": vehicle_capacity - other_seats - (record.x_seats_needed or 0)})

    if conflicts:
        vehicle_name = record.x_vehicle_id.display_name
        conflict_details = []
        total_seats = other_seats + (record.x_seats_needed or 0)
        for c in conflicts:
            so_name = c.sale_order_id.name if c.sale_order_id else "Sin SO"
            c_type = c.sale_order_id.x_service_type if c.sale_order_id else ""
            tipo = " [PRIVADO]" if c_type == "private" else ""
            detail = "- " + so_name + tipo + ": " + str(c.x_tour_start_date) + " a " + str(c.x_tour_end_date) + " (" + str(c.x_seats_needed or 0) + " asientos)"
            conflict_details.append(detail)

        nl = chr(10)

        # Block if this tour is private and vehicle has any other booking
        if is_private:
            msg = "BLOQUEADO: Este tour es PRIVADO y el vehiculo " + vehicle_name + " ya tiene otros tours en estas fechas:" + nl
            msg += nl.join(conflict_details)
            raise UserError(msg + nl + nl + "Un vehiculo en servicio PRIVADO no puede compartirse.")

        # Block if a conflicting tour is private
        if conflict_private:
            msg = "BLOQUEADO: El vehiculo " + vehicle_name + " esta reservado para un tour PRIVADO en estas fechas:" + nl
            msg += nl.join(conflict_details)
            raise UserError(msg + nl + nl + "No se puede asignar un vehiculo reservado en servicio PRIVADO.")

        # Shared: check capacity
        msg = "ADVERTENCIA: El vehiculo " + vehicle_name + " tiene tours superpuestos en estas fechas:" + nl
        msg += nl.join(conflict_details)
        msg += nl + nl + "Capacidad total: " + str(vehicle_capacity) + " asientos"
        msg += nl + "Asientos totales solicitados: " + str(total_seats)

        if vehicle_capacity > 0 and total_seats > vehicle_capacity:
            raise UserError(msg + nl + nl + "EXCEDE la capacidad del vehiculo. No se puede asignar.")
        else:
            record.message_post(body=msg, message_type="comment", subtype_xmlid="mail.mt_note")
'''

# ── Automation 18: Sync Tour Data Changes to Tasks ────────────────────────
# Model: sale.order | Trigger: on_write | Fields: x_service_type, x_num_passengers, x_departure_city, x_tour_start_date, x_tour_end_date

SYNC_TOUR_DATA_CHANGES = '''\
for record in records:
    if not record.x_is_tour or record.state != "sale":
        continue
    tasks = env["project.task"].search([("sale_order_id", "=", record.id)])
    if not tasks:
        continue
    vals = {}
    if record.x_tour_start_date:
        vals["x_tour_start_date"] = record.x_tour_start_date
    else:
        vals["x_tour_start_date"] = False
    if record.x_tour_end_date:
        vals["x_tour_end_date"] = record.x_tour_end_date
    else:
        vals["x_tour_end_date"] = False
    vals["x_seats_needed"] = record.x_num_passengers or 0
    tasks.write(vals)

    # Check private tour conflicts (only against confirmed SOs)
    if record.x_service_type == "private":
        fleet_tasks = tasks.filtered(lambda t: t.x_is_fleet_task and t.x_vehicle_id)
        for ft in fleet_tasks:
            if not ft.x_tour_start_date or not ft.x_tour_end_date:
                continue
            conflicts = env["project.task"].search([
                ("id", "!=", ft.id),
                ("x_vehicle_id", "=", ft.x_vehicle_id.id),
                ("x_is_fleet_task", "=", True),
                ("x_tour_start_date", "!=", False),
                ("x_tour_end_date", "!=", False),
                ("x_tour_start_date", "<=", ft.x_tour_end_date),
                ("x_tour_end_date", ">=", ft.x_tour_start_date),
                ("sale_order_id.state", "=", "sale"),
            ])
            if conflicts:
                nl = chr(10)
                details = []
                for c in conflicts:
                    so_name = c.sale_order_id.name if c.sale_order_id else "Sin SO"
                    details.append("- " + so_name + ": " + str(c.x_tour_start_date) + " a " + str(c.x_tour_end_date))
                msg = "ATENCION: Este tour cambio a PRIVADO pero el vehiculo " + ft.x_vehicle_id.display_name + " tiene otros tours asignados en las mismas fechas:" + nl
                msg += nl.join(details) + nl + nl
                msg += "Revise las asignaciones de vehiculo en las tareas del proyecto."
                record.message_post(body=msg, message_type="comment", subtype_xmlid="mail.mt_note")
'''

# ── Helper: format hours (inlined in each automation) ────────────────────
# _fmt(h) -> "Xh YYmin"  (e.g. 1.75 -> "1h 45min")
# Cannot define functions in safe_eval, so this pattern is repeated.

# ── Automation 20: Work Log → Task Chatter + Recalc ─────────────────────
# Model: x_task_work_log | Trigger: on_create

WORK_LOG_TO_CHATTER = '''nl = chr(10)
for record in records:
    task = record.x_task_id
    if not task:
        continue
    pname = record.x_partner_id.name if record.x_partner_id else "Sin asignar"
    stype = dict(record._fields["x_service_type"].selection).get(record.x_service_type, "") if record.x_service_type else ""
    h = record.x_hours_spent or 0
    t_str = str(int(h)) + "h " + str(int((h - int(h)) * 60)).zfill(2) + "min" if h > 0 else ""
    d_str = str(record.x_date) if record.x_date else ""
    desc = record.x_description or ""
    parts = [pname]
    if stype:
        parts.append("(" + stype + ")")
    if d_str:
        parts.append("| " + d_str)
    if t_str:
        parts.append("| " + t_str)
    entry = " ".join(parts)
    # Recalculate
    total = sum(wl.x_hours_spent or 0 for wl in task.x_work_log_ids)
    remaining = (task.allocated_hours or 0) - total
    task.write({"x_total_hours_logged": total, "x_remaining_hours": remaining})
    tt = str(int(total)) + "h " + str(int((total - int(total)) * 60)).zfill(2) + "min"
    ra = abs(remaining)
    rt = ("-" if remaining < 0 else "") + str(int(ra)) + "h " + str(int((ra - int(ra)) * 60)).zfill(2) + "min"
    body = "Nuevo registro: " + entry
    if desc:
        body += nl + desc
    body += nl + "Totales: " + tt + " registradas | " + rt + " restantes"
    task.message_post(body=body, message_type="comment", subtype_xmlid="mail.mt_note")
'''

# ── Automation 21: Work Log Edit → Chatter + Recalc ─────────────────────
# Model: x_task_work_log | Trigger: on_write | Fields: x_hours_spent, x_partner_id, x_service_type, x_description

RECALC_HOURS_ON_WRITE = '''nl = chr(10)
for record in records:
    task = record.x_task_id
    if not task:
        continue
    pname = record.x_partner_id.name if record.x_partner_id else "Sin asignar"
    stype = dict(record._fields["x_service_type"].selection).get(record.x_service_type, "") if record.x_service_type else ""
    h = record.x_hours_spent or 0
    t_str = str(int(h)) + "h " + str(int((h - int(h)) * 60)).zfill(2) + "min" if h > 0 else ""
    d_str = str(record.x_date) if record.x_date else ""
    parts = [pname]
    if stype:
        parts.append("(" + stype + ")")
    if d_str:
        parts.append("| " + d_str)
    if t_str:
        parts.append("| " + t_str)
    entry = " ".join(parts)
    # Recalculate
    total = sum(wl.x_hours_spent or 0 for wl in task.x_work_log_ids)
    remaining = (task.allocated_hours or 0) - total
    task.write({"x_total_hours_logged": total, "x_remaining_hours": remaining})
    tt = str(int(total)) + "h " + str(int((total - int(total)) * 60)).zfill(2) + "min"
    ra = abs(remaining)
    rt = ("-" if remaining < 0 else "") + str(int(ra)) + "h " + str(int((ra - int(ra)) * 60)).zfill(2) + "min"
    body = "Registro editado: " + entry + nl + "Totales: " + tt + " registradas | " + rt + " restantes"
    task.message_post(body=body, message_type="comment", subtype_xmlid="mail.mt_note")
'''

# ── Automation 22: Work Log Delete → Chatter + Recalc ───────────────────
# Model: x_task_work_log | Trigger: on_unlink

RECALC_HOURS_ON_UNLINK = '''nl = chr(10)
for record in records:
    task = record.x_task_id
    if not task:
        continue
    pname = record.x_partner_id.name if record.x_partner_id else "Sin asignar"
    stype = dict(record._fields["x_service_type"].selection).get(record.x_service_type, "") if record.x_service_type else ""
    h = record.x_hours_spent or 0
    t_str = str(int(h)) + "h " + str(int((h - int(h)) * 60)).zfill(2) + "min" if h > 0 else ""
    d_str = str(record.x_date) if record.x_date else ""
    parts = [pname]
    if stype:
        parts.append("(" + stype + ")")
    if d_str:
        parts.append("| " + d_str)
    if t_str:
        parts.append("| " + t_str)
    entry = " ".join(parts)
    # Recalculate excluding deleted record
    total = sum(wl.x_hours_spent or 0 for wl in task.x_work_log_ids if wl.id != record.id)
    remaining = (task.allocated_hours or 0) - total
    task.write({"x_total_hours_logged": total, "x_remaining_hours": remaining})
    tt = str(int(total)) + "h " + str(int((total - int(total)) * 60)).zfill(2) + "min"
    ra = abs(remaining)
    rt = ("-" if remaining < 0 else "") + str(int(ra)) + "h " + str(int((ra - int(ra)) * 60)).zfill(2) + "min"
    body = "Registro eliminado: " + entry + nl + "Totales: " + tt + " registradas | " + rt + " restantes"
    task.message_post(body=body, message_type="comment", subtype_xmlid="mail.mt_note")
'''

# ── Automation 23: Allocated Hours Change → Chatter + Recalc ────────────
# Model: project.task | Trigger: on_write | Fields: allocated_hours

RECALC_ON_ALLOCATED_CHANGE = '''nl = chr(10)
for record in records:
    total = record.x_total_hours_logged or 0
    alloc = record.allocated_hours or 0
    remaining = alloc - total
    record.write({"x_remaining_hours": remaining})
    ah = str(int(alloc)) + "h " + str(int((alloc - int(alloc)) * 60)).zfill(2) + "min"
    tt = str(int(total)) + "h " + str(int((total - int(total)) * 60)).zfill(2) + "min"
    ra = abs(remaining)
    rt = ("-" if remaining < 0 else "") + str(int(ra)) + "h " + str(int((ra - int(ra)) * 60)).zfill(2) + "min"
    body = "Horas asignadas actualizadas: " + ah + nl + "Totales: " + tt + " registradas | " + rt + " restantes"
    record.message_post(body=body, message_type="comment", subtype_xmlid="mail.mt_note")
'''

# ── Automation 24: Warn Tour on Fleet Service State Change ───────────────
# Model: fleet.vehicle.log.services | Trigger: on_create + on_write (state)
# When a service enters "running" (En proceso), check if the vehicle has
# active tour assignments and warn via chatter (does NOT block — emergency
# repairs may be needed).

WARN_TOUR_ON_SERVICE_STATE = '''\
for record in records:
    if record.state != "running":
        continue
    if not record.vehicle_id:
        continue
    nl = chr(10)
    today = datetime.date.today()
    active_tours = env["project.task"].search([
        ("x_vehicle_id", "=", record.vehicle_id.id),
        ("x_is_fleet_task", "=", True),
        ("x_tour_start_date", "!=", False),
        ("x_tour_end_date", "!=", False),
        ("x_tour_end_date", ">=", today),
        ("sale_order_id.state", "=", "sale"),
    ])
    if active_tours:
        vehicle_name = record.vehicle_id.display_name
        tour_details = []
        for t in active_tours:
            so_name = t.sale_order_id.name if t.sale_order_id else "Sin SO"
            tour_details.append("- " + so_name + ": " + str(t.x_tour_start_date) + " a " + str(t.x_tour_end_date) + " (" + str(t.x_seats_needed or 0) + " asientos)")
        msg = "ATENCION: El vehiculo " + vehicle_name + " tiene tours activos asignados:" + nl
        msg += nl.join(tour_details) + nl + nl
        msg += "Revise las asignaciones de vehiculo en las tareas de los proyectos afectados."
        record.message_post(body=msg, message_type="comment", subtype_xmlid="mail.mt_note")
'''

# ── Server Action: Create POs from Biblia Operativa Operators ────────────
# Model: sale.order | Triggered by button in Biblia Operativa tab

CREATE_POS_FROM_OPERATORS = '''\
for record in records:
    if not record.x_is_tour:
        continue
    ops_by_partner = {}
    for op in record.x_operator_line_ids:
        if not op.x_partner_id or op.x_purchase_order_id:
            continue
        pid = op.x_partner_id.id
        if pid not in ops_by_partner:
            ops_by_partner[pid] = []
        ops_by_partner[pid].append(op)

    if not ops_by_partner:
        raise UserError("No hay operadores sin pedido de compra para generar.")

    product = env["product.product"].search([("default_code", "=", "SRV-TOUR")], limit=1)
    if not product:
        product = env["product.product"].search([("name", "=", "Servicio de Tour"), ("type", "=", "service")], limit=1)
    if not product:
        raise UserError("Producto 'Servicio de Tour' no encontrado. Ejecute setup_custom_fields.py primero.")

    created_pos = []
    stype_labels = {}
    if record.x_operator_line_ids:
        stype_labels = dict(record.x_operator_line_ids[0]._fields["x_service_type"].selection)

    for partner_id, ops in ops_by_partner.items():
        po = env["purchase.order"].create({
            "partner_id": partner_id,
            "origin": record.name,
        })
        for op in ops:
            stype_label = stype_labels.get(op.x_service_type, op.x_service_type or "")
            desc = stype_label + " - " + record.name
            if op.x_name:
                desc = op.x_name + " (" + stype_label + ") - " + record.name
            env["purchase.order.line"].create({
                "order_id": po.id,
                "product_id": product.id,
                "name": desc,
                "product_qty": 1,
                "price_unit": op.x_cost or 0,
                "sale_order_id": record.id,
            })
            op.write({"x_purchase_order_id": po.id})
        created_pos.append(po.name)

    msg = "Pedidos de compra generados: " + ", ".join(created_pos)
    record.message_post(body=msg, message_type="comment", subtype_xmlid="mail.mt_note")
'''
