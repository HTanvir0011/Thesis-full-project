"""Freeze the BibTeX output (main.bbl) as sections/references.tex, a plain thebibliography block, with two style fixes."""
import sys
bbl, out = sys.argv[1], sys.argv[2]
t = open(bbl, encoding="utf-8").read()
n_items = t.count("\\bibitem{")
t = t.replace("et~al..", "et~al.")  # vancouver.bst adds a second period after "et al." in @misc entries
note = "\\newblock Preprint; no journal reference listed on arXiv on 2026-10-29.\n"
assert t.count(note) == 1
t = t.replace(note, "\\newblock Preprint.\n")
head = ("% Reference list frozen from BibTeX (refs.bib, style vancouver-doi.bst), numbered in order of first citation.\n"
        "% To regenerate after adding citations: in main.tex, replace \\input{sections/references} by\n"
        "% \\bibliographystyle{vancouver-doi} \\bibliography{refs}, compile, and run tools/freeze_refs.py on main.bbl.\n")
open(out, "w", encoding="utf-8", newline="\n").write(head + t)
assert t.count("\\bibitem{") == n_items and ".." not in t.replace("...", "")
print("references:", n_items)
