Overleaf project: IEEE two-column journal paper (IEEEtran), about 31 pages, with a separate supplement (about 10 pages)

Lesion-Faithful Bone Suppression from Chest CT Projections: Counterfactual Auditing and Gains for Focal Lesion Detection and
Classification in Chest Radiographs
(Study I: lesion-faithful bone suppression, counterfactual audit, downstream detection and classification;
 Study II: multi-stream fusion with capacity-matched controls)

Compile
  Upload the zip as a new Overleaf project (New Project > Upload Project).
  Menu > Compiler: pdfLaTeX. Main document: main.tex. No BibTeX run is needed: the reference list is frozen in
  sections/references.tex (thebibliography, numbered in order of first citation).
  Supplement: set Menu > Main document to supplementary.tex and compile (uses the same tables/ and figures/).

Files
  main.tex                       preamble, title, author block, structured abstract, index terms; inputs the sections
  sections/introduction.tex      I    Introduction (Fig. 1)
  sections/related_work.tex      II   Related Work and Motivation (Table I, comparison with prior studies)
  sections/methods.tex           III  Materials and Methods (notation, data and preprocessing, Study I, downstream models,
                                      Study II, external validation, statistics)
  sections/algorithm.tex              Algorithm 1 (input by methods.tex)
  sections/results.tex           IV   Experimental Results (Table of all hypotheses and outcomes first)
  sections/discussion.tex        V    Discussion (limitations in V-D)
  sections/conclusion.tex        VI   Conclusion
  sections/appendix.tex               Appendix A: v1 training images rendered from LIDC-IDRI
  sections/backmatter.tex             acknowledgment, ethics, data and code availability, declarations
  sections/references.tex             frozen reference list
  supplementary.tex              analysis notes and corrections (S1), Tables S1-S10, Figures S1-S7
  tables/*.tex                   generated result tables (do not retype numbers; regenerate them in the project repository)
  figures/*.pdf, *.png           figures, drawn at journal widths (88 mm single, 180 mm double) with 8 pt text
  refs.bib, vancouver-doi.bst, tools/freeze_refs.py   only needed to regenerate the reference list (see below)

Supplementary numbers
  The main text cites supplementary items by number (Supplementary Table S1 ... S10, Fig. S1 ... S7, Section S1). They follow the
  order of the floats in supplementary.tex; if you reorder or add floats there, update the citations in the main text.

Replacing a figure with your own drawing (for example a draw.io export)
  Export the drawing as PDF (File > Export as > PDF, "Crop" ticked, at the intended print width) and save it under the same file
  name in figures/, for example figures/fig_tmi_workflow.pdf (Fig. 1), figures/fig_tmi_architecture.pdf (Fig. 2) or
  figures/fig_data_pipeline_tmi.pdf (data preprocessing). Keep text at 8 pt or larger at print size, and keep the rule that no
  image of VinDr-RibCXR, JSRT, VinBigData, Node21, BDCXR-3257 or anything derived from CT-RATE appears in a figure.

Adding or removing a citation
  1. In main.tex replace  \input{sections/references}  by
       \bibliographystyle{vancouver-doi}
       \bibliography{refs}
  2. Compile (Overleaf runs BibTeX). Either keep it this way, or freeze the list again: download main.bbl and run
     python tools/freeze_refs.py main.bbl sections/references.tex   (fixes two style quirks of vancouver.bst), then undo step 1.

Still to fill in before submission (red [TODO: ...] markers)
  journal name; the other authors and affiliations; corresponding author and e-mail; funding and colleagues; CRediT statement;
  competing interests; confirm the generative-AI declaration against the actual use.

Page budget
  31 pages including references (main.tex) at the IEEE journal layout. The target was 30-40 pages; to lengthen it, Supplementary
  Tables S9-S10 and Figures S1, S6-S7 were written for the main text and can move back into results.tex with their captions.
