/* Light/dark toggle for the published document pages. Shares the 'nd-theme' choice with the rest of the site. */
(function () {
  'use strict';
  var root = document.documentElement;
  function get() { try { return localStorage.getItem('nd-theme'); } catch (e) { return null; } }
  var qm = /[?&]nd-theme=(light|dark)/.exec(location.search);
  var saved = qm ? qm[1] : get();
  if (!saved) { var m = /(?:^|;)nd-theme=(light|dark)/.exec(window.name); saved = m && m[1]; }
  var dark = saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  root.setAttribute('data-theme', dark ? 'dark' : 'light');
  function mount() {
    var b = document.createElement('button');
    b.id = 'nd-theme-btn'; b.type = 'button';
    function label() { b.textContent = root.getAttribute('data-theme') === 'dark' ? 'Light theme' : 'Dark theme'; }
    label();
    b.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('nd-theme', next); } catch (e) { /* storage unavailable */ }
      if (/[?&]nd-theme=/.test(location.search)) { try { history.replaceState(null, '', location.search.replace(/nd-theme=(light|dark)/, 'nd-theme=' + next) + location.hash); } catch (e) { /* ignore */ } }
      window.name = window.name.replace(/(?:^|;)nd-theme=(light|dark)/, '') + ';nd-theme=' + next;
      label();
    });
    document.body.appendChild(b);
  }
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);
})();
