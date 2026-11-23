async function startMap() {
  const response = await fetch('data.json');
  if (!response.ok) throw new Error('Map data could not be loaded.');
  const DATA = await response.json();
  await window.mapReady;
const plot = document.getElementById('knowledge-graph');
const nodes = new Map(DATA.nodes.map(n => [n.id, n]));
const details = document.getElementById('details');
const search = document.getElementById('search');
const status = document.getElementById('search-status');
let selected = null;

const activeSections = () => new Set([...document.querySelectorAll('[data-section]:checked')].map(e => e.dataset.section));
const sectionNames = DATA.sections;
const activeCategories = () => new Set([...document.querySelectorAll('[data-category]:checked')].map(e => e.dataset.category));
const plain = text => text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*/g, '');
const shortName = node => node.label.split(' / ')[0];
const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const safeLabel = text => text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

const sections = [...new Set(DATA.nodes.map(n => n.section))];
const crossLinks = DATA.edges.filter(e => nodes.get(e.source).section !== nodes.get(e.target).section);
document.getElementById('counts').textContent = `${DATA.nodes.length} entries · ${DATA.edges.filter(e => e.layer === 'dependency').length} typed prerequisite links · ${crossLinks.length} links between chapters`;
for (const section of sections) {
  const label = document.createElement('label');
  const input = document.createElement('input');
  input.type = 'checkbox'; input.checked = true; input.dataset.section = section;
  const swatch = document.createElement('span');
  swatch.style.cssText = 'display:inline-block;width:12px;height:12px;border-radius:3px;opacity:.7';
  swatch.style.backgroundColor = DATA.domain_regions.find(r => r.section === section).color;
  swatch.setAttribute('aria-hidden', 'true');
  label.append(input, swatch, document.createTextNode(`${section} · ${sectionNames[section] || section}`));
  document.getElementById('sections').append(label);
}
for (const node of DATA.nodes) {
  const option = document.createElement('option');
  option.value = `${node.id} · ${shortName(node)}`;
  document.getElementById('entries').append(option);
}

function element(tag, text, parent = details, className = '') {
  const item = document.createElement(tag);
  item.textContent = text;
  if (className) item.className = className;
  parent.append(item);
  return item;
}

function introduction() {
  details.replaceChildren();
  element('div', 'EXPLORE THE MAP', details, 'eyebrow');
  element('h2', 'How concepts connect');
  element('p', 'Search for a concept or select a node to read its statement, follow its prerequisites and explore its bibliography.');
  element('h3', 'Reading the map');
  element('p', 'Blue: axioms. Green: definitions. Red: theorems. Shaded regions group concepts by subject.');
  element('p', 'Hover over a node to see its name. Select it to highlight its immediate connections.', details, 'muted');
}

function listConnections(title, edges, id, direction) {
  element('h3', `${title} · ${new Set(edges.map(e => e.source === id ? e.target : e.source)).size}`);
  if (!edges.length) { element('p', 'None recorded in this view.', details, 'muted'); return; }
  const grouped = new Map();
  for (const edge of edges) {
    const other = edge.source === id ? edge.target : edge.source;
    if (!grouped.has(other)) grouped.set(other, []);
    grouped.get(other).push(edge);
  }
  for (const [other, links] of grouped) {
    const node = nodes.get(other);
    const button = element('button', `${other} · ${shortName(node)}`, details, 'node-link');
    element('small', `${direction} ${[...new Set(links.map(e => e.kind))].join(', ')}`, button);
    button.title = links.flatMap(e => e.notes).map(plain).join('\n');
    button.addEventListener('click', () => select(other));
  }
}

function showDetails(id) {
  details.replaceChildren();
  if (window.MathJax?.typesetClear) MathJax.typesetClear([details]);
  const node = nodes.get(id);
  const badge = element('div', `${id} · ${node.kind}`, details, 'badge');
  badge.style.color = DATA.colors[node.category];
  element('h2', shortName(node));
  element('p', `${sectionNames[node.section] || node.section}`, details, 'muted');
  if (node.label.includes(' / ')) element('p', node.label.split(' / ').slice(1).join(' / '), details, 'muted');
  if (node.entry_type === 'hypothesis') element('p', 'Additional hypothesis. It is not asserted as a theorem of ZFC.', details, 'muted');
  const statement = element('details', '');
  element('summary', 'Statement and assumptions', statement);
  statement.open = true;
  element('div', plain(node.statement), statement, 'statement');
  const incoming = DATA.edges.filter(e => e.layer === 'dependency' && e.target === id);
  const outgoing = DATA.edges.filter(e => e.layer === 'dependency' && e.source === id);
  listConnections('Direct prerequisites', incoming, id, '→ this entry ·');
  if (document.getElementById('indirect').checked) {
    const direct = new Set(incoming.map(e => e.source));
    const indirect = [...ancestors(id)].filter(other => !direct.has(other)).sort();
    element('h3', `Indirect prerequisites · ${indirect.length}`);
    element('p', 'Computed from recorded direct links; these are inherited prerequisites, not additional direct proof claims.', details, 'muted');
    for (const other of indirect) {
      const button = element('button', `${other} · ${shortName(nodes.get(other))}`, details, 'node-link');
      button.addEventListener('click', () => select(other));
    }
  }
  listConnections('Used by', outgoing, id, 'this entry → ·');
  if (document.getElementById('context').checked) {
    listConnections('Context', DATA.edges.filter(e => e.layer === 'context' && (e.source === id || e.target === id)), id, 'Related ·');
  }
  const sources = element('details', '');
  sources.open = true;
  element('summary', 'Bibliography', sources);
  element('p', plain(node.reference), sources, 'reference');
  for (const citation of node.bibliography) {
    const source = DATA.bibliography[`${node.section}:${citation.source}`];
    element('p', `${source.authors.join(', ')} — ${source.title}`, sources, 'reference');
    element('p', plain(source.citation), sources, 'reference');
    element('p', plain(citation.locator) || 'General reference', sources, 'reference');
    element('p', citation.pages ? `Pages: ${citation.pages}` : 'Page locator not recorded', sources, 'muted');
    element('p', citation.verification === 'verified_locator' ? 'Locator checked' : 'Reading reference; exact locator not verified', sources, 'muted');
    for (const url of source.urls) {
      const link = element('a', 'Open source', sources, 'reference');
      link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      sources.append(document.createElement('br'));
    }
  }
  const raw = element('details', '');
  element('summary', 'Recorded links and qualifications', raw);
  const clauses = [...new Set(DATA.relations.filter(r => r.source === id).map(r => r.clause))];
  element('pre', clauses.map(plain).join('\n\n'), raw);
  if (window.MathJax?.startup?.promise) {
    MathJax.startup.promise.then(() => {
      if (selected === id) return MathJax.typesetPromise([statement]);
    }).catch(() => {});
  }
}

function ancestors(id) {
  const visited = new Set([id]);
  const pending = [id];
  while (pending.length) {
    const current = pending.pop();
    for (const dependency of nodes.get(current).direct_dependencies) {
      if (!visited.has(dependency.target)) {
        visited.add(dependency.target); pending.push(dependency.target);
      }
    }
  }
  visited.delete(id);
  return visited;
}

function segments(edges) {
  const x = [], y = [], seen = new Set();
  for (const e of edges) {
    const key = `${e.source}:${e.target}`;
    if (seen.has(key)) continue;
    seen.add(key);
    x.push(DATA.positions[e.source][0], DATA.positions[e.target][0], null);
    y.push(DATA.positions[e.source][1], DATA.positions[e.target][1], null);
  }
  return {x, y};
}

function updateGraph() {
  const categories = activeCategories();
  const enabledSections = activeSections();
  const visibleNode = id => categories.has(nodes.get(id).category) && enabledSections.has(nodes.get(id).section);
  const visibleEdges = DATA.edges.filter(e => visibleNode(e.source) && visibleNode(e.target));
  const showContext = document.getElementById('context').checked;
  const ancestry = selected && document.getElementById('indirect').checked ? ancestors(selected) : new Set();
  ancestry.add(selected);
  const isFocused = e => (e.source === selected || e.target === selected) ||
    (e.layer === 'dependency' && ancestry.has(e.source) && ancestry.has(e.target));
  const focused = visibleEdges.filter(e => (e.layer === 'dependency' || showContext) && isFocused(e));
  const neighbours = new Set(focused.flatMap(e => [e.source, e.target]));
  neighbours.add(selected);
  const base = segments(visibleEdges.filter(e => e.layer === 'dependency'));
  const context = segments(visibleEdges.filter(e => e.layer === 'context'));
  // Keep contextual links dotted even in a focused view.
  const highlight = segments(focused.filter(e => e.layer === 'dependency'));
  const showNames = document.getElementById('names').checked;
  const traces = [
    {...plot.data[0], x:base.x, y:base.y, opacity:selected ? .2 : 1},
    {...plot.data[1], x:context.x, y:context.y, visible:showContext, opacity:selected ? .45 : 1},
    {...plot.data[2], x:highlight.x, y:highlight.y},
    {...plot.data[3],
      x:DATA.nodes.map(n => visibleNode(n.id) ? DATA.positions[n.id][0] : null),
      y:DATA.nodes.map(n => visibleNode(n.id) ? DATA.positions[n.id][1] : null),
      text:DATA.nodes.map(n => showNames || n.id === selected ? safeLabel(shortName(n)) : ''),
      marker:{...plot.data[3].marker,
        opacity:DATA.nodes.map(n => !selected || neighbours.has(n.id) ? 1 : .13)},
      textfont:{...plot.data[3].textfont,
        color:DATA.nodes.map(n => !selected || neighbours.has(n.id) ? '#405066' : '#cbd5e1')},
    },
  ];
  // Only immediate selected connections need arrowheads. Ancestors remain
  // highlighted as lines, avoiding thousands of SVG annotations.
  const arrowEdges = selected ? [...new Map(focused.filter(e =>
    e.layer === 'dependency' && (e.source === selected || e.target === selected)
  ).map(e => [`${e.source}:${e.target}`, e])).values()] : [];
  const annotations = arrowEdges.map(edge => {
    const [x0,y0] = DATA.positions[edge.source], [x1,y1] = DATA.positions[edge.target];
    return {x:x0+.80*(x1-x0), y:y0+.80*(y1-y0),
      ax:x0+.63*(x1-x0), ay:y0+.63*(y1-y0),
      xref:'x', yref:'y', axref:'x', ayref:'y', text:'',
      showarrow:true, arrowhead:2, arrowsize:1, arrowwidth:1,
      arrowcolor:'#334155', opacity:1};
  });
  const showDomains = document.getElementById('domains').checked;
  const shapes = DATA.domain_regions.map(region => ({...region.shape,
    visible: showDomains && enabledSections.has(region.section) &&
      DATA.nodes.some(n => n.section === region.section && categories.has(n.category)),
  }));
  Plotly.react(plot, traces, {...plot.layout, annotations, shapes}, plot._context);
}

function select(id) {
  if (!nodes.has(id)) return;
  selected = id;
  history.replaceState(null, '', '#' + encodeURIComponent(id));
  document.querySelector(`[data-section="${nodes.get(id).section}"]`).checked = true;
  document.querySelector(`[data-category="${nodes.get(id).category}"]`).checked = true;
  search.value = `${id} · ${shortName(nodes.get(id))}`;
  status.textContent = `Selected ${id}. Its recorded connections are highlighted.`;
  showDetails(id); updateGraph();
}

function searchEntries() {
  const query = normalize(search.value.trim());
  if (!query) {
    selected = null; status.textContent = ''; introduction(); updateGraph(); return;
  }
  const id = search.value.match(/^[A-Z][A-Z0-9]*-[A-Z]+\d+/i)?.[0].toUpperCase();
  const matches = DATA.nodes.filter(n => normalize(`${n.id} ${n.label}`).includes(query));
  if (id && nodes.has(id)) select(id);
  else if (matches.length === 1) select(matches[0].id);
  else status.textContent = matches.length ? `${matches.length} matches. Choose an entry from the suggestions.` : 'No matching entry.';
}
search.addEventListener('change', searchEntries);
search.addEventListener('keydown', e => { if (e.key === 'Enter') searchEntries(); });
plot.on('plotly_click', event => { const id = event.points[0]?.customdata; if (id) select(id); });
document.querySelectorAll('[data-category], [data-section]').forEach(input => input.addEventListener('change', () => {
  if (selected && (!activeCategories().has(nodes.get(selected).category) || !activeSections().has(nodes.get(selected).section))) {
    selected = null; history.replaceState(null, '', location.pathname); search.value = ''; status.textContent = ''; introduction();
  }
  updateGraph();
}));
document.getElementById('names').addEventListener('change', updateGraph);
document.getElementById('domains').addEventListener('change', updateGraph);
document.getElementById('indirect').addEventListener('change', () => { if (selected) showDetails(selected); updateGraph(); });
document.getElementById('context').addEventListener('change', () => { if (selected) showDetails(selected); updateGraph(); });
document.getElementById('reset').addEventListener('click', () => {
  selected = null; history.replaceState(null, '', location.pathname); search.value = ''; status.textContent = '';
  document.querySelectorAll('[data-category], [data-section]').forEach(e => e.checked = true);
  document.getElementById('context').checked = false;
  document.getElementById('indirect').checked = false;
  document.getElementById('names').checked = false;
  document.getElementById('domains').checked = true;
  introduction(); updateGraph();
  Plotly.relayout(plot, {'xaxis.range':[-1170,1170], 'yaxis.range':[-1170,1170]});
});
introduction();

updateGraph();
const initialId = decodeURIComponent(location.hash.slice(1));
if (nodes.has(initialId)) select(initialId);

}
startMap().catch(error => {
  document.getElementById('search-status').textContent = 'The map could not load. Please refresh the page.';
  console.error(error);
});
