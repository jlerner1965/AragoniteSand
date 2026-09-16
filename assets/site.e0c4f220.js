/* AragoCor Aragonite Sand — site script. No dependencies. */
(function () {
  'use strict';
  var AS = window.AS || {};
  var host = location.hostname;
  var isLocal = /^(localhost|127\.|0\.0\.0\.0|\[::1\])/.test(host);
  var isProd = host === 'aragonitesand.com' || host === 'www.aragonitesand.com';

  /* ---------- Navigation ---------- */
  var mb = document.querySelector('.menu-btn'), menu = document.getElementById('site-menu');
  if (mb && menu) {
    var setMenu = function (open) {
      menu.classList.toggle('open', open);
      mb.setAttribute('aria-expanded', open ? 'true' : 'false');
      mb.querySelector('.menu-label').textContent = open ? 'Close' : 'Menu';
    };
    mb.addEventListener('click', function () { setMenu(!menu.classList.contains('open')); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && menu.classList.contains('open')) { setMenu(false); mb.focus(); } });
    document.addEventListener('click', function (e) { if (menu.classList.contains('open') && !menu.contains(e.target) && !mb.contains(e.target)) setMenu(false); });
  }
  var path = location.pathname.replace(/\.html$/, '').replace(/\/$/, '') || '/';
  document.querySelectorAll('.site-nav a:not(.btn)').forEach(function (a) {
    var href = a.getAttribute('href').replace(/\/$/, '') || '/';
    if (href === path) a.setAttribute('aria-current', 'page');
  });

  /* Legacy in-page anchors from the previous single-page site. */
  if (path === '/' && location.hash) {
    var map = { '#grades': '/grades-and-specifications', '#why': '/grades-and-specifications', '#calculator': '/aquarium-and-aquaculture', '#uses': '/commercial-applications', '#wholesale': '/packaging-and-delivery', '#faq': '/aquarium-and-aquaculture#faq', '#quote': '/request-quote' };
    if (map[location.hash]) location.replace(map[location.hash]);
  }

  /* ---------- Attribution ---------- */
  function store(kind) { try { return kind === 'session' ? window.sessionStorage : window.localStorage; } catch (e) { return null; } }
  function get(kind, k) { var s = store(kind); try { return s ? s.getItem(k) : null; } catch (e) { return null; } }
  function set(kind, k, v) { var s = store(kind); try { if (s) s.setItem(k, v); } catch (e) {} }
  var params = new URLSearchParams(location.search);
  var utm = {};
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(function (k) { if (params.get(k)) utm[k] = params.get(k).slice(0, 120); });
  var ref = document.referrer && !document.referrer.indexOf(location.origin) === false ? '' : document.referrer;
  ref = document.referrer && document.referrer.indexOf(location.origin) !== 0 ? document.referrer.slice(0, 300) : '';
  function sourceLabel() {
    if (utm.utm_source) return utm.utm_source + (utm.utm_medium ? ' / ' + utm.utm_medium : '');
    if (ref) { try { return new URL(ref).hostname + ' / referral'; } catch (e) { return 'referral'; } }
    return 'direct / none';
  }
  if (!get('session', 'as_landing')) {
    set('session', 'as_landing', location.href.slice(0, 300));
    set('session', 'as_referrer', ref);
    set('session', 'as_last_touch', sourceLabel());
    set('session', 'as_utm', JSON.stringify(utm));
  } else if (utm.utm_source) {
    set('session', 'as_last_touch', sourceLabel());
    set('session', 'as_utm', JSON.stringify(utm));
  }
  if (!get('local', 'as_first_touch')) {
    set('local', 'as_first_touch', sourceLabel());
    set('local', 'as_first_touch_at', new Date().toISOString());
  }

  /* ---------- Analytics (GA4) ---------- */
  var ga = AS.ga;
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = window.gtag || gtag;
  var gaOn = !!ga && !isLocal && !get('local', 'as_internal');
  if (params.get('internal') === '1') set('local', 'as_internal', '1');
  if (gaOn) {
    var s = document.createElement('script'); s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + ga; document.head.appendChild(s);
    gtag('js', new Date());
    gtag('config', ga, { site_hostname: host, site_environment: isProd ? 'production' : 'preview', form_version: AS.v || '' });
  }
  function track(name, p) {
    var payload = Object.assign({ site_hostname: host, site_environment: isProd ? 'production' : 'preview', page_path: location.pathname }, p || {});
    if (gaOn) gtag('event', name, payload);
    if (isLocal || params.get('debug_events') === '1') { try { console.info('[event]', name, payload); } catch (e) {} }
  }
  window.asTrack = track;

  /* Page-level view events */
  if (path === '/grades-and-specifications') track('specification_view');
  if (path === '/packaging-and-delivery') track('packaging_view');

  /* Click events: data-event, outbound, downloads, tel/mailto */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a, button');
    if (!a) return;
    var name = a.getAttribute('data-event');
    var placement = a.getAttribute('data-placement') || '';
    var href = a.getAttribute('href') || '';
    if (name) { track(name, { placement: placement, link_url: href }); return; }
    if (/^tel:/.test(href)) { track('phone_click', { placement: placement }); return; }
    if (/^mailto:/.test(href)) { track('email_click', { placement: placement }); return; }
    if (/\.pdf(\?|#|$)/i.test(href)) { track('technical_document_download', { document: href.split('/').pop().split('?')[0], placement: placement }); if (/aragocorminerals\.com/.test(href)) track('outbound_aragocor_click', { placement: placement, link_url: href }); return; }
    if (/aragocorminerals\.com/.test(href)) { track('outbound_aragocor_click', { placement: placement, link_url: href }); return; }
  });

  /* ---------- Quote form ---------- */
  var form = document.getElementById('quote-form');
  if (form) initForm(form);

  function initForm(form) {
    var status = document.getElementById('form-status');
    var submit = form.querySelector('button[type=submit]');
    var started = false;
    var openedAt = Date.now();
    form.querySelector('input[name=started_at]').value = String(openedAt);

    /* Hidden attribution */
    var utmStored = {};
    try { utmStored = JSON.parse(get('session', 'as_utm') || '{}'); } catch (e) {}
    var hidden = {
      landing_page: get('session', 'as_landing') || location.href,
      current_page: location.href.slice(0, 300),
      referrer: get('session', 'as_referrer') || '',
      utm_source: utmStored.utm_source || '', utm_medium: utmStored.utm_medium || '', utm_campaign: utmStored.utm_campaign || '',
      utm_content: utmStored.utm_content || '', utm_term: utmStored.utm_term || '',
      first_touch: get('local', 'as_first_touch') || '', last_touch: get('session', 'as_last_touch') || '',
      hostname: host, form_version: AS.v || ''
    };
    Object.keys(hidden).forEach(function (k) { var el = form.querySelector('input[name=' + k + ']'); if (el) el.value = hidden[k]; });

    /* Preselect from query string, e.g. /request-quote?grade=AG-CAL&intent=sample */
    var q = new URLSearchParams(location.search);
    if (q.get('grade')) { var g = form.querySelector('select[name=grade]'); if (g) { Array.prototype.forEach.call(g.options, function (o) { if (o.value === q.get('grade')) g.value = o.value; }); } }
    if (q.get('intent') === 'sample') { var sm = form.querySelector('input[name=sample_request][value=Yes]'); if (sm) sm.checked = true; }
    if (q.get('intent') === 'details') { var d = form.querySelector('select[name=request_type]'); if (d) d.value = 'Product details'; }
    if (q.get('application')) { var ap = form.querySelector('select[name=application]'); if (ap) { Array.prototype.forEach.call(ap.options, function (o) { if (o.value === q.get('application')) ap.value = o.value; }); } }

    form.addEventListener('focusin', function () { if (!started) { started = true; track('quote_start', { placement: 'form' }); } });

    /* Field validation */
    var rules = {
      first_name: { req: true, label: 'First name' },
      last_name: { req: true, label: 'Last name' },
      company: { req: true, label: 'Company' },
      role: { req: true, label: 'Job title or role' },
      email: { req: true, label: 'Work email', email: true },
      country: { req: true, label: 'Country' },
      region: { req: true, label: 'State, province or region' },
      buyer_type: { req: true, label: 'Buyer type' },
      application: { req: true, label: 'Intended application' },
      quantity: { req: true, label: 'Estimated order quantity' },
      destination: { req: true, label: 'Delivery destination or postal code' },
      consent: { req: true, label: 'Privacy consent', check: true }
    };
    function fieldWrap(name) { var el = form.querySelector('[name=' + name + ']'); return el ? el.closest('.field') : null; }
    function setError(name, msg) {
      var w = fieldWrap(name); if (!w) return;
      var e = w.querySelector('.error'); var el = form.querySelector('[name=' + name + ']');
      w.classList.toggle('invalid', !!msg);
      if (e) e.textContent = msg || '';
      if (el) { if (msg) { el.setAttribute('aria-invalid', 'true'); if (e && e.id) el.setAttribute('aria-describedby', e.id); } else { el.removeAttribute('aria-invalid'); } }
    }
    function validate() {
      var errors = [];
      Object.keys(rules).forEach(function (name) {
        var r = rules[name]; var el = form.querySelector('[name=' + name + ']'); if (!el) return;
        var v = r.check ? el.checked : String(el.value || '').trim();
        var msg = '';
        if (r.req && !v) msg = r.check ? 'Please confirm you have read the privacy notice.' : r.label + ' is required.';
        else if (r.email && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) msg = 'Enter a valid email address.';
        setError(name, msg);
        if (msg) errors.push({ name: name, msg: msg });
      });
      return errors;
    }
    form.querySelectorAll('input, select, textarea').forEach(function (el) {
      el.addEventListener('blur', function () { if (rules[el.name] && form.querySelector('.field.invalid')) validate(); });
      el.addEventListener('change', function () { if (rules[el.name] && el.closest('.field.invalid')) validate(); });
    });

    function showStatus(kind, html) { status.className = 'form-status ' + kind; status.innerHTML = html; status.focus(); }
    function collect() {
      var data = {};
      new FormData(form).forEach(function (v, k) {
        if (k === 'documents') { data.documents = (data.documents || []).concat([String(v)]); return; }
        data[k] = String(v).trim();
      });
      data.documents = (data.documents || []).join(', ');
      return data;
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      status.className = 'form-status'; status.innerHTML = '';
      var errors = validate();
      if (errors.length) {
        showStatus('err', '<strong>Please check the highlighted fields.</strong><ul>' + errors.map(function (x) { return '<li><a href="#f-' + x.name + '">' + x.msg + '</a></li>'; }).join('') + '</ul>');
        track('quote_error', { error_type: 'validation', field: errors[0].name });
        return;
      }
      var data = collect();
      submit.disabled = true; submit.textContent = 'Sending…';
      track('quote_submit', { buyer_type: data.buyer_type, application: data.application, quantity: data.quantity });
      var ctrl = ('AbortController' in window) ? new AbortController() : null;
      var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 20000) : null;
      fetch('/api/lead', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(data), signal: ctrl ? ctrl.signal : undefined })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, status: r.status, j: j }; }).catch(function () { return { ok: false, status: r.status, j: null }; }); })
        .then(function (res) {
          if (timer) clearTimeout(timer);
          if (res.ok && res.j && res.j.ok) {
            track('quote_success', { buyer_type: data.buyer_type, application: data.application, quantity: data.quantity, request_type: data.request_type });
            if (data.sample_request === 'Yes') track('sample_request', { application: data.application });
            if (data.request_type === 'Product details') track('product_details_request', { application: data.application });
            try { sessionStorage.setItem('as_lead_sent', JSON.stringify({ type: data.request_type, sample: data.sample_request, docs: data.documents })); } catch (e) {}
            location.assign('/thank-you');
            return;
          }
          if (res.status === 400 && res.j && res.j.fields) {
            Object.keys(res.j.fields).forEach(function (k) { setError(k, res.j.fields[k]); });
            showStatus('err', '<strong>Please check the highlighted fields.</strong>');
            track('quote_error', { error_type: 'server_validation' });
            submit.disabled = false; submit.textContent = 'Send request';
            return;
          }
          throw new Error((res.j && res.j.error) || ('HTTP ' + res.status));
        })
        .catch(function (err) {
          if (timer) clearTimeout(timer);
          submit.disabled = false; submit.textContent = 'Send request';
          track('quote_error', { error_type: 'delivery', message: String(err && err.message || err).slice(0, 80) });
          showStatus('err', '<strong>Your request could not be sent.</strong> Nothing you entered has been lost. You can try again, or send the same details by email.');
          showFallback(data);
        });
    });

    var LEAD_EMAIL = 'info@aragocorminerals.com';
    function leadText(d) {
      var rows = [['Request type', d.request_type], ['Name', d.first_name + ' ' + d.last_name], ['Company', d.company], ['Role', d.role], ['Email', d.email], ['Phone', d.phone],
        ['Country', d.country], ['Region', d.region], ['Buyer type', d.buyer_type], ['Application', d.application], ['Grade', d.grade], ['Order quantity', d.quantity],
        ['Annual volume', d.annual_volume], ['Packaging', d.packaging], ['Destination', d.destination], ['Timing', d.timing], ['Documents', d.documents], ['Sample', d.sample_request]];
      var out = 'Quote request from aragonitesand.com\n\n';
      rows.forEach(function (r) { if (r[1]) out += (r[0] + ':' + '                '.slice(0, Math.max(1, 17 - r[0].length))) + r[1] + '\n'; });
      if (d.message) out += '\n' + d.message + '\n';
      return out;
    }
    function showFallback(d) {
      var old = document.getElementById('lead-fallback'); if (old) old.remove();
      var text = leadText(d);
      var subject = 'Quote request from aragonitesand.com: ' + (d.company || d.buyer_type || 'enquiry');
      var box = document.createElement('div'); box.id = 'lead-fallback'; box.className = 'fallback';
      box.innerHTML = '<div class="btn-row"><a class="btn btn-primary" href="mailto:' + LEAD_EMAIL + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(text.slice(0, 1500)) + '">Open in your email app</a><button class="btn btn-secondary" type="button" id="fb-copy">Copy the request</button></div>' +
        '<p class="note" style="margin:.75rem 0 .4rem">Or send it to <a href="mailto:' + LEAD_EMAIL + '">' + LEAD_EMAIL + '</a>.</p><label class="sr" for="fb-text">Your request</label><textarea id="fb-text" readonly></textarea>';
      status.insertAdjacentElement('afterend', box);
      document.getElementById('fb-text').value = text;
      document.getElementById('fb-copy').addEventListener('click', function () {
        var ta = document.getElementById('fb-text'), btn = this;
        var done = function () { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = 'Copy the request'; }, 2500); };
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(ta.value).then(done, function () { ta.select(); }); else { ta.select(); try { document.execCommand('copy'); done(); } catch (e) {} }
      });
    }
  }

  /* Thank-you page: tailor next steps to what was requested */
  var ty = document.getElementById('thankyou-detail');
  if (ty) {
    try {
      var sent = JSON.parse(sessionStorage.getItem('as_lead_sent') || 'null');
      if (sent) {
        var bits = [];
        if (sent.type) bits.push(sent.type.toLowerCase() === 'quote' ? 'a commercial quote' : sent.type.toLowerCase());
        if (sent.sample === 'Yes') bits.push('a sample');
        if (sent.docs) bits.push('documents (' + sent.docs + ')');
        if (bits.length) ty.textContent = 'You asked for ' + bits.join(', ') + '. ';
      }
    } catch (e) {}
  }
})();
