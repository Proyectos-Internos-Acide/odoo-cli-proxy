"""Kit/BoM definitions for tour packages."""

KITS = [
    {
        "name": {'es': "Cusco 3D/2N", 'en': "Cusco 3D/2N"},
        "type": "consu",
        "sale_ok": True,
        "purchase_ok": False,
        "list_price": 500.0,
        "standard_price": 0.0,
        "components": [
            {
                "template_name": "Apartment 301",
                "qty": 2,
                "label": "Hotel (2 noches)",
            },
            {
                "template_name": "City Tour Cusco",
                "qty": 1,
                "label": "City Tour",
            },
            {
                "template_name": "Palcoyo",
                "qty": 1,
                "label": "Palcoyo",
            },
            {
                "template_name": "Transportation from Airport",
                "qty": 1,
                "label": "Transporte",
            },
        ],
    },
]
