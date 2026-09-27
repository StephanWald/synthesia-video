// stage.js - one 1920x1080 SVG per page, drawn from primitives, and the beat runner that animates it.
//
// Time: the page's own timeline starts at load. The exporter captures from T0 = 4.0 s (one second of the
// cold frame), so beat times are seconds after T0, i.e. seconds into the Synthesia clip. Beats come from the
// page's own list or from ?beats=a,b,c (build.py passes its estimate, later the times measured from the voice).
// Every frame is computed from t alone, never CSS animation: the exporter's clock is virtual.
//
// A still: draw every element as base (last argument true) and call play() without beats(); the cold
// frame is then the finished card and build.py exports it as a PNG (kind "image").
const NS = 'http://www.w3.org/2000/svg';
const Q = new URLSearchParams(location.search);
const T0 = 4.0, DUR = 0.5, HOLD = 3.0;                   // fade length, hold after the last beat
const svg = document.getElementById('stage');
const E = {};                                            // id -> {node, base, path, len, head}

function mk(tag, attrs, parent) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) if (attrs[k] != null) n.setAttribute(k, attrs[k]);
  (parent || svg).appendChild(n);
  return n;
}
function reg(id, node, base) {
  if (E[id]) throw new Error('duplicate id ' + id);
  E[id] = { node, base: !!base };
  if (!base) node.style.opacity = 0;
  return node;
}
// base = true: visible from the cold frame on; false: hidden until a beat shows it
const S = {
  rect(id, x, y, w, h, cls = 'box', base = false) { return reg(id, mk('rect', { x, y, width: w, height: h, class: cls }), base); },
  text(id, x, y, str, cls = '', base = false, anchor = null) {
    const n = mk('text', { x, y, class: cls, 'text-anchor': anchor }); n.textContent = str; return reg(id, n, base);
  },
  line(id, x1, y1, x2, y2, cls = 'rule', base = false) { return reg(id, mk('line', { x1, y1, x2, y2, class: cls }), base); },
  // a wire is a path plus an arrowhead at its end; drawn over DUR when its beat fires
  wire(id, d, base = false) {
    const g = mk('g', { class: 'wire' });
    const p = mk('path', { d }, g);
    const len = p.getTotalLength();
    const a = p.getPointAtLength(len), b = p.getPointAtLength(Math.max(0, len - 1));
    const dx = a.x - b.x, dy = a.y - b.y, m = Math.hypot(dx, dy) || 1, ux = dx / m, uy = dy / m;
    const bx = a.x - ux * 12, by = a.y - uy * 12;
    const head = mk('polygon', { points: `${a.x},${a.y} ${bx - uy * 8},${by + ux * 8} ${bx + uy * 8},${by - ux * 8}` }, g);
    reg(id, g, base);
    Object.assign(E[id], { path: p, len, head });
    p.setAttribute('stroke-dasharray', len);
    p.setAttribute('stroke-dashoffset', base ? 0 : len);
    head.style.opacity = base ? 1 : 0;
    return g;
  },
};
function title(str) {
  S.text('title', 96, 100, str, 'h', true);
  S.line('title-rule', 96, 136, 1824, 136, 'rule', true);
}

// ---- beats ---------------------------------------------------------------------------------------------
// beats([{at, do:[[op, id, arg], ...]}, ...]); ops:
//   show / hide  fade over DUR        text  set text (persistent)       wire  draw over DUR (stays)
//   hi           white while this beat is current                        hik / lo  white until 'lo'
let BEATS = [];
function beats(list) {
  BEATS = list;
  const qb = Q.get('beats');
  if (qb) qb.split(',').map(Number).forEach((t, i) => { if (BEATS[i]) BEATS[i].at = t; });
}
function render(tp) {
  const t = tp - T0;
  const op = {}, cur = new Set(), keep = new Set(), wires = {}, texts = {};
  for (const id in E) op[id] = E[id].base ? 1 : 0;
  let last = -1;
  BEATS.forEach((b, i) => { if (t >= b.at) last = i; });
  BEATS.forEach((b, i) => {
    if (t < b.at) return;
    const p = Math.min(1, (t - b.at) / DUR), isCur = i === last;
    for (const [o, id, arg] of b.do) {
      if (!E[id]) throw new Error('unknown id ' + id);
      switch (o) {
        case 'show': op[id] = Math.max(op[id], p); break;
        case 'hide': op[id] = Math.min(op[id], 1 - p); break;
        case 'hi': if (isCur) cur.add(id); break;
        case 'hik': keep.add(id); break;
        case 'lo': keep.delete(id); break;
        case 'wire': wires[id] = Math.max(wires[id] || 0, p); op[id] = 1; if (isCur) cur.add(id); break;
        case 'text': texts[id] = arg; op[id] = Math.max(op[id], p); break;
      }
    }
  });
  for (const id in E) {
    const e = E[id];
    e.node.style.opacity = op[id];
    e.node.classList.toggle('hi', cur.has(id) || keep.has(id));
    if (e.path) {
      const p = e.base ? 1 : (wires[id] || 0);
      e.path.setAttribute('stroke-dashoffset', e.len * (1 - p));
      e.head.style.opacity = p >= 1 ? 1 : 0;
    }
    if (id in texts) e.node.textContent = texts[id];
  }
}
function tEnd() { return T0 + (BEATS.length ? BEATS[BEATS.length - 1].at : 0) + HOLD; }
// Preview in a browser: plays in real time. ?at=7.5 freezes at page time 7.5 s; ?end shows the end frame.
function play() {
  const end = tEnd();
  if (Q.has('end')) { render(end); return; }
  if (Q.has('at')) { render(+Q.get('at')); return; }
  const loop = () => { const now = performance.now() / 1000; render(Math.min(now, end)); if (now < end) requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
}
