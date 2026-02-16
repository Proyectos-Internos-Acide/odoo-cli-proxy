"""
Odoo MCP Server — expone operaciones XML-RPC como herramientas MCP.

Uso:
    uv run mcp dev mcp_server.py          # MCP Inspector (debug)
    uv run mcp run mcp_server.py          # stdio (para Claude Code)
"""

import json
from mcp.server.fastmcp import FastMCP
from odoo_cli import OdooClient

mcp = FastMCP(
    "odoo",
    instructions=(
        "Servidor MCP para interactuar con una instancia Odoo 19 SaaS vía XML-RPC. "
        "Las credenciales se cargan automáticamente desde el archivo .env del proyecto."
    ),
)

_client: OdooClient | None = None


def _get_client() -> OdooClient:
    global _client
    if _client is None:
        _client = OdooClient()
        _client.connect()
    return _client


def _serialize(obj: object) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_read(
    model: str,
    domain: str = "[]",
    fields: str = "",
    limit: int = 10,
    offset: int = 0,
    order: str = "",
) -> str:
    """Buscar y leer registros de un modelo Odoo.

    Args:
        model: Nombre técnico del modelo (ej. 'res.partner', 'sale.order')
        domain: Dominio de búsqueda en formato JSON (ej. '[["customer_rank", ">", 0]]')
        fields: Campos a leer separados por coma (ej. 'name,email,phone'). Vacío = todos.
        limit: Cantidad máxima de registros (default 10)
        offset: Desplazamiento para paginación
        order: Ordenamiento (ej. 'create_date desc')
    """
    client = _get_client()
    domain_list = json.loads(domain)
    field_list = [f.strip() for f in fields.split(",") if f.strip()] or []

    kwargs: dict = {}
    if field_list:
        kwargs["fields"] = field_list
    if limit:
        kwargs["limit"] = limit
    if offset:
        kwargs["offset"] = offset
    if order:
        kwargs["order"] = order

    result = client.execute(model, "search_read", domain_list, **kwargs)
    return _serialize(result)


@mcp.tool()
def execute(
    model: str,
    method: str,
    args: str = "[]",
    kwargs: str = "{}",
) -> str:
    """Ejecutar cualquier método XML-RPC en un modelo Odoo.

    Args:
        model: Nombre técnico del modelo
        method: Nombre del método (ej. 'read', 'name_get', 'action_confirm')
        args: Lista de argumentos posicionales en JSON (ej. '[[1, 2, 3]]')
        kwargs: Diccionario de argumentos keyword en JSON (ej. '{"context": {"lang": "es_419"}}')
    """
    client = _get_client()
    args_list = json.loads(args)
    kwargs_dict = json.loads(kwargs)
    result = client.execute(model, method, *args_list, **kwargs_dict)
    return _serialize(result)


@mcp.tool()
def read_fields(
    model: str,
    attributes: str = "string,type,required,readonly,relation",
) -> str:
    """Inspeccionar los campos de un modelo Odoo.

    Args:
        model: Nombre técnico del modelo (ej. 'sale.order')
        attributes: Atributos a leer por campo, separados por coma.
                    Default: 'string,type,required,readonly,relation'
    """
    client = _get_client()
    attr_list = [a.strip() for a in attributes.split(",") if a.strip()]
    result = client.execute(model, "fields_get", attributes=attr_list)
    return _serialize(result)


@mcp.tool()
def list_models(filter: str = "") -> str:
    """Listar modelos disponibles en la instancia Odoo.

    Args:
        filter: Filtro opcional por nombre (ej. 'sale' para modelos que contienen 'sale')
    """
    client = _get_client()
    domain = []
    if filter:
        domain = [["model", "ilike", filter]]
    result = client.execute(
        "ir.model", "search_read", domain, fields=["model", "name"], order="model"
    )
    return _serialize(result)


@mcp.tool()
def create_record(model: str, vals: str) -> str:
    """Crear un registro en un modelo Odoo.

    Args:
        model: Nombre técnico del modelo (ej. 'res.partner')
        vals: Diccionario de valores en JSON (ej. '{"name": "Juan", "email": "juan@mail.com"}')
    """
    client = _get_client()
    vals_dict = json.loads(vals)
    result = client.execute(model, "create", [vals_dict])
    # Odoo 19 retorna lista
    if isinstance(result, list):
        result = result[0]
    return _serialize({"id": result})


@mcp.tool()
def write_record(model: str, ids: str, vals: str) -> str:
    """Actualizar registros en un modelo Odoo.

    Args:
        model: Nombre técnico del modelo
        ids: Lista de IDs en JSON (ej. '[1, 2, 3]')
        vals: Diccionario de valores a actualizar en JSON (ej. '{"name": "Nuevo nombre"}')
    """
    client = _get_client()
    ids_list = json.loads(ids)
    vals_dict = json.loads(vals)
    result = client.execute(model, "write", ids_list, vals_dict)
    return _serialize({"success": bool(result)})


@mcp.tool()
def unlink_record(model: str, ids: str) -> str:
    """Eliminar registros de un modelo Odoo.

    Args:
        model: Nombre técnico del modelo
        ids: Lista de IDs en JSON (ej. '[1, 2, 3]')
    """
    client = _get_client()
    ids_list = json.loads(ids)
    result = client.execute(model, "unlink", ids_list)
    return _serialize({"success": bool(result)})


if __name__ == "__main__":
    mcp.run()
