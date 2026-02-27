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
# Updated: adds analytic_distribution from project, PO currency from operators,
# and saves x_po_line_id on each operator for bidirectional PO↔Biblia sync.

CREATE_POS_FROM_OPERATORS = '''\
for record in records:
    if not record.x_is_tour:
        continue
    # Look up analytic account from linked project
    project = env["project.project"].search([("sale_order_id", "=", record.id)], limit=1)
    analytic_dist = {}
    if project and project.account_id:
        analytic_dist = {str(project.account_id.id): 100}

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

    # Get first SO line for sale_line_id link (needed for SO↔PO smart button)
    first_sol = record.order_line[:1] if record.order_line else False

    for partner_id, ops in ops_by_partner.items():
        po_vals = {"partner_id": partner_id, "origin": record.name}
        # Use currency from first operator of this group
        op_currency = ops[0].x_cost_currency_id
        if op_currency:
            po_vals["currency_id"] = op_currency.id
        po = env["purchase.order"].create(po_vals)
        for op in ops:
            stype_label = stype_labels.get(op.x_service_type, op.x_service_type or "")
            desc = stype_label + " - " + record.name
            if op.x_description:
                desc = stype_label + ": " + op.x_description + " - " + record.name
            if op.x_name:
                desc = op.x_name + " (" + stype_label + ")"
                if op.x_description:
                    desc = desc + " " + op.x_description
                desc = desc + " - " + record.name
            pol_vals = {
                "order_id": po.id,
                "product_id": product.id,
                "name": desc,
                "product_qty": 1,
                "price_unit": op.x_cost or 0,
                "analytic_distribution": analytic_dist,
            }
            if first_sol:
                pol_vals["sale_line_id"] = first_sol.id
            pol = env["purchase.order.line"].create(pol_vals)
            op.write({"x_purchase_order_id": po.id, "x_po_line_id": pol.id})
        created_pos.append(po.name)

    msg = "Pedidos de compra generados: " + ", ".join(created_pos)
    if analytic_dist:
        msg = msg + " (con distribucion analitica del proyecto)"
    record.message_post(body=msg, message_type="comment", subtype_xmlid="mail.mt_note")
'''

# ── Automations 26-27: Recalc Tour Financials (on_create / on_write) ─────
# Model: x_operator_line | Trigger: on_create (26), on_write (27)
# Trigger fields for 27: x_cost, x_cost_currency_id
# Calculates x_cost_pen for the record and recalculates SO financial summary.
# Uses so.currency_rate for same-currency conversion, _convert() for rare cases.

RECALC_TOUR_FINANCIALS = '''\
for record in records:
    so = record.x_sale_order_id
    if not so:
        continue
    company_currency = so.company_id.currency_id
    today = datetime.date.today()
    # 1. Calculate x_cost_pen for this record
    if record.x_cost:
        op_cur = record.x_cost_currency_id or so.currency_id
        if op_cur == company_currency:
            pen_val = record.x_cost
        elif op_cur == so.currency_id and so.currency_rate:
            pen_val = record.x_cost / so.currency_rate
        else:
            pen_val = op_cur._convert(record.x_cost, company_currency, so.company_id, record.x_date or today)
        record.write({"x_cost_pen": pen_val})
    else:
        record.write({"x_cost_pen": 0.0})
    # 2. Recalculate SO totals
    if not so.x_is_tour:
        continue
    total_cost = 0.0
    for op in so.x_operator_line_ids:
        if not op.x_cost:
            continue
        op_cur = op.x_cost_currency_id or so.currency_id
        if op_cur == company_currency:
            total_cost += op.x_cost
        elif op_cur == so.currency_id and so.currency_rate:
            total_cost += op.x_cost / so.currency_rate
        else:
            total_cost += op_cur._convert(op.x_cost, company_currency, so.company_id, op.x_date or today)
    if so.currency_id == company_currency:
        so_total_pen = so.amount_untaxed
    elif so.currency_rate:
        so_total_pen = so.amount_untaxed / so.currency_rate
    else:
        so_total_pen = 0.0
    margin = so_total_pen - total_cost
    margin_pct = (margin / so_total_pen) if so_total_pen else 0.0
    # SO-currency equivalents (for display when SO is in USD)
    if so.currency_id == company_currency:
        cost_cur = total_cost
        margin_cur = margin
    elif so.currency_rate:
        cost_cur = total_cost * so.currency_rate
        margin_cur = so.amount_untaxed - cost_cur
    else:
        cost_cur = 0.0
        margin_cur = 0.0
    so.write({
        "x_total_estimated_cost": total_cost,
        "x_estimated_margin": margin,
        "x_estimated_margin_percent": margin_pct,
        "x_total_estimated_cost_cur": cost_cur,
        "x_estimated_margin_cur": margin_cur,
    })
'''

# ── Automation 28: Recalc Tour Financials (on_unlink) ────────────────────
# Model: x_operator_line | Trigger: on_unlink
# Same as 26-27 but excludes the deleted record from totals and skips x_cost_pen.

RECALC_TOUR_FINANCIALS_UNLINK = '''\
for record in records:
    so = record.x_sale_order_id
    if not so or not so.x_is_tour:
        continue
    company_currency = so.company_id.currency_id
    today = datetime.date.today()
    total_cost = 0.0
    for op in so.x_operator_line_ids:
        if op.id == record.id:
            continue
        if not op.x_cost:
            continue
        op_cur = op.x_cost_currency_id or so.currency_id
        if op_cur == company_currency:
            total_cost += op.x_cost
        elif op_cur == so.currency_id and so.currency_rate:
            total_cost += op.x_cost / so.currency_rate
        else:
            total_cost += op_cur._convert(op.x_cost, company_currency, so.company_id, op.x_date or today)
    if so.currency_id == company_currency:
        so_total_pen = so.amount_untaxed
    elif so.currency_rate:
        so_total_pen = so.amount_untaxed / so.currency_rate
    else:
        so_total_pen = 0.0
    margin = so_total_pen - total_cost
    margin_pct = (margin / so_total_pen) if so_total_pen else 0.0
    if so.currency_id == company_currency:
        cost_cur = total_cost
        margin_cur = margin
    elif so.currency_rate:
        cost_cur = total_cost * so.currency_rate
        margin_cur = so.amount_untaxed - cost_cur
    else:
        cost_cur = 0.0
        margin_cur = 0.0
    so.write({
        "x_total_estimated_cost": total_cost,
        "x_estimated_margin": margin,
        "x_estimated_margin_percent": margin_pct,
        "x_total_estimated_cost_cur": cost_cur,
        "x_estimated_margin_cur": margin_cur,
    })
'''

# ── Server Action: Create Budget from Biblia Operativa ───────────────────
# Model: sale.order | Triggered by button in Biblia Operativa tab
# Creates/updates a budget.analytic with expense lines from operator costs.
# Idempotent: updates existing budget if one with matching name exists.

CREATE_BUDGET_FROM_BIBLIA = '''\
for record in records:
    if not record.x_is_tour:
        raise UserError("Esta accion solo aplica a cotizaciones de tour.")
    project = env["project.project"].search([("sale_order_id", "=", record.id)], limit=1)
    if not project or not project.account_id:
        raise UserError("No se encontro proyecto con cuenta analitica para esta venta. Confirme la orden primero.")
    company_currency = record.company_id.currency_id
    today = datetime.date.today()
    # Group costs by currency
    costs_by_currency = {}
    for op in record.x_operator_line_ids:
        if not op.x_cost:
            continue
        op_cur = op.x_cost_currency_id or record.currency_id
        cur_id = op_cur.id
        if cur_id not in costs_by_currency:
            costs_by_currency[cur_id] = {"currency": op_cur, "original": 0.0, "pen": 0.0}
        costs_by_currency[cur_id]["original"] += op.x_cost
        if op_cur == company_currency:
            costs_by_currency[cur_id]["pen"] += op.x_cost
        elif op_cur == record.currency_id and record.currency_rate:
            costs_by_currency[cur_id]["pen"] += op.x_cost / record.currency_rate
        else:
            costs_by_currency[cur_id]["pen"] += op_cur._convert(op.x_cost, company_currency, record.company_id, op.x_date or today)
    total_cost_pen = sum(g["pen"] for g in costs_by_currency.values())
    budget_name = "Presupuesto Tour " + record.name
    date_from = record.x_tour_start_date or today
    date_to = record.x_tour_end_date or today
    # Search existing budget
    existing = env["budget.analytic"].search([("name", "=", budget_name)], limit=1)
    if existing:
        if existing.state != "draft":
            existing.action_budget_draft()
        existing.budget_line_ids.unlink()
        for cur_id, grp in costs_by_currency.items():
            env["budget.line"].create({
                "budget_analytic_id": existing.id,
                "account_id": project.account_id.id,
                "budget_amount": grp["pen"],
                "x_original_currency_id": cur_id,
                "x_original_amount": grp["original"],
                "date_from": date_from,
                "date_to": date_to,
            })
        existing.write({"date_from": date_from, "date_to": date_to, "x_sale_order_id": record.id})
        record.write({"x_budget_id": existing.id})
        msg = "Presupuesto actualizado: " + budget_name + " por S/ " + str(round(total_cost_pen, 2))
    else:
        budget = env["budget.analytic"].create({
            "name": budget_name,
            "date_from": date_from,
            "date_to": date_to,
            "budget_type": "expense",
            "x_sale_order_id": record.id,
        })
        for cur_id, grp in costs_by_currency.items():
            env["budget.line"].create({
                "budget_analytic_id": budget.id,
                "account_id": project.account_id.id,
                "budget_amount": grp["pen"],
                "x_original_currency_id": cur_id,
                "x_original_amount": grp["original"],
                "date_from": date_from,
                "date_to": date_to,
            })
        record.write({"x_budget_id": budget.id})
        msg = "Presupuesto creado: " + budget_name + " por S/ " + str(round(total_cost_pen, 2))
    record.message_post(body=msg, message_type="comment", subtype_xmlid="mail.mt_note")
'''

# ── Automation 29: Autofill from Product ─────────────────────────────────
# Model: x_operator_line | Trigger: on_write | Fields: x_product_id
# When a service product is selected, auto-fills x_cost and x_description
# if they are empty (does not overwrite existing values).

# ── Server Action: View Tour Budget ───────────────────────────────────────
# Model: sale.order | Triggered by stat button
# Returns an action to open the linked budget.analytic record in form view.

VIEW_TOUR_BUDGET = '''\
for record in records:
    if record.x_budget_id:
        action = {
            "type": "ir.actions.act_window",
            "res_model": "budget.analytic",
            "res_id": record.x_budget_id.id,
            "view_mode": "form",
            "views": [[False, "form"]],
        }
'''

AUTOFILL_FROM_PRODUCT = '''\
for record in records:
    if not record.x_product_id:
        continue
    prod = record.x_product_id
    vals = {}
    if prod.standard_price and not record.x_cost:
        vals["x_cost"] = prod.standard_price
    if prod.name and not record.x_description:
        vals["x_description"] = prod.name
    if vals:
        record.write(vals)
'''

# ── Server Action: Append Template to SO ──────────────────────────────
# Model: sale.order | Triggered by button in Biblia Operativa tab
# Adds lines from a second template without removing existing ones.

APPEND_TEMPLATE_TO_SO = '''\
for record in records:
    tmpl = record.x_append_template_id
    if not tmpl:
        raise UserError("Seleccione una plantilla de tour para agregar.")
    if not tmpl.x_is_tour:
        raise UserError("La plantilla seleccionada no es un tour.")

    # 1. Section header + product lines
    max_seq = 0
    for l in record.order_line:
        if (l.sequence or 0) > max_seq:
            max_seq = l.sequence or 0
    max_seq += 1
    env["sale.order.line"].create({
        "order_id": record.id,
        "display_type": "line_section",
        "name": tmpl.name or "Tour adicional",
        "sequence": max_seq,
    })
    for tline in tmpl.sale_order_template_line_ids:
        if not tline.product_id:
            continue
        max_seq += 1
        env["sale.order.line"].create({
            "order_id": record.id,
            "product_id": tline.product_id.id,
            "product_uom_qty": tline.product_uom_qty or 1,
            "sequence": max_seq,
        })

    # 2. Itinerary lines (offset day_number + sequence)
    max_day = 0
    max_itin_seq = 0
    for itin in record.x_itinerary_line_ids:
        if (itin.x_day_number or 0) > max_day:
            max_day = itin.x_day_number or 0
        if (itin.x_sequence or 0) > max_itin_seq:
            max_itin_seq = itin.x_sequence or 0
    for line in tmpl.x_itinerary_line_ids:
        env["x_itinerary_line"].create({
            "x_sale_order_id": record.id,
            "x_sequence": (line.x_sequence or 0) + max_itin_seq,
            "x_day_number": (line.x_day_number or 0) + max_day,
            "x_title": line.x_title or False,
            "x_name": line.x_name or False,
            "x_description": line.x_description or False,
            "x_accommodation": line.x_accommodation or False,
            "x_meals": line.x_meals or False,
        })

    # 3. Operator lines (offset sequence)
    max_op_seq = 0
    for op in record.x_operator_line_ids:
        if (op.x_sequence or 0) > max_op_seq:
            max_op_seq = op.x_sequence or 0
    for op in tmpl.x_operator_line_ids:
        env["x_operator_line"].create({
            "x_sale_order_id": record.id,
            "x_sequence": (op.x_sequence or 0) + max_op_seq,
            "x_partner_id": op.x_partner_id.id if op.x_partner_id else False,
            "x_service_type": op.x_service_type or False,
            "x_name": op.x_name or False,
            "x_description": op.x_description or False,
            "x_date": op.x_date or False,
            "x_product_id": op.x_product_id.id if op.x_product_id else False,
            "x_cost_currency_id": op.x_cost_currency_id.id if op.x_cost_currency_id else False,
            "x_cost": op.x_cost or 0,
        })

    # 4. Concatenate text fields
    sep = chr(10) + "---" + chr(10)
    if tmpl.x_inclusions:
        current = record.x_inclusions or ""
        new_val = current + sep + tmpl.x_inclusions if current else tmpl.x_inclusions
        record.write({"x_inclusions": new_val})
    if tmpl.x_key_times:
        current = record.x_key_times or ""
        new_val = current + sep + tmpl.x_key_times if current else tmpl.x_key_times
        record.write({"x_key_times": new_val})
    if tmpl.x_special_observations:
        current = record.x_special_observations or ""
        new_val = current + sep + tmpl.x_special_observations if current else tmpl.x_special_observations
        record.write({"x_special_observations": new_val})

    # 5. Clear field + notify
    record.write({"x_append_template_id": False})
    record.message_post(
        body="Plantilla agregada: " + (tmpl.name or ""),
        message_type="comment",
        subtype_xmlid="mail.mt_note"
    )
'''
