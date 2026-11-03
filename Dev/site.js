/* ND-iTC site behaviour. Everything here is progressive enhancement:
   the pages are fully readable and linkable with JavaScript turned off. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage unavailable */ } }
  };
  var DATA = {};
  try { DATA = JSON.parse($('#nd-data').textContent); } catch (e) { DATA = { search: [] }; }

  /* ---- theme ---- */
  var root = document.documentElement;
  var saved = store.get('nd-theme');
  if (!saved) { var wm = /(?:^|;)nd-theme=(light|dark)/.exec(window.name); saved = wm && wm[1]; }
  if (saved === 'light' || saved === 'dark') root.setAttribute('data-theme', saved);
  var themeBtn = $('#theme-toggle');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var cur = root.getAttribute('data-theme') ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var next = cur === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    store.set('nd-theme', next);
    window.name = window.name.replace(/(?:^|;)nd-theme=(light|dark)/, '') + ';nd-theme=' + next; /* carries across pages when file:// storage is per-page */
  });

  /* ---- mobile nav ---- */
  var mt = $('#menu-toggle'), nav = $('#nav');
  if (mt && nav) mt.addEventListener('click', function () {
    var open = nav.classList.toggle('open');
    mt.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  /* ---- toast + clipboard ---- */
  var toast = $('#toast'), toastTimer;
  function say(msg) {
    if (!toast) return;
    toast.textContent = msg; toast.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { toast.classList.remove('show'); }, 2200);
  }
  function copy(text, ok) {
    function fallback() {
      var ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly', '');
      ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); say(ok); } catch (e) { say('Copy failed. Select and copy manually.'); }
      document.body.removeChild(ta);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { say(ok); }, fallback);
    } else fallback();
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-copy]');
    if (b) { e.preventDefault(); copy(b.getAttribute('data-copy'), b.getAttribute('data-ok') || 'Copied to clipboard'); return; }
    var s = e.target.closest('[data-share]');
    if (s) {
      e.preventDefault();
      var url = s.getAttribute('data-share') || location.href, title = s.getAttribute('data-title') || document.title;
      if (navigator.share) navigator.share({ title: title, url: url }).catch(function () {});
      else copy(url, 'Link copied');
    }
  });

  /* ---- "which documents do I need?" chooser ---- */
  var chips = $$('[data-choice]');
  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      chips.forEach(function (o) { o.setAttribute('aria-pressed', o === c ? 'true' : 'false'); });
      $$('[data-panel]').forEach(function (p) { p.hidden = p.getAttribute('data-panel') !== c.getAttribute('data-choice'); });
    });
  });

  /* ---- library status filter ---- */
  var pills = $$('[data-status-filter]');
  pills.forEach(function (p) {
    p.addEventListener('click', function () {
      var want = p.getAttribute('data-status-filter');
      pills.forEach(function (o) { o.setAttribute('aria-pressed', o === p ? 'true' : 'false'); });
      $$('[data-release]').forEach(function (r) {
        r.hidden = !(want === 'all' || r.getAttribute('data-release') === want);
      });
    });
  });

  /* ---- open the release a #hash points to ---- */
  function openHash() {
    var t = location.hash && document.getElementById(location.hash.slice(1));
    if (t && t.tagName === 'DETAILS') { t.hidden = false; t.open = true; }
  }
  window.addEventListener('hashchange', openHash); openHash();
  $$('a[href^="#"]').forEach(function (a) { a.addEventListener('click', function () { setTimeout(openHash, 0); }); });

  /* ---- command palette ---- */
  var pal = $('#palette'), pin = $('#palette-input'), plist = $('#palette-list'), opener = $('#open-search');
  var sel = 0, shown = [], lastFocus = null;
  function norm(s) { return (s || '').toLowerCase(); }
  function renderPalette(q) {
    var terms = norm(q).split(/\s+/).filter(Boolean);
    var items = (DATA.search || []).filter(function (it) {
      var hay = norm(it.k + ' ' + it.t + ' ' + (it.s || '') + ' ' + (it.x || ''));
      return terms.every(function (t) { return hay.indexOf(t) !== -1; });
    });
    shown = items.slice(0, 40); sel = 0;
    plist.innerHTML = '';
    if (!shown.length) {
      var li = document.createElement('li'); li.style.padding = '1rem'; li.style.color = 'var(--muted)';
      li.textContent = 'No matches. Try a requirement name such as FCS_TLSS_EXT.1 or an RFI number.'; plist.appendChild(li); return;
    }
    shown.forEach(function (it, i) {
      var li = document.createElement('li'), a = document.createElement('a');
      a.href = it.u; a.setAttribute('role', 'option'); a.setAttribute('aria-selected', i === 0 ? 'true' : 'false');
      if (/^https?:/.test(it.u)) { a.target = '_blank'; a.rel = 'noopener'; }
      var k = document.createElement('span'); k.className = 'k'; k.textContent = it.k;
      var t = document.createElement('span'); t.textContent = it.t;
      var s = document.createElement('span'); s.className = 's'; s.textContent = it.s || '';
      a.appendChild(k); a.appendChild(t); a.appendChild(s); li.appendChild(a); plist.appendChild(li);
    });
  }
  function move(d) {
    var as = $$('a', plist); if (!as.length) return;
    as[sel] && as[sel].setAttribute('aria-selected', 'false');
    sel = (sel + d + as.length) % as.length;
    as[sel].setAttribute('aria-selected', 'true'); as[sel].scrollIntoView({ block: 'nearest' });
  }
  function openPal() { if (!pal) return; lastFocus = document.activeElement; pal.hidden = false; pin.value = ''; renderPalette(''); pin.focus(); }
  function closePal() { if (!pal || pal.hidden) return; pal.hidden = true; if (lastFocus) lastFocus.focus(); }
  if (pal) {
    if (opener) opener.addEventListener('click', openPal);
    pin.addEventListener('input', function () { renderPalette(pin.value); });
    pal.addEventListener('click', function (e) { if (e.target === pal) closePal(); });
    pal.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') { var a = $$('a', plist)[sel]; if (a) { e.preventDefault(); a.click(); } }
    });
    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); pal.hidden ? openPal() : closePal(); }
      else if (e.key === 'Escape') closePal();
      else if (e.key === '/' && pal.hidden && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) { e.preventDefault(); openPal(); }
    });
  }

  /* ---- Technical Decision explorer ---- */
  var table = $('#td-table');
  if (table) {
    var tbody = $('tbody', table), rows = $$('tr', tbody);
    var q = $('#td-q'), doc = $('#td-doc'), yr = $('#td-year'), cnt = $('#td-count'), none = $('#td-none');
    var sortKey = 'date', sortDir = -1;
    var params = new URLSearchParams(location.search);
    if (q && params.get('q')) q.value = params.get('q');
    if (doc && params.get('doc')) doc.value = params.get('doc');
    if (yr && params.get('year')) yr.value = params.get('year');

    function visibleRows() { return rows.filter(function (r) { return !r.hidden; }); }
    function apply() {
      var terms = norm(q.value).split(/\s+/).filter(Boolean), d = doc.value, y = yr.value;
      rows.forEach(function (r) {
        var ok = (!d || (' ' + r.dataset.docs + ' ').indexOf(' ' + d + ' ') !== -1) &&
                 (!y || r.dataset.year === y) &&
                 terms.every(function (t) { return r.dataset.text.indexOf(t) !== -1; });
        r.hidden = !ok;
      });
      var n = visibleRows().length;
      cnt.innerHTML = '<b>' + n + '</b> of ' + rows.length + ' decisions';
      none.hidden = n !== 0; table.hidden = n === 0;
      var p = new URLSearchParams();
      if (q.value) p.set('q', q.value); if (d) p.set('doc', d); if (y) p.set('year', y);
      var qs = p.toString();
      try { history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash); } catch (e) { /* file:// */ }
    }
    function sortBy(key, dir) {
      sortKey = key; sortDir = dir;
      rows.sort(function (a, b) {
        var x = a.dataset[key], y = b.dataset[key];
        if (key === 'id') { x = +a.dataset.num; y = +b.dataset.num; }
        return (x > y ? 1 : x < y ? -1 : 0) * dir;
      }).forEach(function (r) { tbody.appendChild(r); });
      $$('th[data-sort]', table).forEach(function (th) {
        th.setAttribute('aria-sort', th.dataset.sort === key ? (dir === 1 ? 'ascending' : 'descending') : 'none');
      });
    }
    $$('th[data-sort] button', table).forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.parentNode.dataset.sort;
        sortBy(k, k === sortKey ? -sortDir : (k === 'date' || k === 'id' ? -1 : 1));
      });
    });
    [q, doc, yr].forEach(function (el) { el && el.addEventListener('input', apply); });
    var reset = $('#td-reset');
    if (reset) reset.addEventListener('click', function () { q.value = ''; doc.value = ''; yr.value = ''; apply(); q.focus(); });

    function csvCell(s) { s = String(s == null ? '' : s); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }
    var exp = $('#td-export');
    if (exp) exp.addEventListener('click', function () {
      var head = ['ID', 'Title', 'Reference', 'Published', 'Applies to', 'Status', 'URL'];
      var lines = [head.join(',')];
      visibleRows().forEach(function (r) {
        var d = JSON.parse(r.dataset.json);
        lines.push([d.id, d.title, d.reference, d.date, d.applies.join('; '), d.status, d.url].map(csvCell).join(','));
      });
      var blob = new Blob(['﻿' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
      var a = document.createElement('a'); a.href = URL.createObjectURL(blob);
      a.download = 'nd-itc-technical-decisions.csv'; document.body.appendChild(a); a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
      say('Exported ' + (lines.length - 1) + ' decisions');
    });
    var shareView = $('#td-share');
    if (shareView) shareView.addEventListener('click', function () { copy(location.href, 'Link to this filtered view copied'); });

    sortBy('date', -1); apply();
    if (location.hash) { var t = document.getElementById(location.hash.slice(1)); if (t) { t.hidden = false; t.scrollIntoView({ block: 'center' }); } }
  }
})();
