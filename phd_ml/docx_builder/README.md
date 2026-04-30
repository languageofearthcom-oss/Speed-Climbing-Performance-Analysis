# Phase 1 — Word Document Builder

Generates `phd_ml/phase1/PHASE1_METHODOLOGY.docx`, the bilingual (English + Persian) thesis-grade methodology document for advisor review.

## Why a separate folder

`build/` is a node-only toolchain. Keeping it isolated avoids polluting the Python package tree.

## How to regenerate

```bash
cd phd_ml/build
npm install        # pulls the `docx` package from npm
node build_phase1_docx.js
# → writes ../phase1/PHASE1_METHODOLOGY.docx
```

## What is in the document

* Cover page with project metadata
* Executive summary — English + Persian
* Auto-generated Table of Contents
* 10 numbered sections covering problem, methodology, validation, skill proxy, code architecture, outputs, limitations, references
* Appendix A — Key code excerpts
* Appendix B — Reproduction guide
* Appendix C — Bilingual sign-off checklist

## Skill provenance

Built using the official Anthropic `docx` skill (`anthropics/skills/docx`, aiScore 87) installed via `npx skillhub install`. The skill provides the `docx-js` recipe followed in `build_phase1_docx.js`.
