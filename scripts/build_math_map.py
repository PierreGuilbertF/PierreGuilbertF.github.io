#!/usr/bin/env python3
"""Import an existing Math Mapping HTML/JSON export into the static website."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
class Scripts(HTMLParser):
    def __init__(self):
        super().__init__();self.scripts=[];self.current=None
    def handle_starttag(self,tag,attrs):
        if tag=='script':self.current=''
    def handle_data(self,text):
        if self.current is not None:self.current+=text
    def handle_endtag(self,tag):
        if tag=='script' and self.current is not None:
            self.scripts.append(self.current);self.current=None

def public_data(value):
    if isinstance(value,dict):return {k:public_data(v) for k,v in value.items()}
    if isinstance(value,list):return [public_data(v) for v in value]
    if isinstance(value,str) and value.startswith('/'):
        marker='/cartography/'
        return 'cartography/'+value.split(marker,1)[1] if marker in value else Path(value).name
    return value

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('export',type=Path,help='Path to the generated mathematics.html')
a=p.parse_args();source=a.export.read_text();parsed=Scripts();parsed.feed(source)
library=next(s for s in parsed.scripts if 'plotly.js v' in s[:200])
init=next(s for s in parsed.scripts if 'window.PLOTLYENV' in s[:200])
viewer=next(s for s in parsed.scripts if s.lstrip().startswith('const DATA ='))
viewer=re.sub(r'\A\s*const DATA = .*?;\s*\n(?=const plot)', '',viewer,flags=re.S)
# Render math safely: catalogue text is inserted through textContent.
viewer=viewer.replace("  element('pre', plain(node.statement), statement);", "  statement.open = true;\n  element('div', plain(node.statement), statement, 'statement');")
viewer=viewer.replace("  const node = nodes.get(id);\n  const badge", "  if (window.MathJax?.typesetClear) MathJax.typesetClear([details]);\n  const node = nodes.get(id);\n  const badge")
viewer=viewer.replace("  element('pre', clauses.map(plain).join('\\n\\n'), raw);", "  element('pre', clauses.map(plain).join('\\n\\n'), raw);\n  if (window.MathJax?.startup?.promise) {\n    MathJax.startup.promise.then(() => {\n      if (selected === id) return MathJax.typesetPromise([statement]);\n    }).catch(() => {});\n  }")
viewer=viewer.replace("  selected = id;", "  selected = id;\n  history.replaceState(null, '', '#' + encodeURIComponent(id));")
viewer=viewer.replace("introduction();\n", "introduction();\n",1)
viewer += "\nconst initialId = decodeURIComponent(location.hash.slice(1));\nif (nodes.has(initialId)) select(initialId);\n"
# Reset must also clear the sharable selection.
viewer=viewer.replace("  selected = null; search.value = ''; status.textContent = '';", "  selected = null; history.replaceState(null, '', location.pathname); search.value = ''; status.textContent = '';")
viewer=viewer.replace("showNames ? safeLabel(shortName(n)) : n.id", "showNames || n.id === selected ? safeLabel(shortName(n)) : ''")
start=viewer.index('function introduction() {')
end=viewer.index('\nfunction listConnections',start)
viewer=viewer[:start]+"""function introduction() {
  details.replaceChildren();
  element('div', 'EXPLORE THE MAP', details, 'eyebrow');
  element('h2', 'How concepts connect');
  element('p', 'Search for a concept or select a node to read its statement, follow its prerequisites and explore its bibliography.');
  element('h3', 'Reading the map');
  element('p', 'Blue: axioms. Green: definitions. Red: theorems. Shaded regions group concepts by subject.');
  element('p', 'Hover over a node to see its name. Select it to highlight its immediate connections.', details, 'muted');
}
"""+viewer[end:]
viewer=viewer.replace("const initialId = decodeURIComponent", "updateGraph();\nconst initialId = decodeURIComponent")
wrapped="""async function startMap() {
  const response = await fetch('data.json');
  if (!response.ok) throw new Error('Map data could not be loaded.');
  const DATA = await response.json();
  await window.mapReady;
"""+viewer+"""\n}
startMap().catch(error => {
  document.getElementById('search-status').textContent = 'The map could not load. Please refresh the page.';
  console.error(error);
});
"""
out=ROOT/'mathematical-knowledge-map';out.mkdir(exist_ok=True)
(ROOT/'assets/vendor/plotly.min.js').write_text(library)
init=init.replace('Plotly.newPlot(', 'window.mapReady = Plotly.newPlot(',1)
(out/'graph-init.js').write_text(init.rstrip()+'\n')
(out/'map.js').write_text(wrapped)
data=public_data(json.loads(a.export.with_suffix('.json').read_text()))
(out/'data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
print(f'Imported {len(data["nodes"])} concepts and {len(data["edges"])} links.')
