Overleaf project: manuscript for Medical Image Analysis (Elsevier elsarticle, one column), about 99 pages including references

Explainable and hallucination-aware cross-modality learning from chest CT for X-ray disease classification:
lesion-faithful bone suppression and Swin transformer knowledge transfer
(Study I: bone suppression and lesion audit; Study II: bone-suppressed classifier inputs; Study III: CT-to-X-ray distillation)

Compile
  Upload overleaf_submission.zip as a new Overleaf project (New Project > Upload Project).
  Menu > Compiler: pdfLaTeX. Main document: main.tex. Overleaf runs BibTeX automatically.
  Supplementary material: set Menu > Main document to supplementary.tex and compile (uses the same tables/ and figures/).

Files
  main.tex            preamble, title page, abstract, keywords, declarations; inputs the sections in order
  supplementary.tex   supplementary material: deviations from the analysis plans, extra results of Studies II and III
                      (cited in the main text as Supplementary Section S1, Tables S1-S11 and Figures S1-S13; their numbers
                      follow the order of the floats in supplementary.tex, so keep that order or update the citations)
  sections/*.tex      one file per section (introduction ... conclusion, appendix); edit text here
                      sections/claim_checklist.tex is not compiled: it lists where each CLAIM 2024 item is addressed,
                      as a guide for filling the official checklist form at submission
  tables/*.tex        generated tables (do not retype numbers; regenerate them in the project repository)
  figures/*.pdf       figures (vector PDF, drawn at journal column widths); PNG copies for some panels
  refs.bib            bibliography (plainnat author-year style, natbib commands \citep and \citet)
  highlights.txt      highlights, each at most 85 characters (Elsevier uploads these as a separate file)

Still to fill in before submission (red [TODO: ...] markers and the author block in main.tex)
  author names, affiliations and corresponding address; CRediT statement; competing interests;
  confirm the generative-AI declaration against the actual use; funding and colleagues.

Page budget
  The main PDF is about 99 pages at 12 pt and 1.5 line spacing (references single-spaced). It passed the earlier 90-page target
  when the exploratory site calibration (SAP_v5) and the data-preprocessing figures and table were added; to shorten it, move
  secondary material (for example Tables 5-7 or the appendix tables) to supplementary.tex rather than shrinking fonts or spacing.

Rebuild after a change in the repository
  python tools/xm_tables.py && python tools/fig_v4.py   (Study III tables and figures)
  python tools/pack_overleaf.py                          (copies the referenced tables and figures and writes overleaf_submission.zip)
