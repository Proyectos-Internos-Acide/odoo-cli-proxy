"""Default configuration for sprint report generation."""

# =========================================================================
# COMPANY / BENEFICIARY INFORMATION
# =========================================================================
COMPANY_NAME = r"A\&F Destiny E.I.R.L."
PROJECT_SUBTITLE = r"Hotel \& Trip Agency"
PROJECT_DESCRIPTION = (
    r"Fortalecimiento de la Competitividad y Optimizaci\'on de Procesos "
    r"en A\&F Destiny E.I.R.L. mediante la Digitalizaci\'on de Reservas, "
    r"Gesti\'on de Datos y Estrategias de Gesti\'on Comercial."
)
PROJECT_RUC = "20600144813"
LEGAL_REPRESENTATIVE = "Nohemi Milagros Cjumo Ovalle"

# =========================================================================
# IMPLEMENTING COMPANY
# =========================================================================
IMPLEMENTING_COMPANY = "VISEPRO"

# =========================================================================
# PROJECT METADATA
# =========================================================================
PROJECT_CODE = r"N\textdegree{} 471-PROINNOVATE-IMTEMD-2025"
PROGRAM_NAME = r"PROGRAMA PROINNOVATE -- IMTEMD 2025"
REPORT_DATE_START = "01/12/2025"
REPORT_DATE_END = "28/02/2026"

# =========================================================================
# PEOPLE
# =========================================================================
COORDINATOR_NAME = "Nohemi Milagros Cjumo Ovalle"
CONSULTANT_NAME = "Enrique Mauro Villavicencio Luna"
CO_CONSULTANT_NAME = r"Gonzalo Enrique Guti\'errez Castillo"

# =========================================================================
# LOCATION
# =========================================================================
CITY = "CUSCO"
COUNTRY = r"PER\'U"
YEAR = "2026"

# =========================================================================
# IMAGES (relative to report's img/ folder)
# =========================================================================
COVER_IMAGE = "VISEPRO_portada.jpg"      # Full-bleed cover page
LOGO_IMAGE = "MACHU-PICCHU-AF-DESTINY-LOGO.png"  # Company logo for title page

# =========================================================================
# LATEX THEME COLORS (hex without #)
# =========================================================================
COLORS = {
    "primary": "2C3E50",
    "accent": "2980B9",
    "success": "27AE60",
    "warn": "F39C12",
}

# =========================================================================
# BUILD SETTINGS
# =========================================================================
GENERATED_DIR = "generated"

AUX_EXTENSIONS = [
    ".aux", ".log", ".out", ".toc", ".lof", ".lot",
    ".fls", ".fdb_latexmk", ".synctex.gz",
]

LATEX_CMD = "pdflatex"
LATEX_ARGS = ["-interaction=nonstopmode"]

PANDOC_CMD = "pandoc"
PANDOC_ARGS = [
    "--pdf-engine=pdflatex",
    "-V", "geometry:margin=2.5cm",
    "-V", "lang=es",
    "-V", "fontsize=12pt",
    "--highlight-style=tango",
]

REPORT_TYPES = ["implementation", "executive_summary", "lessons_learned"]

# Backward compatibility aliases
PROJECT_ENTITY = COMPANY_NAME
PROJECT_DATE = "Febrero 2026"
