"""Default restaurant products (minimal - just beverages)."""

PRODUCTS = [
    {
        "name": {'es': "Agua", 'en': "Water"},
        "type": "consu",
        "list_price": 2.20,
        "pos_categ": "Bebidas",
        "available_in_pos": True,
        "sale_ok": True,
    },
    {
        "name": {'es': "Gaseosa", 'en': "Soda"},
        "type": "consu",
        "list_price": 3.00,
        "pos_categ": "Bebidas",
        "available_in_pos": True,
        "sale_ok": True,
    },
]
