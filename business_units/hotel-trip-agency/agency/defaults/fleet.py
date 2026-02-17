"""Fleet service type defaults for the travel agency.

Defines service types for vehicle maintenance tracking in the Fleet module.
Categories: 'service' = one-time (repairs), 'contract' = recurring (insurance).
"""

FLEET_SERVICE_TYPES = [
    {"name": "Cambio de aceite", "category": "service"},
    {"name": "Revision tecnica", "category": "service"},
    {"name": "Lavado", "category": "service"},
    {"name": "Reparacion general", "category": "service"},
    {"name": "Cambio de llantas", "category": "service"},
    {"name": "SOAT", "category": "contract"},
    {"name": "Seguro vehicular", "category": "contract"},
]
