/* ==========================================================================
   MORE-MOVIE — Do'kon: mahsulot xaridi (miqdor tanlash modali + AJAX)
   Filtr paneli avtomatik yuborilishi endi umumiy joyda —
   static/js/main.js dagi "form.js-auto-filter" bilan ishlaydigan
   blokka qarang (barcha filtr formalarida bir xil naqsh).
   ========================================================================== */

(function () {
  "use strict";

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
