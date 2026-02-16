"""Required Odoo modules for the hotel-trip-agency instance."""

# Modules that must be installed for the travel agency to work
REQUIRED_MODULES = {
    'sale_management': 'Sales',
    'sale_margin': 'Margins',
    'crm': 'CRM',
    'project': 'Projects',
    'sale_project': 'Sale+Project',
    'hr_expense': 'Expenses',
    'purchase': 'Purchase',
    'fleet': 'Fleet',
    'website_sale': 'eCommerce',
    'mrp': 'Manufacturing (Kit/BoM)',
    'planning': 'Planning',
    'sale_renting': 'Rental',
}

# Extended list for full audit (includes non-required modules)
AUDIT_MODULES = [
    'sale_management', 'sale_margin', 'crm', 'project', 'fleet',
    'hr_expense', 'purchase', 'mrp', 'website_sale', 'website',
    'sale_subscription', 'sale_project', 'analytic', 'account',
    'planning', 'sale_renting', 'product',
]

# Settings fields to check in res.config.settings
SETTINGS_FIELDS = [
    'group_sale_order_template',
    'module_sale_margin',
    'group_product_variant',
]
