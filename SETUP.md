# Setup

## 1. Prerequisites

### Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

You need an Anthropic API key or a Claude subscription. See the
[Claude Code docs](https://docs.anthropic.com/en/docs/claude-code).

### Python 3.10+

```bash
python3 --version      # py --version on Windows
```

No third-party packages are required. `pypdf` is optional — the PDF tools
fall back to Poppler's `pdftotext`, and `tools/verify_layout.py` needs
Poppler specifically (it uses `pdftotext -bbox`, which has no pypdf
equivalent).

```bash
pip install pypdf      # optional
```

### Bun — for the portal search CLIs

```bash
curl -fsSL https://bun.sh/install | bash                       # macOS/Linux
powershell -c "irm https://bun.sh/install.ps1 | iex"           # Windows
```

The CLIs have **zero runtime dependencies**, so they run from a fresh clone
with no install step. `bun install` is only needed to run their typechecks.

### Poppler — for PDF verification

```bash
sudo apt install poppler-utils          # Debian/Ubuntu
brew install poppler                    # macOS
```

Windows: install Poppler and put its `bin/` on `PATH`. Note that Git for
Windows ships an xpdf build of `pdftotext` **without** the `-bbox` flag; the
layout checker skips past it to any Poppler further along `PATH`.

### LaTeX — for compiling the CV and statements

- **Windows:** [MiKTeX](https://miktex.org/download)
- **macOS:** [MacTeX](https://tug.org/mactex/)
- **Linux:** `sudo apt install texlive-full`, or the minimal set:

```bash
sudo apt install texlive-luatex texlive-xetex texlive-latex-extra \
                 texlive-fonts-extra texlive-fonts-recommended
```

`texlive-fonts-extra` is **not optional**: it carries both `fontawesome5`
(the CV dies without it under lualatex) and **Carlito**, the house font.

The CV compiles with **lualatex**; `pdflatex` often fails on modern MiKTeX
with `fontawesome5` font-expansion errors. The statements compile with
**xelatex**, because `statement.cls` requires `fontspec`.

#### Minimal TeX (TinyTeX / BasicTeX)

```bash
tlmgr install moderncv fontawesome5 fontawesome6 academicons import \
  luatexbase pgf titlesec textpos xltxtra xunicode cite realscripts \
  needspace setspace fancyhdr microtype
```

Make sure the TeX binary directory is on `PATH` first, and persist it —
otherwise every new terminal reports `command not found: lualatex` even
though the install succeeded.

## 2. Smoke tests

```bash
cd cv && lualatex -interaction=nonstopmode -halt-on-error main_example.tex && cd ..
cd statements && xelatex -interaction=nonstopmode -halt-on-error sop_example.tex && cd ..

python3 tools/verify_pdf.py cv/main_example.pdf --pages 2 --min-chars 100
python3 tools/verify_layout.py cv/main_example.pdf
pdffonts statements/sop_example.pdf      # must show Carlito only
```

If `pdffonts` shows **Calibri-Bold** for the statement, you have a partial
Calibri install. The class already prefers Carlito for exactly this reason —
if you have edited it to ask for Calibri first, undo that: a bold-only install
silently sets the whole statement in bold, and it compiles.

## 3. Portal CLIs

```bash
python3 tools/install_portal_clis.py
```

Discovers every `.agents/skills/*/cli/package.json` and installs it. A portal
added by `/add-portal` is picked up without editing anything.

Test one live:

```bash
bun run .agents/skills/daad-programmes-search/cli/src/cli.ts \
  search --level masters --query "artificial intelligence" --limit 3 --format table
```

## 4. Repo self-checks

```bash
pip install pyyaml
python3 tools/lint_skills.py        # skill/command frontmatter and structure
python3 tools/security_guards.py    # permissions, gitignore, manifests
python3 -m unittest discover -s tests -t . -v
```

## 5. Your turn

```bash
python3 tools/docs_checklist.py inventory
```

Then open the folder in Claude Code and run `/setup`. See the
[README](README.md#what-you-need-to-give-it) for the full list of what to
supply.
