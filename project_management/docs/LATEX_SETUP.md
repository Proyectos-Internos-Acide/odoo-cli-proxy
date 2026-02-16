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
