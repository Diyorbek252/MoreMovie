/* ==========================================================================
   MORE-MOVIE — Do'kon: filtr paneli (avtomatik yuborish) va mahsulot xaridi
   (miqdor tanlash modali + AJAX)
   ========================================================================== */

(function () {
  "use strict";

  /* --------------------------------------------------------------------
     Filtr paneli — submit tugmasi yo'q, maydon o'zgarishi bilan formani
     o'zi yuboradi. Anonim foydalanuvchi ham qidiruv/saralashdan
     foydalanadi, shuning uchun bu blok MM/autentifikatsiyaga bog'liq emas.
     -------------------------------------------------------------------- */

  const filterForm = document.querySelector(".js-auto-filter");

  if (filterForm) {
    // Select va toggle — o'zgarishi bilanoq (kutishsiz) yuboriladi.
    filterForm.querySelectorAll("select, input[type=checkbox]").forEach(function (field) {
      field.addEventListener("change", function () { filterForm.submit(); });
    });

    // Qidiruv matni — har harfda yubormasdan, yozish to'xtaganda (debounce).
    const searchInput = filterForm.querySelector('input[name="q"]');
    if (searchInput) {
      let debounceTimer;
      searchInput.addEventListener("input", function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () { filterForm.submit(); }, 600);
      });
    }
  }

  /* --------------------------------------------------------------------
     Mahsulot xaridi — miqdor tanlash modali
     -------------------------------------------------------------------- */

  const MM = window.MM;
  if (!MM) return;

  const modal = document.getElementById("buy-modal");
  if (!modal) return;

  const config = document.body.dataset;
  const ENDPOINTS = { purchase: config.urlPurchase || "/api/shop/purchase/" };

  const form = document.getElementById("buy-form");
  const nameEl = document.getElementById("buy-modal-name");
  const quantityInput = document.getElementById("buy-quantity");
  const totalEl = document.getElementById("buy-total");
  const errorBox = form.querySelector(".js-buy-error");

  let currentPrice = 0;

  /** Miqdor maydonidagi qiymatga qarab umumiy summani qayta hisoblaydi. */
  const recalcTotal = function () {
    const quantity = Math.max(1, parseInt(quantityInput.value, 10) || 1);
    totalEl.textContent = String(currentPrice * quantity);
  };

  // "Sotib olish" tugmasi bosilganda — modal ochilishi data-modal-open
  // orqali (main.js) avtomatik amalga oshadi, bu yerda faqat forma
  // ma'lumotlarini shu mahsulotga moslab to'ldiramiz.
  document.addEventListener("click", function (event) {
    const opener = event.target.closest(".js-buy-open");
    if (!opener) return;

    form.dataset.product = opener.dataset.product;
    currentPrice = parseInt(opener.dataset.price, 10) || 0;
    nameEl.textContent = opener.dataset.name;

    quantityInput.value = 1;
    if (opener.dataset.stock !== undefined) {
      quantityInput.max = opener.dataset.stock;
    } else {
      quantityInput.removeAttribute("max");
    }

    errorBox.hidden = true;
    recalcTotal();
  });

  quantityInput.addEventListener("input", recalcTotal);

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const submit = form.querySelector("button[type=submit]");
    const quantity = Math.max(1, parseInt(quantityInput.value, 10) || 1);

    submit.disabled = true;
    errorBox.hidden = true;

    try {
      const data = await MM.postJSON(ENDPOINTS.purchase, {
        product: form.dataset.product,
        quantity: quantity,
      });

      MM.toast(data.message, "success");
      modal.classList.remove("is-open");

      // Balans va zaxira holati bir nechta kartaga ta'sir qiladi
      // (masalan boshqa mahsulot endi balans yetarli emas bo'lib
      // qolishi mumkin) — sahifani qayta yuklab, hammasini serverdan
      // to'g'ri holatda qayta chizamiz.
      window.location.reload();
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
      submit.disabled = false;
    }
  });
})();
