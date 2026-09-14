/* aragonitesand.com — shared behaviour.
 *
 * No build step, no dependencies. Seven things:
 *   1. the responsive navigation (ported from the parent's site-chrome.js)
 *   2. the grain-scale illustration, drawn from data attributes
 *   3. the lot lookup, which fetches data/lots.json
 *   4. the depth calculator, which reads bulk density from data/grades.json
 *   5. the dealer inquiry form on wholesale.html
 *   6. the quote builder on products.html
 *   7. the quote it hands to the inquiry form
 *
 * Every piece looks for its own markup and does nothing if it is absent, so
 * one script serves every page.
 */
(function () {
  "use strict";

  var ICON_MENU =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></svg>';
  var ICON_CLOSE =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';

  /* Resolve a site-relative path from any page. Pages live at the site root,
     so this is a passthrough — kept as one place to change if pages move. */
  function sitePath(p) {
    var base = document.body.getAttribute("data-root") || "";
    return base + p;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* ---------- 1. Navigation ---------- */
  function initNavigation() {
    var toggle = document.querySelector(".ac-nav__toggle");
    var panel = document.getElementById("ac-nav-mobile");
    if (!toggle || !panel) return;

    var header = toggle.closest(".ac-nav");
    var focusableSelector = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

    function setCurrentPage() {
      var file = window.location.pathname.split("/").pop() || "index.html";
      if (file === "") file = "index.html";
      document.querySelectorAll(".ac-nav a[href]").forEach(function (link) {
        var raw = link.getAttribute("href");
        if (raw.indexOf("#") !== -1) return; /* section links never mark a page current */
        var href = raw.split("?")[0];
        if (href === "" || href === "./") href = "index.html";
        if (href === file || (file === "index.html" && href === "/")) {
          link.setAttribute("aria-current", "page");
          var item = link.closest(".ac-nav__item");
          if (item) item.setAttribute("aria-current", "page");
        }
      });
    }

    function setOpen(open) {
      panel.classList.toggle("is-open", open);
      if (header) header.classList.toggle("menu-open", open);
      panel.hidden = !open;
      panel.inert = !open;
      panel.setAttribute("aria-hidden", open ? "false" : "true");
      toggle.innerHTML = open ? ICON_CLOSE : ICON_MENU;
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      if (open) {
        var first = panel.querySelector(focusableSelector);
        if (first) requestAnimationFrame(function () { first.focus(); });
      }
    }

    setCurrentPage();
    setOpen(false);

    toggle.addEventListener("click", function () {
      setOpen(!panel.classList.contains("is-open"));
    });
    panel.addEventListener("click", function (event) {
      if (event.target.closest("a")) setOpen(false);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && panel.classList.contains("is-open")) {
        setOpen(false);
        toggle.focus();
      }
      if (event.key === "Tab" && panel.classList.contains("is-open")) {
        var items = Array.prototype.slice.call(panel.querySelectorAll(focusableSelector));
        if (!items.length) return;
        var first = items[0], last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    });
    document.addEventListener("pointerdown", function (event) {
      if (panel.classList.contains("is-open") && header && !header.contains(event.target)) setOpen(false);
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 1080 && panel.classList.contains("is-open")) setOpen(false);
    });
  }

  /* ---------- 2. Grain-scale illustration ----------
   *
   * <div class="grain__dots" data-grains="0.6,0.85,1.0" data-tone="1"></div>
   * draws one circle per value, at `--mm` pixels per millimetre, so the dots
   * and the ruler underneath agree. This is drawn geometry, not a photograph;
   * the page says so beside it.
   */
  function pxPerMm() {
    var v = getComputedStyle(document.documentElement).getPropertyValue("--mm");
    var n = parseFloat(v);
    return n > 0 ? n : 15;
  }

  function initGrains() {
    var PX = pxPerMm();
    document.querySelectorAll("[data-grains]").forEach(function (el) {
      if (el.childElementCount) return;
      var tone = el.getAttribute("data-tone") || "1";
      el.getAttribute("data-grains").split(",").forEach(function (s, i) {
        var mm = parseFloat(s);
        if (!(mm > 0)) return;
        var d = document.createElement("span");
        d.className = "dot" + (tone !== "1" ? " dot--" + tone : "");
        if (tone === "1" && i % 2) d.className += " dot--2";
        var px = Math.round(mm * PX);
        d.style.width = px + "px";
        d.style.height = px + "px";
        d.setAttribute("aria-hidden", "true");
        el.appendChild(d);
      });
    });

    document.querySelectorAll("[data-ruler]").forEach(function (ruler) {
      if (ruler.childElementCount) return;
      var max = parseFloat(ruler.getAttribute("data-ruler")) || 6;
      var step = max <= 3 ? 0.25 : 0.5;
      var bar = document.createElement("div");
      bar.className = "ruler__bar";
      bar.style.width = (max * PX) + "px";
      ruler.appendChild(bar);
      for (var mm = 0; mm <= max + 1e-9; mm += step) {
        var major = Math.abs(mm - Math.round(mm)) < 1e-9;
        var t = document.createElement("div");
        t.className = "tick" + (major ? " tick--major" : "");
        t.style.left = (mm * PX) + "px";
        ruler.appendChild(t);
        if (major) {
          var l = document.createElement("div");
          l.className = "tick__label";
          l.style.left = (mm * PX) + "px";
          l.textContent = Math.round(mm);
          ruler.appendChild(l);
        }
      }
      var cap = document.createElement("div");
      cap.className = "ruler__cap";
      cap.style.left = (max * PX + 14) + "px";
      cap.textContent = "mm";
      ruler.appendChild(cap);
    });
  }

  /* ---------- 3. Lot lookup ---------- */
  var lotsPromise = null;
  function loadLots() {
    if (!lotsPromise) {
      lotsPromise = fetch(sitePath("data/lots.json"), { cache: "no-cache" }).then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      });
    }
    return lotsPromise;
  }

  function formatDate(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    if (!m) return iso || "";
    var months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    return parseInt(m[3], 10) + " " + months[parseInt(m[2], 10) - 1] + " " + m[1];
  }

  function gradeName(slug) {
    return slug ? slug.charAt(0).toUpperCase() + slug.slice(1) : "";
  }

  function initLotLookup() {
    var input = document.getElementById("lot-input");
    var button = document.getElementById("lot-go");
    var panel = document.getElementById("lot-panel");
    if (!input || !button || !panel) return;

    function renderError(msg) {
      panel.innerHTML = '<p class="lot-panel__err">' + msg + "</p>";
    }

    function render(code) {
      var key = (code || "").trim().toUpperCase().replace(/\s+/g, "");
      if (!key) {
        panel.innerHTML = '<p class="lot-panel__empty">Enter the lot code printed on the bag to see its mineralogy, sieve distribution and sample date.</p>';
        return;
      }
      panel.setAttribute("aria-busy", "true");
      loadLots().then(function (data) {
        var lot = data.lots && data.lots[key];
        if (!lot) {
          renderError("No lot found for “" + escapeHtml(key) + "”. Check the code on the back panel, lower left, or <a class=\"prose-link\" href=\"about.html#contact\">contact us</a> and we will pull the record.");
          return;
        }
        var html = "";
        if (lot.placeholder) {
          html += '<span class="placeholder-flag" data-placeholder>Demo lot. Invented data, not a real analysis.</span>';
        }
        html += '<div class="lot-id num" style="margin-top:' + (lot.placeholder ? '14px' : '0') + '">' + escapeHtml(key) + "</div>" +
          '<div class="lot-meta">' + escapeHtml(gradeName(lot.grade)) + " grade · bagged " + escapeHtml(formatDate(lot.bagged)) + " · sampled " + escapeHtml(formatDate(lot.sampled)) + "</div>" +
          '<div class="lot-rows">';
        (lot.rows || []).forEach(function (r) {
          html += '<div class="lot-row"><span>' + escapeHtml(r[0]) + '</span><span class="num">' + escapeHtml(r[1]) + "</span></div>";
        });
        html += "</div>";
        if (lot.sieve && lot.sieve.length) {
          html += '<div class="lot-sieve"><p class="eyebrow">Sieve distribution, percent retained</p>';
          lot.sieve.forEach(function (s) {
            var pct = Math.max(0, Math.min(100, parseFloat(s[1]) || 0));
            html += '<div class="bar-row"><span class="bar-row__k">' + escapeHtml(s[0]) + "</span>" +
              '<span class="bar-track"><span class="bar-fill" style="width:' + pct + '%"></span></span>' +
              '<span class="bar-row__v num">' + pct + "%</span></div>";
          });
          html += "</div>";
        }
        html += '<div class="lot-status"><strong style="color:var(--bone)">Tested by</strong> ' + escapeHtml(lot.lab || "") +
          (lot.method ? '<br><span>' + escapeHtml(lot.method) + "</span>" : "") + "</div>";
        panel.innerHTML = html;
      }).catch(function () {
        renderError("The lot register could not be loaded. If you opened this page as a file, serve it over HTTP; otherwise try again or <a class=\"prose-link\" href=\"about.html#contact\">contact us</a>.");
      }).then(function () {
        panel.removeAttribute("aria-busy");
      });
    }

    button.addEventListener("click", function () { render(input.value); });
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); render(input.value); } });
    document.querySelectorAll("[data-lot-example]").forEach(function (b) {
      b.addEventListener("click", function () {
        input.value = b.getAttribute("data-lot-example");
        render(input.value);
        input.focus();
      });
    });

    /* ?lot=CODE or #lot=CODE deep links, for a QR code on the bag. */
    var m = /[?&#]lot=([^&#]+)/.exec(window.location.href);
    if (m) {
      input.value = decodeURIComponent(m[1]);
      render(input.value);
      var section = document.getElementById("lot");
      if (section) section.scrollIntoView();
    }
  }

  /* ---------- 4. Depth calculator ---------- */
  var gradesPromise = null;
  function loadGrades() {
    if (!gradesPromise) {
      gradesPromise = fetch(sitePath("data/grades.json"), { cache: "no-cache" }).then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      });
    }
    return gradesPromise;
  }

  function initCalculator() {
    var root = document.querySelector("[data-calc]");
    if (!root) return;
    var L = root.querySelector("[data-calc-length]");
    var W = root.querySelector("[data-calc-width]");
    var D = root.querySelector("[data-calc-depth]");
    var G = root.querySelector("[data-calc-grade]");
    var outLb = root.querySelector("[data-calc-lb]");
    var outBags = root.querySelector("[data-calc-bags]");
    var outNote = root.querySelector("[data-calc-density-note]");
    if (!L || !W || !D || !outLb || !outBags) return;

    /* Densities come from the markup first (rendered from grades.json by the
       build script), then are refreshed from grades.json at runtime so a
       changed data file wins without a rebuild. */
    var densities = {};
    var bagLb = parseFloat(root.getAttribute("data-bag-lb")) || 20;
    var fixedGrade = root.getAttribute("data-calc-fixed-grade");
    if (fixedGrade) densities[fixedGrade] = parseFloat(root.getAttribute("data-calc-density")) || 90;
    if (G) {
      Array.prototype.forEach.call(G.options, function (o) {
        var d = parseFloat(o.getAttribute("data-density"));
        if (d > 0) densities[o.value] = d;
      });
    }

    function currentGrade() { return fixedGrade || (G ? G.value : "fine"); }
    function density() { return densities[currentGrade()] || 90; }

    function fmtIn(n) {
      return (Math.round(n * 100) / 100).toString();
    }

    function calc() {
      var l = parseFloat(L.value) || 0, w = parseFloat(W.value) || 0, d = parseFloat(D.value) || 0;
      var ft3 = (l * w * d) / 1728;
      var lbs = ft3 * density();
      if (!(lbs > 0)) {
        outLb.textContent = "—";
        outBags.textContent = "Enter the tank length, width and the bed depth you want.";
        return;
      }
      var bags = Math.ceil(lbs / bagLb);
      outLb.innerHTML = Math.round(lbs).toLocaleString("en-US") + " <small>lb</small>";
      outBags.textContent = bags + (bags === 1 ? " bag" : " bags") + " at " + bagLb + " lb · " +
        fmtIn(l) + "″ × " + fmtIn(w) + "″ at " + fmtIn(d) + "″ deep";
      if (outNote) {
        outNote.textContent = "Calculated at " + density() + " lb per cubic foot, the typical bulk density of the " + currentGrade() + " grade.";
      }
    }

    [L, W, D].forEach(function (f) { f.addEventListener("input", calc); });
    if (G) G.addEventListener("change", calc);

    root.querySelectorAll("[data-preset]").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var p = chip.getAttribute("data-preset").split("x");
        L.value = p[0]; W.value = p[1];
        root.querySelectorAll("[data-preset]").forEach(function (c) { c.setAttribute("aria-pressed", c === chip ? "true" : "false"); });
        calc();
      });
    });
    [L, W].forEach(function (f) {
      f.addEventListener("input", function () {
        root.querySelectorAll("[data-preset]").forEach(function (c) { c.setAttribute("aria-pressed", "false"); });
      });
    });

    calc();
    loadGrades().then(function (data) {
      (data.grades || []).forEach(function (g) {
        if (g.bulk_density_lb_ft3 > 0) densities[g.slug] = g.bulk_density_lb_ft3;
      });
      if (data.bag_lb > 0) bagLb = data.bag_lb;
      calc();
    }).catch(function () { /* markup values stand */ });
  }

  /* ---------- 5. Dealer inquiry form ----------
   *
   * Validates in the browser, then posts to the endpoint named on the form's
   * `data-endpoint` attribute as JSON. With no endpoint configured, it opens a
   * pre-filled mail message to the dealer address instead, so the form works
   * on plain static hosting from day one.
   */
  function initDealerForm() {
    var form = document.getElementById("dealer-form");
    if (!form) return;
    var alert = form.querySelector("[data-form-alert]");
    var submit = form.querySelector('button[type="submit"]');
    var success = document.getElementById("dealer-success");

    function fieldError(input, msg) {
      var err = document.getElementById(input.id + "-err");
      if (err) err.textContent = msg || "";
      if (msg) input.setAttribute("aria-invalid", "true"); else input.removeAttribute("aria-invalid");
    }

    function validate() {
      var firstBad = null;
      form.querySelectorAll(".fld").forEach(function (input) {
        var msg = "";
        var v = input.value.trim();
        if (input.required && !v) msg = "This field is required.";
        else if (input.type === "email" && v && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) msg = "Enter a valid email address.";
        fieldError(input, msg);
        if (msg && !firstBad) firstBad = input;
      });
      return firstBad;
    }

    form.querySelectorAll(".fld").forEach(function (input) {
      input.addEventListener("input", function () { fieldError(input, ""); });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (alert) { alert.hidden = true; alert.textContent = ""; }
      var bad = validate();
      if (bad) {
        if (alert) { alert.textContent = "A few fields need attention before this can be sent."; alert.hidden = false; }
        bad.focus();
        return;
      }
      var honeypot = form.querySelector('[name="website"]');
      if (honeypot && honeypot.value) return;

      var data = {};
      new FormData(form).forEach(function (v, k) { if (k !== "website") data[k] = v; });
      data.source = "aragonitesand.com dealer inquiry";
      data.page = window.location.href;

      var endpoint = form.getAttribute("data-endpoint");
      function done() {
        form.hidden = true;
        if (success) { success.hidden = false; success.scrollIntoView({ block: "start" }); success.focus(); }
      }
      if (endpoint) {
        if (submit) { submit.disabled = true; submit.textContent = "Sending…"; }
        fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(data) })
          .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); done(); })
          .catch(function () {
            if (alert) { alert.textContent = "The inquiry could not be sent. Email " + (form.getAttribute("data-mailto") || "us") + " directly and we will reply the same business day."; alert.hidden = false; }
            if (submit) { submit.disabled = false; submit.textContent = "Send inquiry"; }
          });
        return;
      }
      /* No endpoint: hand off to the visitor's mail client. */
      var to = form.getAttribute("data-mailto") || "";
      var lines = [];
      Object.keys(data).forEach(function (k) { if (k !== "page" && k !== "source" && data[k]) lines.push(k.replace(/([A-Z])/g, " $1").replace(/^./, function (c) { return c.toUpperCase(); }) + ": " + data[k]); });
      var subject = "Dealer inquiry — " + (data.storeName || data.fullName || "aragonitesand.com");
      window.location.href = "mailto:" + to + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(lines.join("\n"));
      done();
    });
  }

  /* ---------- 6. Quote builder ----------
   *
   * The products page is a price list you can add up. Each SKU carries its
   * price and pallet count in the markup (rendered from data/products.json by
   * tools/build.py), so nothing is fetched and the arithmetic works from a
   * file:// page too. Pallet counts across every grade decide which volume
   * tier applies, which is the whole point: mixing grades still earns the
   * break. The result hands off to the inquiry form as a query string, so no
   * state has to survive the page change.
   */
  function money(n) {
    return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  function money0(n) {
    return "$" + Math.round(n).toLocaleString("en-US");
  }

  function initQuoteBuilder() {
    var root = document.querySelector("[data-quote]");
    if (!root) return;
    var bar = document.getElementById("quote-bar");
    var tiers;
    try { tiers = JSON.parse(root.getAttribute("data-tiers") || "[]"); } catch (e) { tiers = []; }

    var lines = [];
    root.querySelectorAll("[data-sku]").forEach(function (el) {
      var input = el.querySelector('input[type="number"]');
      if (!input) return;
      lines.push({
        el: el,
        input: input,
        sku: el.getAttribute("data-sku"),
        name: el.getAttribute("data-name") || el.getAttribute("data-sku"),
        perBag: parseFloat(el.getAttribute("data-per-bag")) || 0,
        bags: parseInt(el.getAttribute("data-bags-per-pallet"), 10) || 0,
        lb: parseFloat(el.getAttribute("data-bag-lb")) || 0
      });
    });
    if (!lines.length) return;

    function tierFor(pallets) {
      var found = tiers[0] || { discount: 0, label: "" };
      tiers.forEach(function (t) {
        var min = t.min_pallets || 0;
        var max = (t.max_pallets === null || t.max_pallets === undefined) ? Infinity : t.max_pallets;
        if (pallets >= min && pallets <= max) found = t;
      });
      return found;
    }

    function paint() {
      var pallets = 0, bags = 0, lb = 0, gross = 0;
      lines.forEach(function (l) {
        var q = Math.max(0, parseInt(l.input.value, 10) || 0);
        pallets += q;
        bags += q * l.bags;
        lb += q * l.bags * l.lb;
        gross += q * l.bags * l.perBag;
        l.el.classList.toggle("product--active", q > 0);
        var minus = l.el.querySelector("[data-qty-down]");
        if (minus) minus.disabled = q <= 0;
      });

      var tier = tierFor(pallets || 1);
      var discount = pallets > 0 ? (tier.discount || 0) : 0;
      var net = gross * (1 - discount);

      /* The tier cells sit in their own section, not inside the quote root, so
         this is a document query on purpose. */
      document.querySelectorAll("[data-tier]").forEach(function (cell) {
        cell.setAttribute("data-active", pallets > 0 && cell.getAttribute("data-tier") === tier.id ? "true" : "false");
      });

      if (!bar) return;
      var open = pallets > 0;
      bar.hidden = false;
      bar.classList.toggle("is-open", open);
      document.body.classList.toggle("has-quote", open);
      if (!open) {
        reserveSpace(false);
        return;
      }

      bar.querySelector("[data-quote-total]").innerHTML =
        money0(net) + ' <small>estimated, before freight</small>';
      bar.querySelector("[data-quote-meta]").innerHTML =
        pallets + (pallets === 1 ? " pallet" : " pallets") + " · " +
        bags.toLocaleString("en-US") + " bags · " +
        Math.round(lb).toLocaleString("en-US") + " lb" +
        (discount > 0 ? ' · <b>' + Math.round(discount * 100) + "% volume break applied</b>" : "");

      var parts = [];
      lines.forEach(function (l) {
        var q = Math.max(0, parseInt(l.input.value, 10) || 0);
        if (q > 0) parts.push(l.sku + ":" + q);
      });
      /* Two destinations for the same basket. The primary one is the parent's
         lead form, because that is where stock, pricing and the sales desk
         are; the quote rides across in the `document` parameter, which their
         form writes into the details field, and the utm_* trio attributes the
         lead back to this site. The secondary keeps the local form working for
         anyone who would rather not leave. */
      var summary = lines.filter(function (l) {
        return (parseInt(l.input.value, 10) || 0) > 0;
      }).map(function (l) {
        var q = parseInt(l.input.value, 10) || 0;
        return l.name + " (" + l.sku + ") x " + q + " pallet" + (q === 1 ? "" : "s");
      }).join(", ");
      summary = "Aragonite aquarium sand quote built on aragonitesand.com: " + summary +
        " — " + bags + " bags, " + Math.round(lb).toLocaleString("en-US") + " lb, estimated " +
        money(net) + " before freight" +
        (discount > 0 ? " (includes the " + Math.round(discount * 100) + "% volume break)" : "");

      var link = bar.querySelector("[data-quote-link]");
      if (link) {
        var contact = link.getAttribute("data-ac-contact");
        if (contact) {
          var utm = (link.getAttribute("data-ac-utm") || "||").split("|");
          /* An industry is sent only when one is set on the link. An empty
             industry= is not harmless: it can clear a preselected value at
             the other end. */
          var ind = link.getAttribute("data-ac-industry");
          link.href = contact +
            "?interest=" + encodeURIComponent(link.getAttribute("data-ac-interest") || "bulk-pricing") +
            (ind ? "&industry=" + encodeURIComponent(ind) : "") +
            "&document=" + encodeURIComponent(summary) +
            "&utm_source=" + encodeURIComponent(utm[0]) +
            "&utm_medium=" + encodeURIComponent(utm[1]) +
            "&utm_campaign=" + encodeURIComponent(utm[2]) +
            "&utm_content=" + encodeURIComponent("quote-builder");
        }
      }
      var local = bar.querySelector("[data-quote-local]");
      if (local) local.href = "wholesale.html?q=" + encodeURIComponent(parts.join(",")) + "#inquiry";

      /* Last, once the figures are in it: the bar is one row on a desktop and
         three on a phone, and it is the text just written that decides which. */
      reserveSpace(true);
    }

    root.querySelectorAll("[data-qty-up], [data-qty-down]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var input = btn.parentNode.querySelector('input[type="number"]');
        var q = Math.max(0, parseInt(input.value, 10) || 0);
        q = btn.hasAttribute("data-qty-up") ? Math.min(999, q + 1) : Math.max(0, q - 1);
        input.value = q;
        paint();
      });
    });
    lines.forEach(function (l) {
      l.input.addEventListener("input", paint);
      l.input.addEventListener("change", function () {
        var q = parseInt(l.input.value, 10);
        l.input.value = (isNaN(q) || q < 0) ? 0 : Math.min(999, q);
        paint();
      });
    });
    /* Reserve exactly the bar's own height under the page, measured rather than
       assumed: the bar wraps to two and then three rows as the viewport
       narrows, and the stylesheet's fallback figure cannot know which. Without
       this the bar covers the last rows of the footer on a phone. */
    function reserveSpace(open) {
      if (!bar) return;
      document.body.style.paddingBottom = open ? bar.offsetHeight + "px" : "";
    }
    var reflow;
    window.addEventListener("resize", function () {
      window.clearTimeout(reflow);
      reflow = window.setTimeout(function () {
        reserveSpace(document.body.classList.contains("has-quote"));
      }, 120);
    });

    var clear = bar && bar.querySelector("[data-quote-clear]");
    if (clear) {
      clear.addEventListener("click", function () {
        lines.forEach(function (l) { l.input.value = 0; });
        paint();
        lines[0].input.focus();
      });
    }
    paint();
  }

  /* ---------- 7. The quote, carried into the inquiry form ----------
   *
   * `wholesale.html?q=AR-F20:2,AR-M50:1` renders the line items above the
   * form and writes them into a field, so what the buyer priced is what we
   * receive. The catalogue is embedded on that page for the same reason as
   * above: no fetch, no build step, works offline.
   */
  function initQuoteContext() {
    var host = document.getElementById("quote-context");
    if (!host) return;
    var m = /[?&]q=([^&#]+)/.exec(window.location.search || window.location.href);
    if (!m) return;
    var catalogue;
    try { catalogue = JSON.parse(host.getAttribute("data-catalogue") || "{}"); } catch (e) { return; }
    var tiers = catalogue.tiers || [];
    var skus = catalogue.skus || {};

    var pallets = 0, gross = 0, rows = [];
    decodeURIComponent(m[1]).split(",").forEach(function (part) {
      var bits = part.split(":");
      var sku = skus[bits[0]];
      var q = parseInt(bits[1], 10) || 0;
      if (!sku || q <= 0) return;
      var ext = q * sku.bags * sku.perBag;
      pallets += q;
      gross += ext;
      rows.push({ sku: bits[0], name: sku.name, q: q, bags: q * sku.bags, ext: ext });
    });
    if (!rows.length) return;

    var tier = tiers[0] || { discount: 0 };
    tiers.forEach(function (t) {
      var max = (t.max_pallets === null || t.max_pallets === undefined) ? Infinity : t.max_pallets;
      if (pallets >= (t.min_pallets || 0) && pallets <= max) tier = t;
    });
    var net = gross * (1 - (tier.discount || 0));

    var html = '<span class="quote-context__label">The quote you built</span><ul class="quote-context__list">';
    rows.forEach(function (r) {
      html += "<li><span>" + escapeHtml(r.name) + " · " + escapeHtml(r.sku) + " · " + r.q +
        (r.q === 1 ? " pallet" : " pallets") + " (" + r.bags + " bags)</span><span>" + money(r.ext) + "</span></li>";
    });
    html += "</ul>";
    if (tier.discount) {
      html += '<div class="quote-context__total"><span>' + Math.round(tier.discount * 100) +
        "% volume break, " + escapeHtml(tier.label || "") + "</span><span>&minus;" + money(gross - net) + "</span></div>";
    }
    html += '<div class="quote-context__total"><span>' + pallets + (pallets === 1 ? " pallet" : " pallets") +
      ", estimated before freight</span><span>" + money(net) + "</span></div>";
    host.innerHTML = html;
    host.hidden = false;

    var field = document.getElementById("df-quote");
    if (field) {
      field.value = rows.map(function (r) { return r.sku + " x " + r.q + " pallet" + (r.q === 1 ? "" : "s"); }).join(", ") +
        " — estimated " + money(net) + " before freight";
      var wrap = field.closest(".field");
      if (wrap) wrap.hidden = false;
    }
  }

  function init() {
    initNavigation();
    initGrains();
    initLotLookup();
    initCalculator();
    initDealerForm();
    initQuoteBuilder();
    initQuoteContext();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
