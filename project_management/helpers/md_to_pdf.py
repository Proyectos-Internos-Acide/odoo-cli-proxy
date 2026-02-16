"""Convert Markdown files to PDF via pandoc."""

import subprocess
from pathlib import Path

PANDOC_CMD = "pandoc"
PANDOC_ARGS = [
    "--pdf-engine=pdflatex",
    "-V", "geometry:margin=2.5cm",
    "-V", "lang=es",
    "-V", "fontsize=12pt",
    "--highlight-style=tango",
]


def md_to_pdf(
    md_file: Path, output_pdf: Path | None = None
) -> tuple[bool, str]:
    """Convert a .md file to PDF using pandoc.

    Args:
        md_file: Path to the markdown source.
        output_pdf: Optional output path. Defaults to same name with .pdf.

    Returns:
        Tuple of (success: bool, message: str).
    """
    if output_pdf is None:
        output_pdf = md_file.with_suffix(".pdf")

    cmd = [PANDOC_CMD, str(md_file.name), "-o", str(output_pdf.name), *PANDOC_ARGS]

    try:
        result = subprocess.run(
            cmd,
            cwd=md_file.parent,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "pandoc not found. Install it: sudo pacman -S pandoc"

    if result.returncode != 0:
        error_lines = result.stderr.strip().split("\n")[-5:]
        return False, "\n".join(error_lines)

    return True, str(output_pdf.name)
