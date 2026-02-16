"""POS category definitions for the restaurant."""

POS_CATEGORIES = [
    {"name": {'es': "Bebidas", 'en': "Drinks"}, "sequence": 10},
    {"name": {'es': "Desayuno", 'en': "Breakfast"}, "sequence": 20},
    {"name": {'es': "Platos de fondo", 'en': "Main Courses"}, "sequence": 30},
    {"name": {'es': "Hamburguesas", 'en': "Burgers"}, "sequence": 40},
    {"name": {'es': "Sandwiches", 'en': "Sandwiches"}, "sequence": 50},
    {"name": {'es': "Salchipapas", 'en': "Salchipapas"}, "sequence": 60},
]

PREP_DISPLAY_NAME = "Despacho restaurante"

PREP_STAGES = [
    {"name": "To prepare", "color": "#6C757D", "alert_timer": 10},
    {"name": "Ready", "color": "#4D89D1", "alert_timer": 5},
    {"name": "Completed", "color": "#4ea82a", "alert_timer": 0},
]
