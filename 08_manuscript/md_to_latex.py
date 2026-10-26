"""Convert the Markdown manuscript drafts into LaTeX section files for the Overleaf project.

Splits ``methods_draft.md`` (Sections 2-4) and ``results_discussion_draft.md``
(Sections 5-6) at their top-level headings, converts each with pandoc, and
then turns the draft citations ``[Author, year]`` into natbib ``\\citep`` /
``\\citet`` commands. Drafting notes and the Markdown reference list are
dropped (the bibliography is ``latex_source/references.bib``).

Usage (from the repository root):
    python 08_manuscript/md_to_latex.py
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "latex_source" / "sections"

#: Markdown section heading (without its number) -> (file, label)
SECTIONS = {
    "Data": ("data.tex", "sec:data"),
    "Parallax correction method": ("method.tex", "sec:method"),
    "Validation design": ("validation.tex", "sec:validation"),
    "Results": ("results.tex", "sec:results"),
    "Discussion": ("discussion.tex", "sec:discussion"),
}

#: Draft citation text -> LaTeX
CITATIONS = [
    (r"\[SAC, 2014\]", r"\\citep{sac2014}"),
    (r"\[Hou et al\., 2014\]", r"\\citep{hou2014}"),
    (r"\[Iguchi & Meneghini, 2026\]", r"\\citep{gpm2aku_v08}"),
    (r"Iguchi et al\. \[2021\]", r"\\citet{iguchi2021}"),
    (r"\[Natural Earth\]", r"\\citep{naturalearth}"),
    (r"\[Anderson et al\., 1986\]", r"\\citep{anderson1986}"),
    (r"\[Hersbach et al\., 2020; C3S, 2018\]", r"\\citep{hersbach2020,c3s2018}"),
    (r"\[Farr et al\., 2007\]", r"\\citep{farr2007}"),
    (r"\[NIMA, 2000\]", r"\\citep{nima2000}"),
    (r"\[Snow et al\.\]", r"\\citep{pyproj}"),
    (r"\[Raspaud et al\., 2018\]", r"\\citep{raspaud2018}"),
    (r"\[Vicente et al\., 2002\]", r"\\citep{vicente2002}"),
    (r"Bieliński \[2020\]", r"\\citet{bielinski2020}"),
    (r"\[Lam et al\., 2015\]", r"\\citep{lam2015}"),
    (r"Vicente et al\. \(2002\)", r"\\citet{vicente2002}"),
    (r"Bieliński \(2020\)", r"\\citet{bielinski2020}"),
    (r"ISRO's data-quality reports already measure", r"ISRO's data-quality reports \\citep{mosdac_dqe2020} already measure"),
    (r"satpy offers an open-source", r"satpy \\citep{satpy_parallax} offers an open-source"),
    (r"the GOES Hydro-Estimator has applied", r"the GOES Hydro-Estimator \\citep{scofield2003} has applied"),
]

#: Figure and table mentions -> cross-references
REFERENCES = [
    (r"\(Fig\. (\d)\)", r"(Fig.~\\ref{fig:\1})"),
    (r"Fig\. (\d)", r"Fig.~\\ref{fig:\1}"),
    (r"Table (\d)", r"Table~\\ref{tab:\1}"),
    (r"Section (\d)\.(\d)", r"Section~\\ref{sec:\1.\2}"),
    (r"Section (\d)", r"Section~\\ref{sec:\1}"),
    (r"Sections 2–4", r"Sections~\\ref{sec:data}--\\ref{sec:validation}"),
]


def split_sections(md):
    """Top-level '## N Title' blocks of a draft, keyed by title, without notes or references."""
    md = md.split("## Notes for revision")[0].split("## References")[0]
    parts = re.split(r"^## \d+ (.+)$", md, flags=re.M)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts), 2)}


def blank_line_before_lists(md):
    """Pandoc starts a list only after a blank line; the drafts sometimes omit it."""
    out = []
    for line in md.split("\n"):
        is_item = re.match(r"\s*([-*]|\d+\.) ", line)
        if is_item and out and out[-1].strip() and not re.match(r"\s*([-*]|\d+\.) |\s{2,}\S", out[-1]):
            out.append("")
        out.append(line)
    return "\n".join(out)


def to_latex(md):
    md = blank_line_before_lists(md)
    # Citations first, as raw LaTeX: pandoc passes raw LaTeX through, but would escape the brackets.
    for pat, rep in CITATIONS:
        md = re.sub(pat, rep, md)
    tex = subprocess.run(["pandoc", "-f", "markdown", "-t", "latex", "--wrap=none", "--shift-heading-level-by=-1"],
                         input=md, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    # Subsection headings like "5.4 Effect of ..." -> number dropped, label sec:5.4.
    tex = re.sub(r"\\subsection\{(\d+)\.(\d+) (.+?)\}\\label\{[^}]*\}",
                 lambda m: f"\\subsection{{{m.group(3)}}}\\label{{sec:{m.group(1)}.{m.group(2)}}}", tex)
    for pat, rep in REFERENCES:
        tex = re.sub(pat, rep, tex)
    # Tables are short: print the header and caption once, not again on a continuation page.
    tex = tex.replace("\\endhead", "\\endfirsthead")
    # ...and keep them on one page: "\\*" forbids a page break after a row.
    tex = re.sub(r"\\begin\{longtable\}.*?\\end\{longtable\}",
                 lambda m: re.sub(r"\\\\(?=\s*\n)", r"\\\\*", m.group(0)), tex, flags=re.S)
    # Markdown section separators ("---") would print as rules.
    tex = tex.replace("\\begin{center}\\rule{0.5\\linewidth}{0.5pt}\\end{center}\n", "")
    # "**Table N.** Caption" paragraphs become captions inside the longtable that follows them.
    # Numbered captions are Results tables (tab:1-3); lettered ones (R, S) are Methods tables.
    tex = re.sub(r"\\textbf\{Table(?:~\\ref\{tab:(\d)\}| ([A-Z]))\.\} (.+?)\n\n(\\begin\{longtable\}.*?)(\\toprule)",
                 lambda m: f"{m.group(4)}\\caption{{{m.group(3)}}}\\label{{tab:{m.group(1) or m.group(2)}}}\\\\\n{m.group(5)}",
                 tex, flags=re.S)
    return tex


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    blocks = {}
    for name in ("methods_draft.md", "results_discussion_draft.md"):
        blocks.update(split_sections((HERE / name).read_text(encoding="utf-8")))
    numbers = {"Data": 2, "Parallax correction method": 3, "Validation design": 4, "Results": 5, "Discussion": 6}
    for title, (fname, label) in SECTIONS.items():
        if title not in blocks:
            raise KeyError(f"section {title!r} not found in the drafts")
        body = to_latex(blocks[title])
        tex = f"\\section{{{title}}}\n\\label{{{label}}}\n\\label{{sec:{numbers[title]}}}\n\n{body}"
        (OUT / fname).write_text(tex, encoding="utf-8", newline="\n")
        print(f"wrote {OUT / fname}")


if __name__ == "__main__":
    main()
