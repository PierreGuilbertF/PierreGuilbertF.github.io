#!/usr/bin/env python3
"""Generate matching HTML and LaTeX CVs from data/cv.json (Python standard library)."""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cv = json.loads((ROOT / 'data/cv.json').read_text())
def h(s):
    return escape(s, quote=True)
def tex(s):
    replacements = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(replacements.get(c, c) for c in s)
def pairs_html(items):
    return '<dl>' + ''.join(f'<div><dt>{h(k)}</dt><dd>{h(v)}</dd></div>' for k,v in items) + '</dl>'

jobs = ''.join(f'''<article class="job"><div class="job-heading"><h3>{h(j['company'])} <span>{h(j['role'])}</span></h3><p>{h(j['location'])} · {h(j['dates'])}</p></div><ul>{''.join('<li>'+h(b)+'</li>' for b in j['bullets'])}</ul></article>''' for j in cv['experience'])
education = '<ul class="education">' + ''.join(f'<li><div><strong>{h(title)}</strong><span>{h(school)}</span></div><time>{year}</time></li>' for title,school,year in cv['education']) + '</ul>'
html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Curriculum Vitae | {h(cv['name'])}</title>
<meta name="description" content="Pierre Guilbert's curriculum vitae: computer vision, machine learning, and mathematical modelling.">
<link rel="stylesheet" href="cv.css">
</head>
<body>
<main>
<nav aria-label="Page navigation"><a href="index.html">← Home</a><div><a href="output/pdf/cv.pdf">Download PDF</a><a href="cv.tex" download>LaTeX source</a></div></nav>
<header><img class="profile-photo" src="profile_picture.png" alt="Portrait of Pierre Guilbert" width="836" height="852"><div class="header-copy"><p class="eyebrow">Curriculum Vitae</p><h1>{h(cv['name'])}</h1><p class="headline">{h(cv['headline'])}</p>
<address><span>{h(cv['location'])}</span><a href="mailto:{h(cv['email'])}">{h(cv['email'])}</a><a href="tel:+41786576581">{h(cv['phone'])}</a><a href="{h(cv['github'])}">GitHub</a><a href="{h(cv['linkedin'])}">LinkedIn</a></address></div></header>
<section class="summary" aria-label="Profile">{''.join('<p>'+h(p)+'</p>' for p in cv['summary'])}</section>
<section><h2>Experience</h2>{jobs}</section>
<section><h2>Skills</h2>{pairs_html(cv['skills'])}</section>
<section><h2>Education</h2>{education}</section>
<section><h2>Personal Interests</h2>{pairs_html(cv['interests'])}</section>
<footer><a href="output/pdf/cv.pdf">Download this CV as a PDF</a></footer>
</main>
</body>
</html>
'''
(ROOT / 'cv.html').write_text(html)

preamble = r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=14mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{graphicx}
\usepackage{xcolor}
\definecolor{accent}{HTML}{235D69}
\definecolor{ink}{HTML}{202B35}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{hyperref}
\hypersetup{colorlinks=true,urlcolor=accent,pdftitle={Pierre Guilbert - Curriculum Vitae},pdfauthor={Pierre Guilbert}}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{3pt}
\setlist[itemize]{leftmargin=12pt,itemsep=1pt,topsep=2pt,parsep=0pt}
\titleformat{\section}{\sffamily\large\color{accent}}{}{0pt}{}[\vspace{3pt}\titlerule]
\titlespacing*{\section}{0pt}{8pt}{5pt}
\newcommand{\entry}[2]{\textbf{#1}: #2\par}
\begin{document}
\color{ink}
\begin{minipage}[t]{0.80\textwidth}
\vspace{0pt}
{\sffamily\fontsize{27}{30}\selectfont Pierre Guilbert}\par
{\sffamily\color{accent} Computer Vision, Machine Learning \& Mathematical Modelling}\par
'''
lines = [preamble, tex(cv['location']) + r'\par \href{mailto:' + cv['email'] + '}{' + tex(cv['email']) + r'} \enspace | \enspace \href{tel:+41786576581}{' + tex(cv['phone']) + r'}\par', r'\href{' + cv['github'] + r'}{GitHub} \enspace | \enspace \href{' + cv['linkedin'] + r'}{LinkedIn}\par\vspace{3pt}']
lines += [r'\end{minipage}\hfill', r'\begin{minipage}[t]{0.16\textwidth}', r'\vspace{0pt}', r'\includegraphics[width=\linewidth]{profile_picture.png}', r'\end{minipage}\par\vspace{5pt}']
lines += [tex(p) + r'\par' for p in cv['summary']]
lines += [r'\section{Experience}']
for job in cv['experience']:
    lines += [r'\textbf{' + tex(job['company']) + r'} --- ' + tex(job['role']) + r'\hfill {\small ' + tex(job['dates']) + r'}\par', r'{\small\itshape ' + tex(job['location']) + r'}\vspace{-3pt}', r'\begin{itemize}']
    lines += [r'\item ' + tex(b) for b in job['bullets']]
    lines += [r'\end{itemize}']
lines += [r'\section{Skills}']
lines += [r'\entry{' + tex(k) + '}{' + tex(v) + '}' for k,v in cv['skills']]
lines += [r'\section{Education}']
lines += [r'\textbf{' + tex(title) + r'} --- ' + tex(school) + r'\hfill ' + year + r'\par' for title,school,year in cv['education']]
lines += [r'\section{Personal Interests}']
lines += [r'\entry{' + tex(k) + '}{' + tex(v) + '}' for k,v in cv['interests']]
lines += [r'\end{document}']
(ROOT / 'cv.tex').write_text('\n'.join(lines) + '\n')
print('Generated cv.html and cv.tex')
