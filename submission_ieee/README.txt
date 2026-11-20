Overleaf project: IEEE two-column journal version (IEEEtran) of the combined manuscript

Explainable and hallucination-aware cross-modality learning from chest CT for X-ray disease classification:
lesion-faithful bone suppression and Swin transformer knowledge transfer
(Study I: bone suppression and lesion audit; Study II: bone-suppressed classifier inputs; Study III: CT-to-X-ray distillation)

Compile
  Upload the zip as a new Overleaf project (New Project > Upload Project).
  Menu > Compiler: pdfLaTeX. Main document: main.tex. No BibTeX run is needed: the reference list is frozen in
  sections/references.tex (thebibliography, numbered in order of first citation).

Files
  main.tex                 preamble, title, author block, structured abstract, index terms; inputs the sections in order
  sections/introduction.tex       I    Introduction
  sections/related_work.tex       II   Related Work and Motivation, Table I (comparison with prior studies)
  sections/methods.tex            III  A-C: problem formulation, data and preprocessing, Study I
  sections/algorithm.tex               Algorithm 1 (input by methods.tex)
  sections/methods2.tex           III  D-F: Study II, Study III, statistics
  sections/results.tex            IV   Experimental Results
  sections/discussion.tex         V    Discussion (limitations in V-C)
  sections/conclusion.tex         VI   Conclusion
  sections/backmatter.tex              appendix tables, acknowledgment, ethics, data and code availability, declarations
  sections/references.tex              frozen reference list
  tables/*.tex             generated result tables (do not retype numbers; regenerate them in the project repository)
  figures/*.pdf            figures, drawn at journal column widths (88 mm single, 180 mm double) with 8 pt text
  refs.bib, vancouver-doi.bst, tools/freeze_refs.py   only needed to regenerate the reference list (see below)

Adding or removing a citation
  1. In main.tex replace  \input{sections/references}  by
       \bibliographystyle{vancouver-doi}
       \bibliography{refs}
  2. Compile (Overleaf runs BibTeX). Either keep it this way, or freeze the list again: download main.bbl and run
     python tools/freeze_refs.py main.bbl sections/references.tex   (fixes two style quirks of vancouver.bst), then undo step 1.

Still to fill in before submission (red [TODO: ...] markers)
  journal name; the other authors and affiliations; corresponding author and e-mail; CRediT statement; competing interests;
  funding and colleagues; confirm the generative-AI declaration against the actual use.
