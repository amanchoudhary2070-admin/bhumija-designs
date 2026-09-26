// Bhoomija Designs storefront JS: navigation, wishlist, gallery, and the small
// motion/polish layer (scroll reveal, header state, toasts, sticky mobile buy bar).
// Every enhancement here is progressive: if JS fails, the page is still fully usable.
(function () {
  "use strict";

  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- Top loading bar on internal navigation ----
  (function () {
    var bar = document.createElement("div");
    bar.className = "nprogress-bar";
    document.body.appendChild(bar);
    document.addEventListener("click", function (event) {
      var link = event.target.closest("a[href]");
      if (!link || event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || link.target === "_blank") return;
      var url;
      try { url = new URL(link.href, window.location.href); } catch (e) { return; }
      if (url.origin !== window.location.origin || url.hash) return;
      requestAnimationFrame(function () { bar.style.width = "70%"; });
    });
    window.addEventListener("pageshow", function () {
      bar.classList.add("is-done");
      bar.style.width = "100%";
      setTimeout(function () { bar.style.width = "0%"; bar.classList.remove("is-done"); }, 300);
    });
  })();

  // ---- Mobile nav drawer ----
  var drawer = document.querySelector("[data-mobile-nav]");
  var backdrop = document.querySelector(".mobile-nav-backdrop");
  function openDrawer() {
    drawer.hidden = false; backdrop.hidden = false;
    requestAnimationFrame(function () { drawer.classList.add("is-open"); backdrop.classList.add("is-open"); });
    var toggle = document.querySelector("[data-open-menu]");
    if (toggle) toggle.setAttribute("aria-expanded", "true");
  }
  function closeDrawer() {
    drawer.classList.remove("is-open"); backdrop.classList.remove("is-open");
    var toggle = document.querySelector("[data-open-menu]");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
    setTimeout(function () { drawer.hidden = true; backdrop.hidden = true; }, reducedMotion ? 0 : 360);
  }
  document.querySelectorAll("[data-open-menu]").forEach(function (btn) { btn.addEventListener("click", openDrawer); });
  document.querySelectorAll("[data-close-menu]").forEach(function (el) { el.addEventListener("click", closeDrawer); });

  // ---- Header: shadow/blur once scrolled ----
  var header = document.querySelector(".site-header");
  if (header) {
    var setHeaderState = function () { header.classList.toggle("is-scrolled", window.scrollY > 8); };
    setHeaderState();
    window.addEventListener("scroll", setHeaderState, { passive: true });
  }

  // ---- Back-to-top button ----
  (function () {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "back-to-top";
    btn.setAttribute("aria-label", "Back to top");
    btn.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
    document.body.appendChild(btn);
    window.addEventListener("scroll", function () { btn.classList.toggle("is-visible", window.scrollY > 700); }, { passive: true });
    btn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: reducedMotion ? "auto" : "smooth" }); });
  })();

  // ---- Scroll-reveal: fade cards/sections up as they enter the viewport ----
  (function () {
    if (reducedMotion || !("IntersectionObserver" in window)) return;
    var targets = document.querySelectorAll(
      ".card, .section-head, .promo-panel, .story-copy, .story-quote, .category-grid > li, .artisan-card, .post-card"
    );
    if (!targets.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.add("is-visible"); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    targets.forEach(function (el, i) {
      el.classList.add("reveal", "reveal-stagger");
      el.style.setProperty("--stagger", i % 6);
      io.observe(el);
    });
  })();

  // ---- Hero slider (crossfade via CSS .is-active; JS just swaps the class) ----
  document.querySelectorAll("[data-slider]").forEach(function (slider) {
    var slides = Array.prototype.slice.call(slider.querySelectorAll("[data-slide]"));
    var dots = Array.prototype.slice.call(slider.querySelectorAll("[data-slide-dot]"));
    if (slides.length < 2) return;
    var index = 0, timer;

    function show(i) {
      index = (i + slides.length) % slides.length;
      slides.forEach(function (s, n) { s.classList.toggle("is-active", n === index); });
      dots.forEach(function (d, n) { d.classList.toggle("is-active", n === index); });
    }
    function restart() { clearInterval(timer); timer = setInterval(function () { show(index + 1); }, 6000); }

    var prev = slider.querySelector("[data-slide-prev]"), next = slider.querySelector("[data-slide-next]");
    if (prev) prev.addEventListener("click", function () { show(index - 1); restart(); });
    if (next) next.addEventListener("click", function () { show(index + 1); restart(); });
    dots.forEach(function (dot, n) { dot.addEventListener("click", function () { show(n); restart(); }); });
    slider.addEventListener("mouseenter", function () { clearInterval(timer); });
    slider.addEventListener("mouseleave", restart);
    show(0);
    restart();
  });

  // ---- Product gallery thumbnails ----
  document.querySelectorAll("[data-photo]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      var main = document.getElementById("main-photo");
      if (!main) return;
      event.preventDefault();
      main.style.opacity = "0";
      setTimeout(function () { main.src = link.getAttribute("href"); main.style.opacity = "1"; }, reducedMotion ? 0 : 150);
      document.querySelectorAll("[data-photo]").forEach(function (t) { t.classList.remove("is-active"); });
      link.classList.add("is-active");
    });
  });
  var mainPhoto = document.getElementById("main-photo");
  if (mainPhoto) mainPhoto.style.transition = "opacity 0.2s ease";

  // ---- Wishlist toggle (progressive enhancement over the plain form POST) ----
  document.addEventListener("submit", function (event) {
    var form = event.target.closest("[data-wishlist-form]");
    if (!form || !window.fetch) return;
    event.preventDefault();
    var button = form.querySelector("[data-wishlist-toggle]");
    fetch(form.action, {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      body: new FormData(form),
    })
      .then(function (res) {
        if (res.status === 401) return res.json().then(function (data) { window.location.href = data.login_url; });
        return res.json();
      })
      .then(function (data) {
        if (!data || !button) return;
        button.classList.toggle("is-active", data.wishlisted);
        button.setAttribute("aria-pressed", data.wishlisted ? "true" : "false");
        button.innerHTML = data.wishlisted
          ? '<svg viewBox="0 0 24 24" width="17" height="17" fill="currentColor" stroke="currentColor" stroke-width="1.8"><path d="M12 21S4 14.6 4 9.3C4 6.4 6.3 4 9.2 4c1.7 0 3.2.9 2.8.8C12.8 4 14.3 4 16 4c2.9 0 5.2 2.4 5.2 5.3C21.2 14.6 12 21 12 21z"/></svg>'
          : '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 21S4 14.6 4 9.3C4 6.4 6.3 4 9.2 4c1.7 0 3.2.9 2.8.8C12.8 4 14.3 4 16 4c2.9 0 5.2 2.4 5.2 5.3C21.2 14.6 12 21 12 21z"/></svg>';
        if (!reducedMotion) {
          button.classList.remove("is-popping");
          void button.offsetWidth; // restart the animation even if toggled twice quickly
          button.classList.add("is-popping");
        }
      })
      .catch(function () { form.submit(); }); // fall back to a normal request if the fetch failed
  });

  // ---- Cart badge: bounce once if this page load followed an "added to cart" message ----
  (function () {
    var addedToCart = Array.prototype.some.call(
      document.querySelectorAll(".message-success"),
      function (m) { return /added/i.test(m.textContent) && /cart/i.test(m.textContent); }
    );
    var badge = document.querySelector(".cart-icon .badge");
    if (addedToCart && badge && !reducedMotion) {
      badge.classList.add("is-bouncing");
      setTimeout(function () { badge.classList.remove("is-bouncing"); }, 550);
    }
  })();

  // ---- Toast-style messages: entrance is CSS; this adds the auto-dismiss timer ----
  (function () {
    document.querySelectorAll(".messages .message").forEach(function (msg, i) {
      if (msg.classList.contains("message-error")) return; // keep errors visible until the person moves on
      var delay = 4000 + i * 350;
      msg.style.setProperty("--dismiss-after", delay + "ms");
      msg.setAttribute("data-autodismiss", "");
      setTimeout(function () {
        msg.classList.add("is-leaving");
        setTimeout(function () { msg.remove(); }, reducedMotion ? 0 : 380);
      }, delay);
    });
  })();

  // ---- PIN code delivery checker (estimates only; no real courier lookup) ----
  document.querySelectorAll("[data-pincode-check]").forEach(function (box) {
    var input = box.querySelector("[data-pincode-input]");
    var button = box.querySelector("[data-pincode-submit]");
    var result = box.querySelector("[data-pincode-result]");
    var dispatchDays = parseInt(box.getAttribute("data-dispatch-days"), 10) || 3;

    function addDays(n) {
      var d = new Date();
      var added = 0;
      while (added < n) {
        d.setDate(d.getDate() + 1);
        if (d.getDay() !== 0) added++; // skip Sundays
      }
      return d;
    }
    function fmt(d) { return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }); }

    function check() {
      var pin = input.value.replace(/\D/g, "");
      result.hidden = false;
      result.classList.remove("is-error");
      if (!/^[1-9][0-9]{5}$/.test(pin)) {
        result.classList.add("is-error");
        result.textContent = "Enter a valid 6-digit PIN code.";
        return;
      }
      var early = addDays(dispatchDays + 3);
      var late = addDays(dispatchDays + 7);
      result.innerHTML = "Delivery by <strong>" + fmt(early) + " \u2013 " + fmt(late) + "</strong> to " + pin + ". Cash on delivery may be available.";
    }
    button.addEventListener("click", check);
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); check(); } });
  });

  // ---- Sticky mobile "Add to cart" bar on the product page ----
  (function () {
    var form = document.querySelector(".buy-form");
    if (!form || !("IntersectionObserver" in window)) return;
    var priceEl = document.querySelector(".buy-price");
    var nameEl = document.querySelector(".buy h1");
    var bar = document.createElement("div");
    bar.className = "sticky-buy";
    bar.innerHTML =
      '<div class="sticky-buy-info"><strong>' + (nameEl ? nameEl.textContent : "") + '</strong>' +
      '<span>' + (priceEl ? priceEl.childNodes[0].textContent.trim() : "") + '</span></div>';
    var btn = document.createElement("button");
    btn.type = "submit";
    btn.className = "btn btn-terracotta";
    btn.textContent = "Add to Cart";
    btn.addEventListener("click", function () {
      var realSubmit = form.querySelector('button[type="submit"]');
      if (realSubmit) realSubmit.click();
    });
    bar.appendChild(btn);
    document.body.appendChild(bar);
    bar.classList.add("can-show");

    var io = new IntersectionObserver(function (entries) {
      var visible = entries[0].isIntersecting;
      bar.classList.toggle("is-visible", !visible);
      document.body.classList.toggle("has-sticky-buy", !visible);
    }, { threshold: 0 });
    io.observe(form);
  })();
})();
