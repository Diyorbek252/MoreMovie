/* ==========================================================================
   MORE-MOVIE — Do'kon: mahsulot xaridi (AJAX)
   ========================================================================== */

(function () {
  "use strict";

  const MM = window.MM;
  if (!MM) return;

  const config = document.body.dataset;
  const ENDPOINTS = { purchase: config.urlPurchase || "/api/shop/purchase/" };

  document.addEventListener("click", async function (event) {
    const button = event.target.closest(".js-buy");
    if (!button || button.disabled) return;

    button.disabled = true;
    button.classList.add("is-loading");

    try {
      const data = await MM.postJSON(ENDPOINTS.purchase, { product: button.dataset.product });

      const balanceEls = document.querySelectorAll("#cinepoint-balance");
      balanceEls.forEach(function (el) { el.textContent = data.balance; });

      MM.toast(data.message, "success");
      button.textContent = "Xarid qilindi";
    } catch (error) {
      MM.toast(error.message, "error");
      button.disabled = false;
    } finally {
      button.classList.remove("is-loading");
    }
  });
})();
