// Bhoomija Designs storefront JS: mobile nav drawer, hero slider, product gallery
// thumbnails, and wishlist heart toggled via fetch (falls back to a normal form
// POST if JavaScript is off or the request fails).
(function () {
  "use strict";

  // ---- Mobile nav drawer ----
  var drawer = document.querySelector("[data-mobile-nav]");
  var backdrop = document.querySelector(".mobile-nav-backdrop");
  document.querySelectorAll("[data-open-menu]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      drawer.hidden = false; backdrop.hidden = false; btn.setAttribute("aria-expanded", "true");
    });
  });
  document.querySelectorAll("[data-close-menu]").forEach(function (el) {
    el.addEventListener("click", function () {
      drawer.hidden = true; backdrop.hidden = true;
      var toggle = document.querySelector("[data-open-menu]");
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    });
  });

  // ---- Hero slider ----
  document.querySelectorAll("[data-slider]").forEach(function (slider) {
    var slides = Array.prototype.slice.call(slider.querySelectorAll("[data-slide]"));
    var dots = Array.prototype.slice.call(slider.querySelectorAll("[data-slide-dot]"));
    if (slides.length < 2) return;
    var index = 0, timer;

    function show(i) {
      index = (i + slides.length) % slides.length;
      slides.forEach(function (s, n) { s.hidden = n !== index; s.classList.toggle("is-active", n === index); });
      dots.forEach(function (d, n) { d.classList.toggle("is-active", n === index); });
    }
    function restart() { clearInterval(timer); timer = setInterval(function () { show(index + 1); }, 6000); }

    var prev = slider.querySelector("[data-slide-prev]"), next = slider.querySelector("[data-slide-next]");
    if (prev) prev.addEventListener("click", function () { show(index - 1); restart(); });
    if (next) next.addEventListener("click", function () { show(index + 1); restart(); });
    dots.forEach(function (dot, n) { dot.addEventListener("click", function () { show(n); restart(); }); });
    slider.addEventListener("mouseenter", function () { clearInterval(timer); });
    slider.addEventListener("mouseleave", restart);
    restart();
  });

  // ---- Product gallery thumbnails ----
  document.querySelectorAll("[data-photo]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      var main = document.getElementById("main-photo");
      if (!main) return;
      event.preventDefault();
      main.src = link.getAttribute("href");
      document.querySelectorAll("[data-photo]").forEach(function (t) { t.classList.remove("is-active"); });
      link.classList.add("is-active");
    });
  });

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
      })
      .catch(function () { form.submit(); }); // fall back to a normal request if the fetch failed
  });
})();
