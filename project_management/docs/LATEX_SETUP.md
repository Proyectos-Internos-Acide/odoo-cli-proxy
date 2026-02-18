# LaTeX and Pandoc Setup Guide

Prerequisites for compiling report PDFs.

## LaTeX (for .tex files)

### Arch Linux

```bash
sudo pacman -S texlive-basic texlive-latexrecommended texlive-latexextra texlive-fontsrecommended texlive-langspanish
```

#### Packages explained

| pacman package              | LaTeX packages it provides                                            |
| --------------------------- | --------------------------------------------------------------------- |
| `texlive-basic`             | `pdflatex` compiler, core LaTeX engine                                |
| `texlive-latexrecommended`  | `graphicx`, `hyperref`, `geometry`, `longtable`                       |
| `texlive-latexextra`        | `booktabs`, `tabularx`, `enumitem`, `fancyhdr`, `titlesec`, `xcolor` |
| `texlive-fontsrecommended`  | Standard fonts for PDF output                                         |
| `texlive-langspanish`       | `babel` Spanish language support                                      |

### Ubuntu / Debian

```bash
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-lang-spanish
```

### Windows

#### Option A: MiKTeX (recommended for Windows)

1. Download the installer from https://miktex.org/download
2. Run the installer and select "Install missing packages on the fly: Yes"
3. MiKTeX will auto-install any missing LaTeX packages on first compilation

#### Option B: TeX Live

1. Download the installer from https://tug.org/texlive/acquire-netinstall.html
2. Run `install-tl-windows.bat`
3. Select "scheme-full" for all packages, or "scheme-medium" and install extras later with:
   ```cmd
   tlmgr install booktabs tabularx enumitem fancyhdr titlesec xcolor babel-spanish
   ```

#### PATH configuration (Windows)

After installation, ensure `pdflatex` is in your PATH:

- **MiKTeX**: The installer adds it automatically. Verify with `pdflatex --version` in CMD.
- **TeX Live**: Add `C:\texlive\2025\bin\windows` (adjust year) to your system PATH.

### Verify LaTeX installation

```bash
pdflatex --version
```

## Pandoc (for .md to PDF conversion)

Pandoc is required only if you want to convert Markdown reports to PDF.

### Arch Linux

```bash
sudo pacman -S pandoc
```

### Ubuntu / Debian

```bash
sudo apt install pandoc
```

### Windows

Download and install from https://pandoc.org/installing.html

The installer adds `pandoc` to PATH automatically.

### Verify Pandoc installation

```bash
pandoc --version
```

**Note:** Pandoc uses `pdflatex` as its PDF engine, so LaTeX must also be installed for Markdown-to-PDF conversion.

## PlantUML (for UML diagrams)

PlantUML generates professional UML diagrams (use cases, sequences, class/ER).

### Dependencies

PlantUML requires **Java** and **Graphviz**:

```bash
# Arch Linux
sudo pacman -S graphviz    # Required for use-case, class, and ER diagrams
# Note: Java (openjdk) should already be installed
```

```bash
# Ubuntu / Debian
sudo apt install graphviz default-jre
```

### Installation (user-local, no sudo)

```bash
mkdir -p ~/.local/lib ~/.local/bin
curl -L -o ~/.local/lib/plantuml.jar \
  "https://github.com/plantuml/plantuml/releases/download/v1.2024.7/plantuml-1.2024.7.jar"
printf '#!/bin/sh\njava -jar ~/.local/lib/plantuml.jar "$@"\n' > ~/.local/bin/plantuml
chmod +x ~/.local/bin/plantuml
```

### Verify

```bash
plantuml -version
```

### Usage

```bash
# Generate PNG from .puml file
plantuml -tpng diagram.puml -o /absolute/path/to/output/

# Generate SVG (vector, higher quality)
plantuml -tsvg diagram.puml -o /absolute/path/to/output/
```

**Important:** The `-o` flag requires an **absolute path**. Relative paths create nested directories.

### Graphviz dependency matrix

| Diagram type     | Needs Graphviz? |
|------------------|-----------------|
| Sequence         | No              |
| Activity         | No              |
| Use Case         | **Yes**         |
| Class / ER       | **Yes**         |
| Component        | **Yes**         |

Without Graphviz, affected diagrams produce a small error image (~10KB).

## LaTeX packages used in templates

| Package      | Purpose                                            |
| ------------ | -------------------------------------------------- |
| `inputenc`   | UTF-8 encoding for Spanish characters              |
| `fontenc`    | T1 font encoding                                   |
| `babel`      | Spanish language hyphenation and labels             |
| `geometry`   | Page margins (2.5cm)                                |
| `graphicx`   | Image inclusion (`\includegraphics`)                |
| `booktabs`   | Professional table rules (`\toprule`, `\midrule`)   |
| `tabularx`   | Tables with auto-width columns (`X` type)           |
| `enumitem`   | Customized lists                                    |
| `hyperref`   | Clickable URLs and cross-references                 |
| `xcolor`     | Custom colors for headers and status indicators     |
| `fancyhdr`   | Custom page headers and footers                     |
| `titlesec`   | Styled section headings with colored rules          |
| `longtable`  | Tables that span multiple pages                     |
| `float`      | Precise figure/table placement (`[H]`)              |
| `amsmath`    | Mathematical formulas                               |
| `helvet`     | Helvetica/Arial font family                         |
| `setspace`   | Line spacing control (`\onehalfspacing`)            |
| `etoolbox`   | Environment hooks (auto `\noindent` on tabularx)    |
| `tikz`       | Native LaTeX vector diagrams                        |
| `caption`    | Caption positioning (above) and left-alignment      |
| `pdflscape`  | Landscape pages for wide content (rotated in viewer) |

See `STYLE_GUIDE.md` for the full standard preamble and style configurations.

## Compilation

### Single .tex file (e.g., sprint reports)

```bash
cd project_management/generated/reports/<report_name>/
pdflatex -interaction=nonstopmode <file>.tex
```

### Reports with TOC, LOF, LOT (e.g., implementation report)

Reports using `\tableofcontents`, `\listoffigures`, or `\listoftables` need **2 passes**:

```bash
cd project_management/generated/reports/implementation/
pdflatex -interaction=nonstopmode implementation.tex
pdflatex -interaction=nonstopmode implementation.tex   # 2nd pass resolves refs
```

### PlantUML diagrams

Generate PNG images from `.puml` source files before compiling:

```bash
cd project_management/generated/reports/implementation/
plantuml -tpng diagrams/use_case.puml -o "$(pwd)/img/"
plantuml -tpng diagrams/sequence_tour.puml -o "$(pwd)/img/"
plantuml -tpng diagrams/sequence_reservation.puml -o "$(pwd)/img/"
plantuml -tpng diagrams/data_model.puml -o "$(pwd)/img/"
```

**Important:** The `-o` flag requires an **absolute path**. Use `$(pwd)` to build it.

## Report Directory Structure

Each report follows this layout:

```
generated/reports/<report_name>/
├── <report_name>.tex          # Main LaTeX source
├── <report_name>.pdf          # Compiled output
├── img/                       # PNG images (screenshots, generated diagrams)
│   ├── use_case.png
│   ├── sequence_tour.png
│   └── ...
├── diagrams/                  # PlantUML source files (.puml)
│   ├── use_case.puml
│   ├── sequence_tour.puml
│   └── ...
└── <auxiliary files>          # .aux, .log, .toc, .lof, .lot, .out
```

- **img/**: Contains all images referenced by `\includegraphics`. Both manually placed screenshots and PlantUML-generated PNGs go here.
- **diagrams/**: Contains `.puml` source files. Run `plantuml -tpng` to generate PNGs into `img/`.
- **Auxiliary files**: Generated by `pdflatex`. Can be cleaned with `clean_sprint.py` or deleted manually.
