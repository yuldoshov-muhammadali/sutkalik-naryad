// Umumiy xatti-harakatlar. Inline JavaScript yo'q (Content-Security-Policy: script-src 'self').
(function () {
  "use strict";

  // --- Modal oynani yopish: <button data-close-modal> --------------------------------------
  document.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-close-modal]");
    if (btn) {
      var modal = document.getElementById("modal");
      if (modal) modal.innerHTML = "";
    }
  });

  // --- Tasdiqlash so'rovi: <form data-confirm="Matn"> -------------------------------------
  document.addEventListener("submit", function (event) {
    var form = event.target.closest("form[data-confirm]");
    if (form && !window.confirm(form.getAttribute("data-confirm"))) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);

  // --- Kunduzgi / tungi / avtomatik rejim (static/js/theme.js bilan birga) -----------------
  var THEME_KEY = "naryad-theme";
  var THEME_ORDER = ["auto", "light", "dark"];
  // Sarlavhalar joriy tilda tugmaning data-title-* atributlaridan olinadi
  function themeTitle(btn, pref) { return btn.getAttribute("data-title-" + pref) || pref; }
  var systemQuery = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function applyTheme(pref) {
    var root = document.documentElement;
    root.setAttribute("data-theme", pref);
    var dark = pref === "dark" || (pref === "auto" && systemQuery && systemQuery.matches);
    root.classList.toggle("dark", !!dark);
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.title = themeTitle(btn, pref);
      var label = btn.querySelector("[data-theme-label]");
      if (label) label.textContent = themeTitle(btn, pref);
    });
  }

  function currentTheme() {
    var pref = document.documentElement.getAttribute("data-theme");
    return THEME_ORDER.indexOf(pref) >= 0 ? pref : "auto";
  }

  document.addEventListener("click", function (event) {
    if (!event.target.closest("[data-theme-toggle]")) return;
    var next = THEME_ORDER[(THEME_ORDER.indexOf(currentTheme()) + 1) % THEME_ORDER.length];
    try { window.localStorage.setItem(THEME_KEY, next); } catch (e) { /* saqlanmasa ham ishlaydi */ }
    applyTheme(next);
  });
  if (systemQuery && systemQuery.addEventListener) {
    systemQuery.addEventListener("change", function () { if (currentTheme() === "auto") applyTheme("auto"); });
  }
  applyTheme(currentTheme());

  // --- Jonli soat va joriy sutka (Toshkent vaqti, UTC+5) ----------------------------------
  // Server vaqti sahifada data-server-now (ms) da beriladi; JS faqat farqni hisoblaydi,
  // shuning uchun telefon soati noto'g'ri bo'lsa ham to'g'ri ko'rsatadi.
  var TZ_OFFSET = 5 * 3600 * 1000;
  var DAY = 24 * 3600 * 1000;
  var SHIFT_HOUR = 18;
  // Hafta kunlari, oylar va “Smena almashishiga … qoldi” — joriy tilda, serverdan data- atributlarida
  var WEEKDAYS = [], MONTHS = [], DAY_MONTH = "{d}-{m}", LEFT_HM = "", LEFT_M = "";

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function dayLabel(d) { return DAY_MONTH.replace("{d}", d.getUTCDate()).replace("{m}", MONTHS[d.getUTCMonth()]); }

  function setText(root, selector, text) {
    var el = root.querySelector(selector);
    if (el && el.textContent !== text) el.textContent = text;
  }

  var clock = document.querySelector("[data-clock]");
  var lastShiftStart = null;
  if (clock) {
    WEEKDAYS = (clock.getAttribute("data-weekdays") || "").split(",");
    MONTHS = (clock.getAttribute("data-months") || "").split(",");
    DAY_MONTH = clock.getAttribute("data-day-month") || DAY_MONTH;
    LEFT_HM = clock.getAttribute("data-left-hm") || "";
    LEFT_M = clock.getAttribute("data-left-m") || "";
    var serverNow = parseInt(clock.getAttribute("data-server-now"), 10);
    var skew = isNaN(serverNow) ? 0 : serverNow - Date.now();

    var tick = function () {
      var local = Date.now() + skew + TZ_OFFSET; // Toshkent devor soati (UTC maydonlari orqali o'qiladi)
      var now = new Date(local);
      setText(clock, "[data-clock-time]", pad(now.getUTCHours()) + ":" + pad(now.getUTCMinutes()) + ":" + pad(now.getUTCSeconds()));
      setText(clock, "[data-clock-date]", WEEKDAYS[now.getUTCDay()] + ", " + dayLabel(now) + " " + now.getUTCFullYear());  // 14-oktabr 2026 / 14 октября 2026

      var start = Math.floor(local / DAY) * DAY + SHIFT_HOUR * 3600 * 1000;
      if (local < start) start -= DAY;
      var end = start + DAY;
      var left = end - local;
      var hours = Math.floor(left / 3600000);
      var minutes = Math.floor((left % 3600000) / 60000);
      setText(clock, "[data-duty-label]", dayLabel(new Date(start)) + " 18:00 → " + dayLabel(new Date(end)) + " 18:00");
      setText(clock, "[data-duty-left]", (hours ? LEFT_HM : LEFT_M).replace("{h}", hours).replace("{m}", minutes));
      var bar = clock.querySelector("[data-duty-bar]");
      if (bar) {
        var pct = Math.min(100, Math.max(0, ((local - start) / DAY) * 100)).toFixed(1) + "%";
        bar.style.width = pct;
        bar.parentElement.setAttribute("aria-valuenow", Math.round(parseFloat(pct)));
      }
      // 18:00 — yangi sutka: holat kartochkalari ham darhol yangilansin
      if (lastShiftStart !== null && start !== lastShiftStart) refreshStatus(true);
      lastShiftStart = start;
    };
    tick();
    window.setInterval(tick, 1000);
  }

  // --- Bosh sahifa holat kartochkalari: har 60 soniyada HTMX bilan (yashirin tabda emas) ---
  var REFRESH_MS = 60 * 1000;
  var lastRefresh = Date.now();

  function refreshStatus(force) {
    var target = document.querySelector("[data-live-status]");
    if (!target || !window.htmx) return;
    if (!force && document.visibilityState !== "visible") return;
    lastRefresh = Date.now();
    window.htmx.trigger(target, "naryad:refresh");
  }

  if (document.querySelector("[data-live-status]")) {
    window.setInterval(function () { refreshStatus(false); }, REFRESH_MS);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible" && Date.now() - lastRefresh >= REFRESH_MS) refreshStatus(false);
    });
  }

  // --- Kursant: “Naryadga … qoldi” / “Hozir naryaddasiz, smena almashishiga … qoldi” (14-bosqich) ---
  // Element HTMX bilan almashtirilishi mumkin, shuning uchun har soniyada qaytadan topiladi.
  // Matn shablonlari joriy tilda data-t-* atributlarida: {d} kun, {h} soat, {m} daqiqa.
  function countdownTick() {
    document.querySelectorAll("[data-countdown]").forEach(function (el) {
      if (el._skew === undefined) {
        var serverNow = parseInt(el.getAttribute("data-server-now"), 10);
        el._skew = isNaN(serverNow) ? 0 : serverNow - Date.now();
        el._phase = null;
      }
      var now = Date.now() + el._skew;
      var start = parseInt(el.getAttribute("data-start"), 10);
      var end = parseInt(el.getAttribute("data-end"), 10);
      var onDuty = now >= start;
      var phase = now >= end ? "done" : (onDuty ? "on" : "before");
      // Naryad boshlandi yoki tugadi — kartochka serverdan yangilansin
      if (el._phase !== null && phase !== el._phase) refreshStatus(true);
      el._phase = phase;
      if (phase === "done") return;
      var total = Math.max(0, Math.floor(((onDuty ? end : start) - now) / 60000));
      var d = Math.floor(total / 1440), h = Math.floor((total % 1440) / 60), m = total % 60;
      var key = onDuty ? ((d || h) ? "on-hm" : "on-m") : (d ? "before-d" : (h ? "before-hm" : "before-m"));
      var text = (el.getAttribute("data-t-" + key) || "").replace("{d}", d).replace("{h}", h + (onDuty ? d * 24 : 0)).replace("{m}", m);
      if (el.textContent !== text) el.textContent = text;
    });
  }
  if (document.querySelector("[data-countdown]")) {
    countdownTick();
    window.setInterval(countdownTick, 1000);
  }

  // --- Ro'yxatdan qidirib tanlash: <input data-filter-select="id_cadet"> (17-bosqich, Kasallar ro'yxati) ---
  // Mos kelmagan variantlar yashiriladi; bitta qolsa — o'zi tanlanadi.
  document.addEventListener("input", function (event) {
    var input = event.target.closest("[data-filter-select]");
    if (!input) return;
    var select = document.getElementById(input.getAttribute("data-filter-select"));
    if (!select) return;
    var q = input.value.trim().toLowerCase();
    var visible = [];
    Array.prototype.forEach.call(select.options, function (opt) {
      var show = !opt.value || !q || opt.text.toLowerCase().indexOf(q) !== -1;
      opt.hidden = !show;
      if (show && opt.value) visible.push(opt);
    });
    if (visible.length === 1) select.value = visible[0].value;
  });

  // Sessiya tugagan bo'lsa (kirish sahifasiga yo'naltirilgan) — butun sahifani kirishga o'tkazamiz
  document.addEventListener("htmx:beforeSwap", function (event) {
    var xhr = event.detail.xhr;
    if (xhr && xhr.responseURL && xhr.responseURL.indexOf("/kirish/") !== -1) {
      event.detail.shouldSwap = false;
      window.location.href = xhr.responseURL;
    }
  });
})();
