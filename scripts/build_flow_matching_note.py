#!/usr/bin/env python3
"""Convert the original note to HTML without editorial changes. Requires Pandoc."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'notes/flow-matching-generalization'
source = (OUT / 'FlowMatchingOverfitting.tex').read_text()
macros = '\n'.join(line for line in source.splitlines() if line.startswith((r'\newcommand', r'\DeclareMathOperator')))
body = source.split(r'\maketitle', 1)[1].split(r'\end{document}', 1)[0]
body = re.sub(r'(?m)(?<!\\)%.*$', '', body)
bib = re.search(r'\\begin\{thebibliography\}\{99\}(.*?)\\end\{thebibliography\}', body, re.S)
entries = re.findall(r'\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\Z)', bib.group(1), re.S)
numbers = {key: i for i, (key, _) in enumerate(entries, 1)}
refs = {}
section = subsection = figure = 0
for match in re.finditer(r'\\(section|subsection)\{[^}]+\}|\\begin\{figure\}|\\label\{([^}]+)\}', body[:bib.start()]):
    if match.group(1) == 'section': section += 1; subsection = 0; current = str(section)
    elif match.group(1) == 'subsection': subsection += 1; current = f'{section}.{subsection}'
    elif match.group(0).startswith(r'\begin'): figure += 1; current = str(figure)
    elif not match.group(2).startswith('eq:'): refs[match.group(2)] = current
bibliography = r'\section*{References}' + '\n' + r'\begin{enumerate}' + '\n'
bibliography += '\n'.join(r'\item\label{ref:' + key + '} ' + text.strip() for key, text in entries)
bibliography += '\n' + r'\end{enumerate}'
body = body[:bib.start()] + bibliography + body[bib.end():]
body = re.sub(r'\\cite\{([^}]+)\}', lambda m: ', '.join(r'\href{\#ref:' + key + '}{[' + str(numbers[key]) + ']}' for key in m.group(1).split(',')), body)
body = re.sub(r'\\ref\{([^}]+)\}', lambda m: r'\href{\#' + m.group(1) + '}{' + refs[m.group(1)] + '}', body)
# Preserve the source text but omit print-only placement commands.
body = body.replace(r'\FloatBarrier', '')
converted = subprocess.run(['pandoc', '-f', 'latex', '-t', 'html5', '--mathjax', '--shift-heading-level-by=1', '--number-sections'], input=macros+'\n'+body, text=True, capture_output=True, check=True).stdout
media = {
 'overfit/figures/spiral_online_note_preview.pdf': 'spiral_online_note_preview.png',
 'overfit/figures/spiral_density.pdf': 'spiral_density.png',
 'overfit/figures/references/nakkiran_model_double_descent.png': 'nakkiran_model_double_descent.png',
 'overfit/figures/references/nakkiran_epoch_double_descent.png': 'nakkiran_epoch_double_descent.png',
 'overfit/fixed_dataset_longer/visualisations_975/figures/fixed_spiral_losses.png': 'fixed_spiral_losses.png',
 'overfit/fixed_dataset_longer/visualisations_975/figures/fixed_spiral_endpoints.png': 'fixed_spiral_endpoints.png',
}
for old, new in media.items(): converted = converted.replace(old, 'media/'+new)
converted = re.sub(r'<embed src="([^"]+)"([^>]*)/>', r'<img src="\1"\2 alt="Spiral probability density" loading="lazy">', converted)
converted = re.sub(r'run:overfit/(?:figures|fixed_dataset_longer/visualisations_975/figures)/([^"\s]+)', r'media/\1', converted)
# The first preview becomes a player, in exactly the same position.
converted = re.sub(r'<p><a\s+href="media/spiral_flow_matching_online_975_particles.mp4">.*?</a></p>', '<video controls playsinline muted loop preload="metadata" poster="media/spiral_online_note_preview.png" aria-label="Gaussian-to-spiral transport of 975 particles"><source src="media/spiral_flow_matching_online_975_particles.mp4" type="video/mp4"><a href="media/spiral_flow_matching_online_975_particles.mp4">Open the particle video (MP4)</a></video>', converted, count=1, flags=re.S)
# Resolve print figure numbers and make bibliography entries direct citation targets.
count = 0
def caption(m):
    global count
    count += 1
    return f'<figcaption><strong>Figure {count}.</strong> '
converted = re.sub(r'<figcaption>', caption, converted)
converted = converted.replace('<ol>\n<li><p><span id="ref:', '<ol class="bibliography">\n<li><p><span id="ref:')
# Add playable versions of the three videos beside their unchanged source links.
players = '<div class="video-grid">'
for name, title in [('generalisation','Generalisation'),('memorisation_onset','Overfitting begins'),('late_training','Memorisation')]:
    players += f'<div><h3>{title}</h3><video controls playsinline muted loop preload="metadata" poster="media/{name}.jpg" aria-label="{title}"><source src="media/fixed_spiral_{name}.mp4" type="video/mp4"><a href="media/fixed_spiral_{name}.mp4">{title}</a></video></div>'
players += '</div>'
pattern = r'(<figure id="fig:finite-data-transport".*?</figure>)'
converted = re.sub(pattern, lambda m: m.group(1)+players, converted, flags=re.S)
# Give every static figure meaningful alternative text without changing captions.
alts = {'nakkiran_model_double_descent.png':'Model-width double descent for ResNet18 on CIFAR-10', 'nakkiran_epoch_double_descent.png':'Training-time double descent for ResNet18 on CIFAR-10', 'fixed_spiral_losses.png':'Training and validation losses for the fixed 500/500 split', 'fixed_spiral_endpoints.png':'Transported densities at three training checkpoints'}
for file, alt in alts.items():
    converted = re.sub(r'<img\s+src="media/'+re.escape(file)+r'"([^>]*)>', lambda m: '<img src="media/'+file+'"'+re.sub(r'\s+alt="[^"]*"','',m.group(1))+' alt="'+alt+'" loading="lazy">', converted)
page = '''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>When Generative Models Do Not Exhibit Double Descent: A Flow Matching Example | Pierre Guilbert</title>
<meta name="author" content="Pierre Guilbert">
<meta name="description" content="A mathematical note on generalisation and memorisation in Flow Matching, with two-dimensional experiments and particle videos.">
<link rel="stylesheet" href="../../cv.css"><link rel="stylesheet" href="../note.css">
<script>window.MathJax={tex:{tags:'ams'},svg:{fontCache:'local'}};</script>
<script defer src="../../assets/vendor/mathjax-tex-svg.js"></script>
</head><body><main>
<nav aria-label="Page navigation"><a href="../../index.html">← Home</a><a href="../../notes.html">Mathematical Notes</a></nav>
<article><header class="note-header"><p class="eyebrow">Mathematical Notes · Flow Matching generalization</p>
<h1>When Generative Models Do Not Exhibit Double Descent: A Flow Matching Example</h1>
<p class="byline"><a href="https://orcid.org/0009-0002-1582-4435" rel="author">Pierre Guilbert</a> · <a href="mailto:spguilbert@gmail.com">spguilbert@gmail.com</a></p>
<p class="downloads"><a href="FlowMatchingOverfitting.pdf">Original PDF</a><a href="FlowMatchingOverfitting.tex" download>LaTeX source</a></p></header>
'''+converted+'''</article></main></body></html>\n'''
(OUT / 'index.html').write_text(page)
assert count == 5, count
assert len(entries) == 32, len(entries)
print(f'Converted {count} figures and {len(entries)} references.')
