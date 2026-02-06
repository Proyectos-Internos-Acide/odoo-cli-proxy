"""Product definitions for the travel agency."""

# Purchase-only product for third-party transport services
TRANSPORT_PRODUCT = {
    "name": "Servicio de Transporte Externo",
    "type": "service",
    "purchase_ok": True,
    "sale_ok": False,
    "list_price": 0.0,
    "standard_price": 0.0,
}

# Default timezone for verification checks
DEFAULT_TIMEZONE = "America/Lima"
