"""Default configuration for sprint report generation."""

# Company information (used in LaTeX headers and title blocks)
COMPANY_NAME = r"A\&F Destiny E.I.R.L."
PROJECT_SUBTITLE = r"Hotel \& Trip Agency"
PROJECT_DESCRIPTION = (
    r"Implementaci\'on de ERP Odoo 19 para Hotel, "
    r"Agencia de Viajes y Restaurante"
)

# LaTeX theme colors (hex without #)
COLORS = {
    "primary": "2C3E50",
    "accent": "2980B9",
    "success": "27AE60",
    "warn": "F39C12",
}

# Output directory (relative to project_management/)
GENERATED_DIR = "generated"

# Auxiliary file extensions to clean after compilation
AUX_EXTENSIONS = [
    ".aux", ".log", ".out", ".toc", ".lof", ".lot",
    ".fls", ".fdb_latexmk", ".synctex.gz",
]

# LaTeX compiler
LATEX_CMD = "pdflatex"
LATEX_ARGS = ["-interaction=nonstopmode"]

# Pandoc compiler (for markdown -> PDF)
PANDOC_CMD = "pandoc"
PANDOC_ARGS = [
    "--pdf-engine=pdflatex",
    "-V", "geometry:margin=2.5cm",
    "-V", "lang=es",
    "-V", "fontsize=12pt",
    "--highlight-style=tango",
]

# Post-implementation report types
REPORT_TYPES = ["implementation", "executive_summary", "lessons_learned"]

# Project metadata (for post-implementation reports)
PROJECT_CODE = r"N\textdegree{} 471-PROINNOVATE-IMTEMD-2025"
PROJECT_ENTITY = COMPANY_NAME
PROJECT_RUC = "20600144813"
PROJECT_DATE = "Febrero 2026"
COORDINATOR_NAME = "Nohemi Milagros Cjumo Ovalle"
CONSULTANT_NAME = "Marco Rosendo Mejia Miranda"
PROGRAM_NAME = r"PROGRAMA PROINNOVATE -- IMTEMD 2025"
