# Pierre Guilbert

Personal website for https://pierreguilbertf.github.io/.

- `index.html`: homepage, linking to the CV and downloadable PDF.
- `cv.html` and `cv.css`: responsive HTML CV.
- `cv.tex`: standalone LaTeX source.
- `output/pdf/cv.pdf`: PDF compiled from the LaTeX source.
- `data/cv.json`: shared content for the HTML and LaTeX versions.

## Update the CV

Edit `data/cv.json`, then run:

```sh
python3 scripts/build_cv.py
tectonic cv.tex --outdir output/pdf
```

The generator uses only Python's standard library. Compilation requires
[Tectonic](https://tectonic-typesetting.github.io/), which downloads LaTeX
packages on its first run. Commit the regenerated HTML, LaTeX, and PDF together.

## Publish

Push changes to the branch configured in GitHub Pages. In GitHub, open
**Settings → Pages**, choose **Deploy from a branch**, then **main** and
**/(root)**. The site needs no build step.

## Mathematical notes

`notes.html` lists the notes. The Flow Matching note lives in
`notes/flow-matching-generalization/`, alongside its unchanged original PDF,
LaTeX source and referenced media. To regenerate its HTML after editing the
copied LaTeX source, install Pandoc and run:

```sh
python3 scripts/build_flow_matching_note.py
```

MathJax is served locally from `assets/vendor/`; equation rendering does not
require a third-party CDN.

## Mathematical Knowledge Map

The map is a static page in `mathematical-knowledge-map/`. Its JSON data,
graph layout and viewer are imported from the Math Mapping application's
existing export. To refresh them after regenerating that export:

```sh
python3 scripts/build_math_map.py /path/to/math_mapping/code/output/mathematics.html
```

The importer removes local absolute paths. Commit the regenerated files
alongside the page and its stylesheet. Visitors do not need Python.
