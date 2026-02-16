"""Query Odoo for configuration data within a date range."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from typing import Any

from odoo_cli import OdooClient


def connect() -> OdooClient:
    """Create and authenticate an OdooClient."""
    client = OdooClient()
    client.connect()
    return client


# ---------------------------------------------------------------------------
# Date-range queries (records created during a sprint/period)
# ---------------------------------------------------------------------------

# Each entry: (dict_key, odoo_model, fields_list)
DATE_RANGE_MODELS: list[tuple[str, str, list[str]]] = [
    # ── Products & Inventory ──────────────────────────────────────────
    ("products", "product.template", [
        "name", "list_price", "type", "categ_id", "create_date",
    ]),
    ("product_variants", "product.product", [
        "name", "product_tmpl_id", "create_date",
    ]),
    ("categories", "product.category", [
        "name", "parent_id", "create_date",
    ]),
    ("attributes", "product.attribute", [
        "name", "create_variant", "create_date",
    ]),
    ("attribute_values", "product.attribute.value", [
        "name", "attribute_id", "create_date",
    ]),
    ("product_tags", "product.tag", [
        "name", "create_date",
    ]),
    ("pricelists", "product.pricelist", [
        "name", "currency_id", "create_date",
    ]),
    ("pricelist_items", "product.pricelist.item", [
        "pricelist_id", "applied_on", "compute_price", "create_date",
    ]),
    ("uom", "uom.uom", [
        "name", "category_id", "create_date",
    ]),

    # ── Sales ─────────────────────────────────────────────────────────
    ("quotations", "sale.order", [
        "name", "partner_id", "state", "amount_total", "create_date",
    ]),
    ("quotation_templates", "sale.order.template", [
        "name", "create_date",
    ]),

    # ── CRM ───────────────────────────────────────────────────────────
    ("crm_leads", "crm.lead", [
        "name", "stage_id", "partner_id", "create_date",
    ]),
    ("crm_stages", "crm.stage", [
        "name", "create_date",
    ]),

    # ── Purchase ──────────────────────────────────────────────────────
    ("purchase_orders", "purchase.order", [
        "name", "partner_id", "state", "amount_total", "create_date",
    ]),

    # ── Stock / Inventory ─────────────────────────────────────────────
    ("warehouses", "stock.warehouse", [
        "name", "code", "create_date",
    ]),
    ("stock_locations", "stock.location", [
        "name", "usage", "create_date",
    ]),
    ("picking_types", "stock.picking.type", [
        "name", "code", "warehouse_id", "create_date",
    ]),

    # ── Manufacturing / Kits ──────────────────────────────────────────
    ("bom", "mrp.bom", [
        "product_tmpl_id", "type", "product_qty", "create_date",
    ]),
    ("bom_lines", "mrp.bom.line", [
        "product_id", "product_qty", "bom_id", "create_date",
    ]),
    ("workcenters", "mrp.workcenter", [
        "name", "create_date",
    ]),

    # ── Accounting & Invoicing ────────────────────────────────────────
    ("invoices", "account.move", [
        "name", "partner_id", "move_type", "state", "amount_total", "create_date",
    ]),
    ("journals", "account.journal", [
        "name", "type", "code", "create_date",
    ]),
    ("taxes", "account.tax", [
        "name", "amount", "type_tax_use", "create_date",
    ]),
    ("payment_terms", "account.payment.term", [
        "name", "create_date",
    ]),
    ("fiscal_positions", "account.fiscal.position", [
        "name", "create_date",
    ]),
    ("analytic_plans", "account.analytic.plan", [
        "name", "create_date",
    ]),
    ("analytic_accounts", "account.analytic.account", [
        "name", "plan_id", "create_date",
    ]),
    ("currencies", "res.currency", [
        "name", "symbol", "active", "create_date",
    ]),

    # ── Projects & Planning ───────────────────────────────────────────
    ("projects", "project.project", [
        "name", "is_template", "create_date",
    ]),
    ("tasks", "project.task", [
        "name", "project_id", "stage_id", "create_date",
    ]),
    ("planning_slots", "planning.slot", [
        "display_name", "resource_id", "start_datetime", "end_datetime", "create_date",
    ]),

    # ── HR ────────────────────────────────────────────────────────────
    ("employees", "hr.employee", [
        "name", "department_id", "job_id", "work_email", "create_date",
    ]),
    ("departments", "hr.department", [
        "name", "parent_id", "manager_id", "create_date",
    ]),
    ("job_positions", "hr.job", [
        "name", "department_id", "create_date",
    ]),
    ("contracts", "hr.contract", [
        "name", "employee_id", "state", "wage", "create_date",
    ]),
    ("leave_types", "hr.leave.type", [
        "name", "create_date",
    ]),
    ("work_locations", "hr.work.location", [
        "name", "create_date",
    ]),
    ("expenses", "hr.expense", [
        "name", "total_amount", "state", "create_date",
    ]),

    # ── Resources & Scheduling ────────────────────────────────────────
    ("resources", "resource.resource", [
        "name", "resource_type", "create_date",
    ]),
    ("work_schedules", "resource.calendar", [
        "name", "tz", "create_date",
    ]),

    # ── POS & Restaurant ──────────────────────────────────────────────
    ("pos_categories", "pos.category", [
        "name", "parent_id", "create_date",
    ]),
    ("pos_configs", "pos.config", [
        "name", "create_date",
    ]),
    ("restaurant_floors", "restaurant.floor", [
        "name", "pos_config_ids", "create_date",
    ]),

    # ── Events ────────────────────────────────────────────────────────
    ("events", "event.event", [
        "name", "date_begin", "date_end", "create_date",
    ]),

    # ── Fleet ─────────────────────────────────────────────────────────
    ("vehicles", "fleet.vehicle", [
        "name", "model_id", "create_date",
    ]),

    # ── Partners ──────────────────────────────────────────────────────
    ("partners", "res.partner", [
        "name", "email", "is_company", "create_date",
    ]),

    # ── Email & Automation ────────────────────────────────────────────
    ("email_templates", "mail.template", [
        "name", "model_id", "create_date",
    ]),
    ("sequences", "ir.sequence", [
        "name", "code", "prefix", "create_date",
    ]),
]


def query_date_range(
    client: OdooClient,
    start_date: str,
    end_date: str,
) -> dict[str, list[dict[str, Any]]]:
    """Query all relevant Odoo models for records created in [start_date, end_date).

    Silently skips models that don't exist or raise errors (e.g. uninstalled apps).

    Args:
        client: Authenticated OdooClient.
        start_date: ISO date string "YYYY-MM-DD".
        end_date: ISO date string "YYYY-MM-DD".

    Returns:
        Dict keyed by model alias. Each value is a list of record dicts.
        Only includes keys for models that returned results.
    """
    domain = [["create_date", ">=", start_date], ["create_date", "<", end_date]]
    data: dict[str, list[dict[str, Any]]] = {}

    for key, model, fields in DATE_RANGE_MODELS:
        try:
            records = client.search_read(
                model,
                domain=domain,
                fields=fields,
                order="create_date asc",
            )
            if records:
                data[key] = records
        except Exception:
            # Model not installed or inaccessible — skip silently
            pass

    return data


# ---------------------------------------------------------------------------
# System-wide queries (not date-filtered)
# ---------------------------------------------------------------------------


def query_installed_modules(client: OdooClient) -> list[dict[str, Any]]:
    """Get all installed Odoo modules."""
    return client.search_read(
        "ir.module.module",
        domain=[["state", "=", "installed"]],
        fields=["name", "shortdesc", "state"],
        order="name asc",
    )


def query_pos_configs(client: OdooClient) -> list[dict[str, Any]]:
    """Get all POS configurations."""
    try:
        return client.search_read(
            "pos.config",
            fields=["name", "module_pos_restaurant", "create_date"],
            order="name asc",
        )
    except Exception:
        return []


def query_websites(client: OdooClient) -> list[dict[str, Any]]:
    """Get website configurations."""
    try:
        return client.search_read(
            "website",
            fields=["name", "domain", "create_date"],
        )
    except Exception:
        return []


def query_company(client: OdooClient) -> list[dict[str, Any]]:
    """Get company information."""
    return client.search_read(
        "res.company",
        fields=["name", "currency_id", "country_id"],
    )


def query_config_parameters(client: OdooClient) -> list[dict[str, Any]]:
    """Get system configuration parameters (ir.config_parameter).

    Filters out internal/secret keys (database.*, base_setup.*).
    """
    try:
        return client.search_read(
            "ir.config_parameter",
            domain=[
                ["key", "not like", "database."],
                ["key", "not like", "base_setup."],
                ["key", "not like", "mail."],
                ["key", "not like", "report."],
            ],
            fields=["key", "value"],
            order="key asc",
        )
    except Exception:
        return []


def query_active_currencies(client: OdooClient) -> list[dict[str, Any]]:
    """Get active currencies."""
    try:
        return client.search_read(
            "res.currency",
            domain=[["active", "=", True]],
            fields=["name", "symbol", "rounding"],
            order="name asc",
        )
    except Exception:
        return []


def query_warehouses(client: OdooClient) -> list[dict[str, Any]]:
    """Get all warehouses."""
    try:
        return client.search_read(
            "stock.warehouse",
            fields=["name", "code", "partner_id"],
            order="name asc",
        )
    except Exception:
        return []


def query_journals(client: OdooClient) -> list[dict[str, Any]]:
    """Get all accounting journals."""
    try:
        return client.search_read(
            "account.journal",
            fields=["name", "type", "code", "company_id"],
            order="code asc",
        )
    except Exception:
        return []


def query_system_overview(client: OdooClient) -> dict[str, Any]:
    """Get a full system overview.

    Useful for post-implementation reports.
    """
    return {
        "installed_modules": query_installed_modules(client),
        "pos_configs": query_pos_configs(client),
        "websites": query_websites(client),
        "company": query_company(client),
        "config_parameters": query_config_parameters(client),
        "active_currencies": query_active_currencies(client),
        "warehouses": query_warehouses(client),
        "journals": query_journals(client),
    }


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def format_date_short(iso_datetime: str) -> str:
    """Convert '2026-01-26 15:30:00' to '26/01/2026'."""
    date_part = iso_datetime.split(" ")[0]
    parts = date_part.split("-")
    return f"{parts[2]}/{parts[1]}/{parts[0]}"


def group_by_date(
    records: list[dict], date_field: str = "create_date"
) -> dict[str, list[dict]]:
    """Group records by their date (YYYY-MM-DD portion of create_date)."""
    groups: dict[str, list[dict]] = {}
    for rec in records:
        date_key = rec[date_field].split(" ")[0]
        groups.setdefault(date_key, []).append(rec)
    return groups


def build_summary_table(
    data: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Build a 'Configuration by Date' summary from all queried data.

    Returns list of dicts: [{"date": "26/01/2026", "items": 30, "detail": "..."}]
    """
    all_records: list[dict[str, str]] = []
    for model_name, records in data.items():
        for rec in records:
            create_date = rec.get("create_date", "")
            if not create_date:
                continue
            all_records.append(
                {
                    "date": create_date.split(" ")[0],
                    "model": model_name,
                    "name": rec.get("name", rec.get("display_name", "")),
                }
            )

    by_date: dict[str, list[dict[str, str]]] = {}
    for rec in all_records:
        by_date.setdefault(rec["date"], []).append(rec)

    summary = []
    for date_key in sorted(by_date.keys()):
        items = by_date[date_key]
        model_counts: dict[str, int] = {}
        for item in items:
            model_counts[item["model"]] = model_counts.get(item["model"], 0) + 1
        detail = ", ".join(
            f"{count} {model}" for model, count in model_counts.items()
        )
        summary.append(
            {
                "date": format_date_short(date_key + " 00:00:00"),
                "items": len(items),
                "detail": detail,
            }
        )

    return summary


# Display labels for model keys
MODEL_LABELS: dict[str, str] = {
    # Products & Inventory
    "products": "Productos (product.template)",
    "product_variants": "Variantes (product.product)",
    "categories": "Categorias (product.category)",
    "attributes": "Atributos (product.attribute)",
    "attribute_values": "Valores de atributo (product.attribute.value)",
    "product_tags": "Tags de producto (product.tag)",
    "pricelists": "Listas de precios (product.pricelist)",
    "pricelist_items": "Reglas de lista de precios (product.pricelist.item)",
    "uom": "Unidades de medida (uom.uom)",
    # Sales
    "quotations": "Cotizaciones (sale.order)",
    "quotation_templates": "Plantillas de cotizacion (sale.order.template)",
    # CRM
    "crm_leads": "Leads CRM (crm.lead)",
    "crm_stages": "Etapas CRM (crm.stage)",
    # Purchase
    "purchase_orders": "Ordenes de compra (purchase.order)",
    # Stock / Inventory
    "warehouses": "Almacenes (stock.warehouse)",
    "stock_locations": "Ubicaciones de stock (stock.location)",
    "picking_types": "Tipos de operacion (stock.picking.type)",
    # Manufacturing / Kits
    "bom": "Listas de materiales (mrp.bom)",
    "bom_lines": "Componentes LdM (mrp.bom.line)",
    "workcenters": "Centros de trabajo (mrp.workcenter)",
    # Accounting & Invoicing
    "invoices": "Facturas (account.move)",
    "journals": "Diarios contables (account.journal)",
    "taxes": "Impuestos (account.tax)",
    "payment_terms": "Plazos de pago (account.payment.term)",
    "fiscal_positions": "Posiciones fiscales (account.fiscal.position)",
    "analytic_plans": "Planes analiticos (account.analytic.plan)",
    "analytic_accounts": "Cuentas analiticas (account.analytic.account)",
    "currencies": "Monedas (res.currency)",
    # Projects & Planning
    "projects": "Proyectos (project.project)",
    "tasks": "Tareas (project.task)",
    "planning_slots": "Planificacion (planning.slot)",
    # HR
    "employees": "Empleados (hr.employee)",
    "departments": "Departamentos (hr.department)",
    "job_positions": "Puestos de trabajo (hr.job)",
    "contracts": "Contratos (hr.contract)",
    "leave_types": "Tipos de ausencia (hr.leave.type)",
    "work_locations": "Ubicaciones de trabajo (hr.work.location)",
    "expenses": "Gastos (hr.expense)",
    # Resources & Scheduling
    "resources": "Recursos (resource.resource)",
    "work_schedules": "Horarios de trabajo (resource.calendar)",
    # POS & Restaurant
    "pos_categories": "Categorias POS (pos.category)",
    "pos_configs": "Configuraciones POS (pos.config)",
    "restaurant_floors": "Pisos restaurante (restaurant.floor)",
    # Events
    "events": "Eventos (event.event)",
    # Fleet
    "vehicles": "Vehiculos (fleet.vehicle)",
    # Partners
    "partners": "Contactos (res.partner)",
    # Email & Automation
    "email_templates": "Plantillas de email (mail.template)",
    "sequences": "Secuencias (ir.sequence)",
}
