"""Build the PDF manual from the Markdown pages in ``docs/``.

The pages are joined in reading order, links between pages are turned into
links within the PDF, and pandoc renders the result with XeLaTeX (a table of
contents, numbered sections, one chapter per page).

Usage (from the repository root; needs pandoc and a TeX distribution with XeLaTeX):
    python docs/build_manual.py [-o docs/PyGeoParallax-IN_manual.pdf]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
PAGES = ("index", "installation", "quickstart", "cli", "python_api", "outputs", "troubleshooting",
         "concepts", "data", "validation", "unet", "development")
REPO = "https://github.com/bapallinaveen60/PyGeoParallax-IN/blob/main/"


def page_text(name):
    """One page, with its title as an anchored chapter and its links rewritten for a single document."""
    text = (HERE / f"{name}.md").read_text(encoding="utf-8")
    # Title: "# Something" -> "# Something {#page-name}".
    text = re.sub(r"\A# (.+)$", lambda m: f"# {m.group(1)} {{#page-{name}}}", text, count=1, flags=re.M)

    def link(m):
        label, target = m.group(1), m.group(2)
        if re.match(r"[a-z]+://|#|mailto:", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
        stem = Path(path).stem
        if path.endswith(".md") and Path(path).parent == Path(".") and stem in PAGES:
            return f"[{label}](#{anchor or 'page-' + stem})"
        # Files elsewhere in the repository: link to GitHub.
        clean = re.sub(r"^(\.\./)+", "", path)
        return f"[{label}]({REPO}{clean}{'#' + anchor if anchor else ''})"

    return re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)\s]+)\)", link, text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("-o", "--output", default=str(HERE / "PyGeoParallax-IN_manual.pdf"))
    args = ap.parse_args(argv)

    from importlib.metadata import PackageNotFoundError

    try:
        import pygeoparallax

        version = pygeoparallax.__version__
    except (ImportError, PackageNotFoundError):
        version = ""
    header = (f"---\ntitle: PyGeoParallax-IN\nsubtitle: User and developer manual"
              f"{', version ' + version if version else ''}\nauthor: Naveen Bapalli\n---\n\n")
    body = "\n\n".join(page_text(n) for n in PAGES)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "manual.md"
        src.write_text(header + body, encoding="utf-8")
        cmd = ["pandoc", str(src), "-o", str(Path(args.output).resolve()), "--pdf-engine=xelatex",
               "--toc", "--toc-depth=2", "--number-sections", "--top-level-division=chapter",
               "-V", "documentclass=report", "-V", "geometry:margin=2.3cm", "-V", "fontsize=10pt",
               "-V", "colorlinks=true", "-V", "linkcolor=blue", "-V", "urlcolor=blue",
               "-V", "mainfont=Cambria", "-V", "monofont=Consolas",
               "--highlight-style=tango", "--resource-path", str(HERE)]
        subprocess.run(cmd, check=True)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
