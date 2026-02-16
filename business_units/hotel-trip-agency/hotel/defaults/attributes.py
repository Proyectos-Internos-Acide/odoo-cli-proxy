"""Hotel and tour product attribute configuration."""

# Hotel/stay attributes that should NOT create variants (no_variant)
# These are informational specs (beds, bathrooms, area, etc.)
HOTEL_ATTR_IDS = [24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37]
# Names: Adicionales, Camas, Beds, Bathrooms, Room Service, Warm Water,
#        Internet Gratis, Telefono, Servicio Lavanderia, Estacionamiento,
#        Area, TV Cable, TVs, Habitaciones

# Tour attributes that SHOULD create variants (always)
# These generate price-differentiating variants
TOUR_ATTR_IDS = [38, 39, 40, 41, 42, 43, 44, 45]

# Target create_variant mode for hotel attributes
HOTEL_ATTR_MODE = 'no_variant'

# Target create_variant mode for tour attributes
TOUR_ATTR_MODE = 'always'
