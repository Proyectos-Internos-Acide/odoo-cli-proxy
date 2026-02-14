"""Template rendering utilities shared by sprint and report scripts."""

from pathlib import Path
from typing import Any


def render_template(template_path: Path, replacements: dict[str, str]) -> str:
    """Read a template file and replace all {{PLACEHOLDER}} tokens."""
    content = template_path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in a string."""
    chars = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for char, escaped in chars.items():
        text = text.replace(char, escaped)
    return text


# ---------------------------------------------------------------------------
# Field formatting helpers
# ---------------------------------------------------------------------------


def _m2o_display(record: dict, field: str) -> str:
    """Extract display name from a Many2one field ([id, name] or False)."""
    val = record.get(field)
    if isinstance(val, (list, tuple)) and len(val) >= 2:
        return str(val[1])
    return str(val) if val else ""


def _format_field(record: dict, field: str, fmt_type: str = "str") -> str:
    """Format a record field value based on its type.

    Supported fmt_type values:
        str:      default string conversion
        m2o:      Many2one display name
        currency: format as S/.X.XX
        bool:     Si / No
        date:     extract YYYY-MM-DD from datetime string
    """
    val = record.get(field)
    if fmt_type == "m2o":
        return _m2o_display(record, field)
    if fmt_type == "currency":
        return f"S/.{float(val or 0):.2f}"
    if fmt_type == "bool":
        return "Si" if val else "No"
    if fmt_type == "date":
        return str(val).split(" ")[0] if val else ""
    return str(val) if val else ""


# ---------------------------------------------------------------------------
# Column definitions per model key: list of (header, field_name, format_type)
# ---------------------------------------------------------------------------

MODEL_COLUMNS: dict[str, list[tuple[str, str, str]]] = {
    # ── Products & Inventory ──────────────────────────────────────────
    "products": [
        ("ID", "id", "str"), ("Producto", "name", "str"),
        ("Precio", "list_price", "currency"), ("Tipo", "type", "str"),
    ],
    "product_variants": [
        ("ID", "id", "str"), ("Variante", "name", "str"),
        ("Template", "product_tmpl_id", "m2o"),
    ],
    "categories": [
        ("ID", "id", "str"), ("Categoria", "name", "str"),
        ("Padre", "parent_id", "m2o"),
    ],
    "attributes": [
        ("ID", "id", "str"), ("Atributo", "name", "str"),
        ("Variante", "create_variant", "str"),
    ],
    "attribute_values": [
        ("ID", "id", "str"), ("Valor", "name", "str"),
        ("Atributo", "attribute_id", "m2o"),
    ],
    "product_tags": [
        ("ID", "id", "str"), ("Tag", "name", "str"),
    ],
    "pricelists": [
        ("ID", "id", "str"), ("Lista de Precios", "name", "str"),
        ("Moneda", "currency_id", "m2o"),
    ],
    "pricelist_items": [
        ("ID", "id", "str"), ("Lista", "pricelist_id", "m2o"),
        ("Aplicado en", "applied_on", "str"), ("Calculo", "compute_price", "str"),
    ],
    "uom": [
        ("ID", "id", "str"), ("UdM", "name", "str"),
        ("Categoria", "category_id", "m2o"),
    ],
    # ── Sales ─────────────────────────────────────────────────────────
    "quotations": [
        ("ID", "id", "str"), ("Nombre", "name", "str"),
        ("Cliente", "partner_id", "m2o"), ("Estado", "state", "str"),
        ("Total", "amount_total", "currency"),
    ],
    "quotation_templates": [
        ("ID", "id", "str"), ("Plantilla", "name", "str"),
    ],
    # ── CRM ───────────────────────────────────────────────────────────
    "crm_leads": [
        ("ID", "id", "str"), ("Lead", "name", "str"),
        ("Etapa", "stage_id", "m2o"), ("Cliente", "partner_id", "m2o"),
    ],
    "crm_stages": [
        ("ID", "id", "str"), ("Etapa", "name", "str"),
    ],
    # ── Purchase ──────────────────────────────────────────────────────
    "purchase_orders": [
        ("ID", "id", "str"), ("Nombre", "name", "str"),
        ("Proveedor", "partner_id", "m2o"), ("Estado", "state", "str"),
        ("Total", "amount_total", "currency"),
    ],
    # ── Stock / Inventory ─────────────────────────────────────────────
    "warehouses": [
        ("ID", "id", "str"), ("Almacen", "name", "str"),
        ("Codigo", "code", "str"),
    ],
    "stock_locations": [
        ("ID", "id", "str"), ("Ubicacion", "name", "str"),
        ("Tipo", "usage", "str"),
    ],
    "picking_types": [
        ("ID", "id", "str"), ("Tipo Operacion", "name", "str"),
        ("Codigo", "code", "str"), ("Almacen", "warehouse_id", "m2o"),
    ],
    # ── Manufacturing / Kits ──────────────────────────────────────────
    "bom": [
        ("ID", "id", "str"), ("Producto", "product_tmpl_id", "m2o"),
        ("Tipo", "type", "str"), ("Cantidad", "product_qty", "str"),
    ],
    "bom_lines": [
        ("ID", "id", "str"), ("Componente", "product_id", "m2o"),
        ("Cantidad", "product_qty", "str"), ("LdM", "bom_id", "m2o"),
    ],
    "workcenters": [
        ("ID", "id", "str"), ("Centro de Trabajo", "name", "str"),
    ],
    # ── Accounting & Invoicing ────────────────────────────────────────
    "invoices": [
        ("ID", "id", "str"), ("Numero", "name", "str"),
        ("Tercero", "partner_id", "m2o"), ("Tipo", "move_type", "str"),
        ("Estado", "state", "str"), ("Total", "amount_total", "currency"),
    ],
    "journals": [
        ("ID", "id", "str"), ("Diario", "name", "str"),
        ("Tipo", "type", "str"), ("Codigo", "code", "str"),
    ],
    "taxes": [
        ("ID", "id", "str"), ("Impuesto", "name", "str"),
        ("Monto", "amount", "str"), ("Uso", "type_tax_use", "str"),
    ],
    "payment_terms": [
        ("ID", "id", "str"), ("Plazo de Pago", "name", "str"),
    ],
    "fiscal_positions": [
        ("ID", "id", "str"), ("Posicion Fiscal", "name", "str"),
    ],
    "analytic_plans": [
        ("ID", "id", "str"), ("Plan Analitico", "name", "str"),
    ],
    "analytic_accounts": [
        ("ID", "id", "str"), ("Cuenta", "name", "str"),
        ("Plan", "plan_id", "m2o"),
    ],
    "currencies": [
        ("ID", "id", "str"), ("Moneda", "name", "str"),
        ("Simbolo", "symbol", "str"), ("Activa", "active", "bool"),
    ],
    # ── Projects & Planning ───────────────────────────────────────────
    "projects": [
        ("ID", "id", "str"), ("Proyecto", "name", "str"),
        ("Template", "is_template", "bool"),
    ],
    "tasks": [
        ("ID", "id", "str"), ("Tarea", "name", "str"),
        ("Proyecto", "project_id", "m2o"), ("Etapa", "stage_id", "m2o"),
    ],
    "planning_slots": [
        ("ID", "id", "str"), ("Nombre", "display_name", "str"),
        ("Inicio", "start_datetime", "date"), ("Fin", "end_datetime", "date"),
    ],
    # ── HR ────────────────────────────────────────────────────────────
    "employees": [
        ("ID", "id", "str"), ("Empleado", "name", "str"),
        ("Departamento", "department_id", "m2o"), ("Puesto", "job_id", "m2o"),
    ],
    "departments": [
        ("ID", "id", "str"), ("Departamento", "name", "str"),
        ("Padre", "parent_id", "m2o"), ("Responsable", "manager_id", "m2o"),
    ],
    "job_positions": [
        ("ID", "id", "str"), ("Puesto", "name", "str"),
        ("Departamento", "department_id", "m2o"),
    ],
    "contracts": [
        ("ID", "id", "str"), ("Contrato", "name", "str"),
        ("Empleado", "employee_id", "m2o"), ("Estado", "state", "str"),
        ("Salario", "wage", "currency"),
    ],
    "leave_types": [
        ("ID", "id", "str"), ("Tipo de Ausencia", "name", "str"),
    ],
    "work_locations": [
        ("ID", "id", "str"), ("Ubicacion", "name", "str"),
    ],
    "expenses": [
        ("ID", "id", "str"), ("Gasto", "name", "str"),
        ("Monto", "total_amount", "currency"), ("Estado", "state", "str"),
    ],
    # ── Resources & Scheduling ────────────────────────────────────────
    "resources": [
        ("ID", "id", "str"), ("Recurso", "name", "str"),
        ("Tipo", "resource_type", "str"),
    ],
    "work_schedules": [
        ("ID", "id", "str"), ("Horario", "name", "str"),
        ("Zona Horaria", "tz", "str"),
    ],
    # ── POS & Restaurant ──────────────────────────────────────────────
    "pos_categories": [
        ("ID", "id", "str"), ("Categoria", "name", "str"),
        ("Padre", "parent_id", "m2o"),
    ],
    "pos_configs": [
        ("ID", "id", "str"), ("Config POS", "name", "str"),
    ],
    "restaurant_floors": [
        ("ID", "id", "str"), ("Piso", "name", "str"),
    ],
    # ── Events ────────────────────────────────────────────────────────
    "events": [
        ("ID", "id", "str"), ("Evento", "name", "str"),
        ("Inicio", "date_begin", "date"), ("Fin", "date_end", "date"),
    ],
    # ── Fleet ─────────────────────────────────────────────────────────
    "vehicles": [
        ("ID", "id", "str"), ("Vehiculo", "name", "str"),
        ("Modelo", "model_id", "m2o"),
    ],
    # ── Partners ──────────────────────────────────────────────────────
    "partners": [
        ("ID", "id", "str"), ("Nombre", "name", "str"),
        ("Email", "email", "str"), ("Empresa", "is_company", "bool"),
    ],
    # ── Email & Automation ────────────────────────────────────────────
    "email_templates": [
        ("ID", "id", "str"), ("Plantilla", "name", "str"),
        ("Modelo", "model_id", "m2o"),
    ],
    "sequences": [
        ("ID", "id", "str"), ("Secuencia", "name", "str"),
        ("Codigo", "code", "str"), ("Prefijo", "prefix", "str"),
    ],
}

_DEFAULT_COLUMNS: list[tuple[str, str, str]] = [
    ("ID", "id", "str"), ("Nombre", "name", "str"), ("Fecha", "create_date", "date"),
]


# ---------------------------------------------------------------------------
# Generic table formatters
# ---------------------------------------------------------------------------


def records_to_latex_rows(
    records: list[dict[str, Any]], columns: list[tuple[str, str, str]]
) -> str:
    """Convert records to LaTeX table rows using column definitions."""
    lines = []
    for rec in records:
        cells = []
        for _header, field, fmt_type in columns:
            val = _format_field(rec, field, fmt_type)
            cells.append(escape_latex(val))
        lines.append("    " + " & ".join(cells) + " \\\\")
    return "\n".join(lines)


def records_to_md_rows(
    records: list[dict[str, Any]], columns: list[tuple[str, str, str]]
) -> str:
    """Convert records to markdown table rows using column definitions."""
    lines = []
    for rec in records:
        cells = [_format_field(rec, field, fmt_type) for _, field, fmt_type in columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_section_latex(
    label: str, records: list[dict[str, Any]],
    columns: list[tuple[str, str, str]],
) -> str:
    """Build a complete LaTeX subsection with table for a model."""
    rows = records_to_latex_rows(records, columns)
    headers = " & ".join(
        f"\\textbf{{{escape_latex(h)}}}" for h, _, _ in columns
    )
    # r for ID, X for name (flexible), l for remaining columns
    col_spec = "r" + "X" + "l" * max(0, len(columns) - 2)
    return (
        f"\\subsection{{{escape_latex(label)} ({len(records)})}}\n\n"
        f"\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}\n"
        f"    \\toprule\n"
        f"    {headers} \\\\\n"
        f"    \\midrule\n"
        f"{rows}\n"
        f"    \\bottomrule\n"
        f"\\end{{tabularx}}"
    )


def build_section_md(
    label: str, records: list[dict[str, Any]],
    columns: list[tuple[str, str, str]],
) -> str:
    """Build a complete markdown subsection with table for a model."""
    rows = records_to_md_rows(records, columns)
    headers = "| " + " | ".join(h for h, _, _ in columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    return f"## {label} ({len(records)})\n\n{headers}\n{separator}\n{rows}"


def build_all_data_sections(
    data: dict[str, list[dict[str, Any]]],
    model_labels: dict[str, str],
    fmt: str,
) -> str:
    """Build all Odoo data sections from query results.

    Args:
        data: Dict from query_date_range(), keyed by model alias.
        model_labels: Display labels from MODEL_LABELS.
        fmt: "latex" or "markdown".
    """
    sections = []
    for key, records in data.items():
        label = model_labels.get(key, key)
        columns = MODEL_COLUMNS.get(key, _DEFAULT_COLUMNS)
        if fmt == "latex":
            sections.append(build_section_latex(label, records, columns))
        else:
            sections.append(build_section_md(label, records, columns))
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Summary table formatters
# ---------------------------------------------------------------------------


def summary_to_latex_rows(summary: list[dict[str, Any]]) -> str:
    """Convert summary table entries to LaTeX rows: Date & Items & Detail \\\\"""
    lines = []
    total = 0
    for row in summary:
        detail = escape_latex(str(row["detail"]))
        lines.append(f"    {row['date']} & {row['items']} & {detail} \\\\")
        total += row["items"]
    lines.append("    \\midrule")
    lines.append(f"    \\textbf{{Total}} & \\textbf{{{total}}} & \\\\")
    return "\n".join(lines)


def summary_to_md_rows(summary: list[dict[str, Any]]) -> str:
    lines = []
    total = 0
    for row in summary:
        lines.append(f"| {row['date']} | {row['items']} | {row['detail']} |")
        total += row["items"]
    lines.append(f"| **Total** | **{total}** | |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Evidence image formatters
# ---------------------------------------------------------------------------


def evidence_to_latex(image_paths: list[str]) -> str:
    """Generate LaTeX figure blocks for evidence images."""
    blocks = []
    for i, path in enumerate(image_paths, 1):
        block = (
            "\\begin{figure}[h]\n"
            "    \\centering\n"
            f"    \\includegraphics[width=0.9\\textwidth]{{{path}}}\n"
            f"    \\caption{{Evidencia {i}}}\n"
            "\\end{figure}"
        )
        blocks.append(block)
    return "\n\n".join(blocks)


def evidence_to_md(image_paths: list[str]) -> str:
    """Generate markdown image references for evidence."""
    lines = []
    for i, path in enumerate(image_paths, 1):
        lines.append(f"![Evidencia {i}]({path})")
        lines.append("")
    return "\n".join(lines)
