/* ==========================================================================
   MORE-MOVIE — Navbar jonli qidiruvi
   Debounce bilan AJAX, klaviatura navigatsiyasi
   ========================================================================== */

(function () {
  "use strict";

  const wrapper = document.getElementById("nav-search");
  const toggle = document.getElementById("search-toggle");
  const input = document.getElementById("search-input");
  const results = document.getElementById("search-results");

  if (!wrapper || !toggle || !input || !results) return;

  const ENDPOINT = document.body.dataset.urlSearchApi || "/api/search/";
  const DEBOUNCE_MS = 250;
  const MIN_CHARS = 2;

  let timer = null;
  let controller = null;   // oldingi so'rovni bekor qilish uchun
  let highlighted = -1;

  /* --- Ochish / yopish --- */

  function open() {
    wrapper.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
    input.focus();
  }

  function close() {
    wrapper.classList.remove("is-open");
    results.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    highlighted = -1;
  }

  toggle.addEventListener("click", function (event) {
    event.stopPropagation();
    if (wrapper.classList.contains("is-open")) {
      close();
    } else {
      open();
    }
  });

  document.addEventListener("click", function (event) {
    if (!wrapper.contains(event.target)) close();
  });

  /* --- Natijalarni chizish --- */

  /**
   * Matnni HTML ga xavfsiz joylash uchun escape qiladi.
   * Server javobi foydalanuvchi kiritgan ma'lumot bo'lishi mumkin,
   * shuning uchun innerHTML ga to'g'ridan-to'g'ri qo'yilmaydi.
   */
  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.innerHTML;
  }

  function render(items, query) {
    if (!items.length) {
      results.innerHTML =
        '<p class="search-result__empty">«' +
        escapeHtml(query) +
        '» bo\'yicha hech narsa topilmadi.</p>';
      results.classList.add("is-open");
      return;
    }

    const html = items
      .map(function (item) {
        const poster = item.poster
          ? '<img class="search-result__poster" src="' +
            escapeHtml(item.poster) +
            '" alt="" loading="lazy" width="46" height="68">'
          : '<div class="search-result__poster"></div>';

        return (
          '<a class="search-result" href="' +
          escapeHtml(item.url) +
          '" role="option">' +
          poster +
          "<div>" +
          '<div class="search-result__title">' + escapeHtml(item.title) + "</div>" +
          '<div class="search-result__meta">' +
          escapeHtml(item.year) + " · " + escapeHtml(item.quality) +
          (item.imdb ? " · IMDb " + escapeHtml(item.imdb) : "") +
          "</div></div></a>"
        );
      })
      .join("");

    results.innerHTML = html;
    results.classList.add("is-open");
    highlighted = -1;
  }

  /* --- So'rov --- */

  async function search(query) {
    // Oldingi so'rov hali tugamagan bo'lsa bekor qilamiz.
    if (controller) controller.abort();
    controller = new AbortController();

    try {
      const response = await fetch(
        ENDPOINT + "?q=" + encodeURIComponent(query),
        { signal: controller.signal, credentials: "same-origin" }
      );
      if (!response.ok) return;

      const data = await response.json();
      render(data.results || [], query);
    } catch (error) {
      // AbortError — bu kutilgan holat, e'tiborsiz qoldiramiz.
      if (error.name !== "AbortError") {
        results.classList.remove("is-open");
      }
    }
  }

  input.addEventListener("input", function () {
    const query = input.value.trim();

    clearTimeout(timer);

    if (query.length < MIN_CHARS) {
      results.classList.remove("is-open");
      if (controller) controller.abort();
      return;
    }

    // Har harfda so'rov yubormaslik uchun kutamiz.
    timer = setTimeout(function () {
      search(query);
    }, DEBOUNCE_MS);
  });

  /* --- Klaviatura --- */

  input.addEventListener("keydown", function (event) {
    const items = results.querySelectorAll(".search-result");

    if (event.key === "Escape") {
      close();
      input.blur();
      return;
    }

    if (!items.length) return;

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();

      items[highlighted] && items[highlighted].classList.remove("is-highlighted");

      if (event.key === "ArrowDown") {
        highlighted = (highlighted + 1) % items.length;
      } else {
        highlighted = highlighted <= 0 ? items.length - 1 : highlighted - 1;
      }

      items[highlighted].classList.add("is-highlighted");
      items[highlighted].scrollIntoView({ block: "nearest" });
      return;
    }

    // Enter: tanlangan natijaga o'tamiz, tanlanmagan bo'lsa forma yuboriladi.
    if (event.key === "Enter" && highlighted >= 0) {
      event.preventDefault();
      window.location.href = items[highlighted].getAttribute("href");
    }
  });

  // Klaviatura yorlig'i: "/" bosilganda qidiruv ochiladi.
  document.addEventListener("keydown", function (event) {
    const tag = (event.target.tagName || "").toLowerCase();
    if (event.key === "/" && tag !== "input" && tag !== "textarea") {
      event.preventDefault();
      open();
    }
  });
})();
