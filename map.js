/* NDcPP v4.0 dependency map: browse SFRs and follow their dependencies. */
(function () {
  'use strict';
  var node = document.getElementById('rm-data');
  if (!node) return;
  var D = JSON.parse(node.textContent), CPP = D.cpp, SD = D.sd;
  var byId = {}; D.sfrs.forEach(function (s) { byId[s.id] = s; });
  var ext = {}; D.external.forEach(function (x) { ext[x] = 1; });
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var TYPES = { 'mandatory': 'Mandatory', 'selection-based': 'Selection-based', 'optional': 'Optional' };
  var state = { q: '', types: { 'mandatory': 1, 'selection-based': 1, 'optional': 1 }, sel: null };

  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  function say(m) { var t = document.getElementById('toast'); if (!t) return; t.textContent = m; t.classList.add('show'); clearTimeout(say.t); say.t = setTimeout(function () { t.classList.remove('show'); }, 2200); }

  // ---- list
  var listEl = $('#rm-list'), countEl = $('#rm-count'), noneEl = $('#rm-none');
  function matches(s) {
    if (!state.types[s.type]) return false;
    if (!state.q) return true;
    return (s.id + ' ' + s.title).toLowerCase().indexOf(state.q) !== -1;
  }
  function renderList() {
    listEl.textContent = '';
    var n = 0, fam = null, ul = null;
    D.sfrs.forEach(function (s) {
      if (!matches(s)) return;
      n++;
      if (s.family !== fam) {
        fam = s.family;
        listEl.appendChild(el('h3', 'rm-fam', fam));
        ul = el('ul', 'rm-items'); listEl.appendChild(ul);
      }
      var li = el('li'), b = el('button', 'rm-item' + (state.sel === s.id ? ' on' : ''));
      b.type = 'button'; b.dataset.id = s.id;
      b.appendChild(el('span', 'rm-id', s.id));
      b.appendChild(el('span', 'rm-ttl', s.title));
      b.appendChild(el('span', 'rm-badge ' + s.type, TYPES[s.type]));
      li.appendChild(b); ul.appendChild(li);
    });
    countEl.textContent = n + ' of ' + D.sfrs.length + ' requirements';
    noneEl.hidden = n > 0;
  }
  listEl.addEventListener('click', function (e) {
    var b = e.target.closest('.rm-item'); if (b) select(b.dataset.id, true);
  });
  $('#rm-q').addEventListener('input', function (e) { state.q = e.target.value.trim().toLowerCase(); renderList(); });
  document.querySelectorAll('.rm-type').forEach(function (c) {
    c.addEventListener('change', function () { state.types[c.value] = c.checked ? 1 : 0; renderList(); });
  });
  $('#rm-reset').addEventListener('click', function () {
    state.q = ''; $('#rm-q').value = '';
    document.querySelectorAll('.rm-type').forEach(function (c) { c.checked = true; state.types[c.value] = 1; });
    renderList();
  });

  // ---- detail
  var detail = $('#rm-detail');
  function chip(id, cls) {
    var known = !!byId[id];
    var b = el(known ? 'button' : 'span', 'rm-chip' + (known ? '' : ' ext') + (cls ? ' ' + cls : ''), id);
    if (known) { b.type = 'button'; b.dataset.go = id; } else b.title = 'Defined in the Common Criteria, not in this cPP';
    return b;
  }
  function section(title, hint) {
    var s = el('section', 'rm-sec'); s.appendChild(el('h3', null, title));
    if (hint) s.appendChild(el('p', 'rm-hint', hint));
    return s;
  }
  function diagram(s) {
    var W = 720, ROW = 34, GAP = 8, BW = 150, BH = 26;
    var left = [], right = s.used_by.slice(0, 14);
    s.deps.forEach(function (d, gi) { d.any_of.forEach(function (id) { left.push({ id: id, g: gi, or: d.any_of.length > 1 }); }); });
    var rows = Math.max(left.length, right.length, 1), H = rows * (BH + GAP) + 24;
    var NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('class', 'rm-svg'); svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Dependency diagram for ' + s.id);
    function mk(t, a, txt) { var e = document.createElementNS(NS, t); for (var k in a) e.setAttribute(k, a[k]); if (txt != null) e.textContent = txt; return e; }
    var cy = H / 2, cx = W / 2 - 70;
    function box(x, y, id, kind) {
      var g = mk('g', { 'class': 'rm-n ' + kind + (byId[id] ? '' : ' ext'), transform: 'translate(' + x + ',' + y + ')', tabindex: byId[id] && kind !== 'self' ? 0 : -1 });
      g.appendChild(mk('rect', { width: BW, height: BH, rx: 7 }));
      g.appendChild(mk('text', { x: BW / 2, y: BH / 2 + 4, 'text-anchor': 'middle' }, id.length > 21 ? id.slice(0, 20) + '…' : id));
      if (byId[id] && kind !== 'self') { g.setAttribute('role', 'button'); g.dataset.go = id; }
      svg.appendChild(g);
    }
    function link(x1, y1, x2, y2, dashed) {
      var m = (x1 + x2) / 2;
      svg.insertBefore(mk('path', { d: 'M' + x1 + ',' + y1 + ' C' + m + ',' + y1 + ' ' + m + ',' + y2 + ' ' + x2 + ',' + y2, 'class': 'rm-edge' + (dashed ? ' or' : '') }), svg.firstChild);
    }
    function yAt(i, n) { return (H - n * (BH + GAP) + GAP) / 2 + i * (BH + GAP); }
    left.forEach(function (n, i) { var y = yAt(i, left.length); box(0, y, n.id, 'dep'); link(BW, y + BH / 2, cx, cy, n.or); });
    right.forEach(function (id, i) { var y = yAt(i, right.length); box(W - BW, y, id, 'by'); link(cx + BW, cy, W - BW, y + BH / 2, false); });
    box(cx, cy - BH / 2, s.id, 'self');
    if (!left.length) svg.appendChild(mk('text', { x: 0, y: cy + 4, 'class': 'rm-none' }, 'No dependencies'));
    if (!right.length) svg.appendChild(mk('text', { x: W, y: cy + 4, 'text-anchor': 'end', 'class': 'rm-none' }, 'Nothing depends on it'));
    svg.appendChild(mk('text', { x: 0, y: 10, 'class': 'rm-col' }, 'NEEDS'));
    svg.appendChild(mk('text', { x: W, y: 10, 'text-anchor': 'end', 'class': 'rm-col' }, 'NEEDED BY'));
    return svg;
  }
  function select(id, push) {
    var s = byId[id]; if (!s) return;
    state.sel = id;
    if (push) history.replaceState(null, '', '#' + encodeURIComponent(id));
    detail.textContent = '';
    detail.classList.add('open');
    var top = el('div', 'rm-top');
    var close = el('button', 'rm-close', '← All requirements'); close.type = 'button';
    close.addEventListener('click', function () { detail.classList.remove('open'); state.sel = null; history.replaceState(null, '', location.pathname); renderList(); });
    top.appendChild(close); detail.appendChild(top);
    detail.appendChild(el('div', 'rm-badge ' + s.type, TYPES[s.type]));
    detail.appendChild(el('h2', 'rm-h', s.id));
    detail.appendChild(el('p', 'rm-sub', s.title));
    var acts = el('div', 'actions');
    function a(label, href, primary) { var x = el('a', 'act' + (primary ? ' primary' : ''), label); x.href = href; return x; }
    if (s.anchor) acts.appendChild(a('Requirement in cPP', CPP + '#' + s.anchor, true));
    if (s.sd_anchor) acts.appendChild(a('Evaluation activities in SD', SD + '#' + s.sd_anchor));
    var cp = el('button', 'act', 'Copy link'); cp.type = 'button';
    cp.addEventListener('click', function () { var u = location.href; (navigator.clipboard ? navigator.clipboard.writeText(u) : Promise.reject()).then(function () { say('Link copied'); }, function () { say(u); }); });
    acts.appendChild(cp); detail.appendChild(acts);

    var d3 = section('Map'); d3.appendChild(diagram(s)); detail.appendChild(d3);
    if (s.note) detail.appendChild(el('p', 'rm-note', s.note));
    if (s.members && s.members.length) {
      var dm = section('Iterations'); var gm = el('div', 'rm-group wrap');
      s.members.forEach(function (id) { gm.appendChild(chip(id)); }); dm.appendChild(gm); detail.appendChild(dm);
    }
    var d1 = section('Needs', 'Dependencies from Annex E of the cPP. "or" groups are alternatives: one of them satisfies the dependency.');
    if (!s.deps.length) d1.appendChild(el('p', 'rm-none-p', 'This requirement has no dependencies.'));
    s.deps.forEach(function (d) {
      var g = el('div', 'rm-group');
      d.any_of.forEach(function (id, i) { if (i) g.appendChild(el('span', 'rm-or', 'or')); g.appendChild(chip(id)); });
      if (!d.any_of.length) g.appendChild(el('span', null, d.text));
      d1.appendChild(g);
    });
    if (s.rationale.length) {
      var r = el('ul', 'rm-rat'); s.rationale.forEach(function (t) { r.appendChild(el('li', null, t)); });
      var det = el('details'); det.appendChild(el('summary', null, 'How the cPP says each is satisfied')); det.appendChild(r); d1.appendChild(det);
    }
    detail.appendChild(d1);
    var d2 = section('Needed by', s.used_by.length ? s.used_by.length + ' requirement' + (s.used_by.length > 1 ? 's' : '') + ' in this cPP depend on it.' : '');
    if (!s.used_by.length) d2.appendChild(el('p', 'rm-none-p', 'No other requirement lists it as a dependency.'));
    var gb = el('div', 'rm-group wrap'); s.used_by.forEach(function (id) { gb.appendChild(chip(id)); }); d2.appendChild(gb);
    detail.appendChild(d2);
    renderList();
    if (push) { detail.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); }
  }
  detail.addEventListener('click', function (e) { var t = e.target.closest('[data-go]'); if (t) select(t.dataset.go, true); });
  detail.addEventListener('keydown', function (e) { if ((e.key === 'Enter' || e.key === ' ') && e.target.dataset && e.target.dataset.go) { e.preventDefault(); select(e.target.dataset.go, true); } });
  window.addEventListener('hashchange', function () { var h = decodeURIComponent(location.hash.slice(1)); if (byId[h]) select(h, false); });

  renderList();
  var h0 = decodeURIComponent(location.hash.slice(1)); if (byId[h0]) select(h0, false);
})();
