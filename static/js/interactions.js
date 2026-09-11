/* ==========================================================================
   MORE-MOVIE — Foydalanuvchi harakatlari (faqat tizimga kirganlar uchun)
   Watchlist, Favorite, Rating, Review — barchasi AJAX orqali
   ========================================================================== */

(function () {
  "use strict";

  const MM = window.MM;
  if (!MM) return;

  // URL lar sahifadagi data-atributlardan olinadi, kodga qattiq yozilmaydi.
  const config = document.body.dataset;

  const ENDPOINTS = {
    watchlist: config.urlWatchlist || "/api/watchlist/toggle/",
    favorite: config.urlFavorite || "/api/favorite/toggle/",
    rate: config.urlRate || "/api/rate/",
    review: config.urlReview || "/api/review/",
  };

  /* --------------------------------------------------------------------
     Watchlist va Favorite tugmalari
     -------------------------------------------------------------------- */

  /**
   * Bosilgan tugmani serverga yuboradi va holatini yangilaydi.
   * Sahifada bir xil filmning bir nechta tugmasi bo'lishi mumkin
   * (masalan karta va detail sahifasi) — barchasi sinxronlanadi.
   */
  async function toggleCollection(button, url, selector) {
    const movieId = button.dataset.movie;
    if (!movieId || button.disabled) return;

    button.disabled = true;

    try {
      const data = await MM.postJSON(url, { movie: movieId });

      // Shu filmga tegishli barcha tugmalarni yangilaymiz.
      document
        .querySelectorAll(selector + '[data-movie="' + movieId + '"]')
        .forEach(function (el) {
          el.classList.toggle("is-active", data.added);
          el.setAttribute("aria-pressed", String(data.added));

          // Ikonka almashtirish (outline/filled) — player.js dagi
          // play/pause bilan bir xil naqsh. Faqat shunday belgilangan
          // tugmalarda ishlaydi, qolganlarida (masalan Favorite) hech
          // narsa topilmagani uchun jim o'tkaziladi.
          el.querySelectorAll("[data-icon]").forEach(function (holder) {
            holder.hidden = (holder.dataset.icon === "filled") !== data.added;
          });

          const label = el.querySelector(".js-toggle-label");
          if (label) {
            label.textContent = data.added ? label.dataset.onLabel : label.dataset.offLabel;
          }
        });

      // Kartalardagi doim ko'rinadigan "Watchlist'da" belgisi.
      document
        .querySelectorAll('.js-watchlist-badge[data-movie="' + movieId + '"]')
        .forEach(function (badge) {
          badge.hidden = !data.added;
        });

      MM.toast(data.message, data.added ? "success" : "info");
    } catch (error) {
      MM.toast(error.message, "error");
    } finally {
      button.disabled = false;
    }
  }

  // Delegatsiya — dinamik qo'shilgan kartalar ham ishlaydi.
  document.addEventListener("click", function (event) {
    const watchlistBtn = event.target.closest(".js-watchlist");
    if (watchlistBtn) {
      event.preventDefault();
      toggleCollection(watchlistBtn, ENDPOINTS.watchlist, ".js-watchlist");
      return;
    }

    const favoriteBtn = event.target.closest(".js-favorite");
    if (favoriteBtn) {
      event.preventDefault();
      toggleCollection(favoriteBtn, ENDPOINTS.favorite, ".js-favorite");
    }
  });

  /* --------------------------------------------------------------------
     Watchlist / Favorites sahifasidan olib tashlash
     Element butunlay ro'yxatdan yo'qoladi.
     -------------------------------------------------------------------- */

  document.addEventListener("click", async function (event) {
    const removeBtn = event.target.closest(".js-remove-entry");
    if (!removeBtn) return;

    event.preventDefault();

    const movieId = removeBtn.dataset.movie;
    const kind = removeBtn.dataset.kind; // "watchlist" yoki "favorite"
    const url = kind === "favorite" ? ENDPOINTS.favorite : ENDPOINTS.watchlist;

    removeBtn.disabled = true;

    try {
      await MM.postJSON(url, { movie: movieId });

      const card = removeBtn.closest("[data-entry]");
      if (card) {
        card.style.transition = "opacity 240ms, transform 240ms";
        card.style.opacity = "0";
        card.style.transform = "scale(0.94)";
        setTimeout(function () {
          const grid = card.parentElement;
          card.remove();
          // Ro'yxat bo'shab qolsa sahifani yangilaymiz — "empty state" chiqsin.
          if (grid && !grid.children.length) window.location.reload();
        }, 240);
      }

      MM.toast("Ro'yxatdan olib tashlandi", "info");
    } catch (error) {
      MM.toast(error.message, "error");
      removeBtn.disabled = false;
    }
  });

  /* --------------------------------------------------------------------
     Yulduz reyting
     -------------------------------------------------------------------- */

  const starsInput = document.querySelector(".js-rating");
  let paintStars = function () {};

  if (starsInput) {
    const buttons = Array.prototype.slice.call(starsInput.querySelectorAll("button"));

    /** Berilgan bahogacha bo'lgan yulduzlarni yoqadi. */
    const paint = function (score) {
      buttons.forEach(function (button, index) {
        const icon = button.querySelector("svg");
        if (icon) icon.classList.toggle("is-filled", index < score);
      });
    };
    paintStars = paint;

    const current = parseInt(starsInput.dataset.score || "0", 10);
    paint(current);

    // Sichqoncha yulduz ustida turganda bahoni oldindan ko'rsatamiz.
    buttons.forEach(function (button, index) {
      button.addEventListener("mouseenter", function () { paint(index + 1); });
    });

    starsInput.addEventListener("mouseleave", function () {
      paint(parseInt(starsInput.dataset.score || "0", 10));
    });

    starsInput.addEventListener("click", async function (event) {
      const button = event.target.closest("button");
      if (!button) return;

      const score = buttons.indexOf(button) + 1;
      const movieId = starsInput.dataset.movie;

      try {
        const data = await MM.postJSON(ENDPOINTS.rate, { movie: movieId, score: score });

        starsInput.dataset.score = String(data.score);
        paint(data.score);

        // Sahifadagi sayt bahosini yangilaymiz. Bu faqat sharhi tasdiqlangan
        // foydalanuvchilar hisobga olinganda mavjud bo'ladi (data.user_rating
        // null bo'lishi mumkin — sharh hali moderatsiyada).
        if (data.user_rating !== null) {
          const avgEl = document.querySelector(".js-avg-rating");
          if (avgEl) avgEl.textContent = data.user_rating;

          document.querySelectorAll(".js-user-rating").forEach(
            function (el) { el.hidden = false; }
          );
        }

        MM.toast(data.message, "success");
      } catch (error) {
        MM.toast(error.message, "error");
        paint(parseInt(starsInput.dataset.score || "0", 10));
      }
    });
  }

  /* --------------------------------------------------------------------
     Sharh yuborish
     -------------------------------------------------------------------- */

  const reviewForm = document.querySelector(".js-review-form");

  if (reviewForm) {
    reviewForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      const textarea = reviewForm.querySelector("textarea");
      const submit = reviewForm.querySelector("button[type=submit]");
      const comment = textarea ? textarea.value.trim() : "";

      if (comment.length < 10) {
        MM.toast("Sharh kamida 10 ta belgidan iborat bo'lishi kerak.", "warning");
        return;
      }

      submit.classList.add("is-loading");

      try {
        const data = await MM.postJSON(ENDPOINTS.review, {
          movie: reviewForm.dataset.movie,
          comment: comment,
        });

        MM.toast(data.message, "success");

        // Moderatsiya haqida eslatmani ko'rsatamiz va maydonni tozalaymiz —
        // sahifani qayta yuklaganda mavjud sharh tahrirlash uchun baribir
        // qayta to'ldiriladi (server shablonida), bu yerda faqat shu
        // instansiya uchun "yuborildi" holatini ko'rsatamiz.
        if (textarea) textarea.value = "";

        const notice = reviewForm.querySelector(".js-review-notice");
        if (notice) notice.hidden = false;

        // Yulduz bahosi ko'rsatkichini vizual ravishda tozalaymiz — baza
        // o'zgarmaydi, faqat sahifada eski baho ko'rinib turmasligi uchun.
        if (starsInput) {
          starsInput.dataset.score = "0";
          paintStars(0);
        }
        const ratingStatus = document.querySelector(".js-rating-status");
        if (ratingStatus) ratingStatus.textContent = "Hali baholamagansiz";
      } catch (error) {
        MM.toast(error.message, "error");
      } finally {
        submit.classList.remove("is-loading");
      }
    });
  }
})();
