/* ==========================================================================
   MORE-MOVIE — Boshqaruv paneli skripti
   Toggle switch'lar, sharh moderatsiyasi, rasm preview, SVG grafik
   ========================================================================== */

(function () {
  "use strict";

  const MM = window.MM;
  if (!MM) return;

  /* --------------------------------------------------------------------
     Toggle switch'lar (chop etish / tanlangan / bloklash)
     -------------------------------------------------------------------- */

  document.addEventListener("click", async function (event) {
    const toggle = event.target.closest(".js-toggle");
    if (!toggle) return;

    const url = toggle.dataset.url;
    if (!url || toggle.disabled) return;

    toggle.disabled = true;

    try {
      const data = await MM.postJSON(url, {});

      // Server qaysi maydonni qaytarganiga qarab holatni aniqlaymiz.
      const state = data.published !== undefined ? data.published
                  : data.featured !== undefined ? data.featured
                  : data.blocked;

      toggle.classList.toggle("is-on", Boolean(state));
      toggle.setAttribute("aria-checked", String(Boolean(state)));

      if (data.message) MM.toast(data.message, "success");
    } catch (error) {
      MM.toast(error.message, "error");
    } finally {
      toggle.disabled = false;
    }
  });

  /* --------------------------------------------------------------------
     Sharh moderatsiyasi
     -------------------------------------------------------------------- */

  document.addEventListener("click", async function (event) {
    const button = event.target.closest(".js-moderate");
    if (!button) return;

    const reviewId = button.dataset.review;
    const action = button.dataset.action;

    if (action === "delete" && !window.confirm("Sharh butunlay o'chiriladi. Davom etamizmi?")) {
      return;
    }

    const card = document.querySelector('[data-review="' + reviewId + '"]');
    const buttons = card ? card.querySelectorAll("button") : [button];
    buttons.forEach(function (b) { b.disabled = true; });

    try {
      const data = await MM.postJSON(
        "/dashboard/api/review/" + reviewId + "/" + action + "/",
        {}
      );

      MM.toast(data.message, action === "approve" ? "success" : "info");

      // Kartani ro'yxatdan olib tashlaymiz.
      if (card) {
        card.classList.add("is-gone");
        setTimeout(function () { card.remove(); }, 260);
      }
    } catch (error) {
      MM.toast(error.message, "error");
      buttons.forEach(function (b) { b.disabled = false; });
    }
  });

  /* --------------------------------------------------------------------
     Rasm yuklashda oldindan ko'rish
     -------------------------------------------------------------------- */

  document.querySelectorAll('input[type="file"]').forEach(function (input) {
    input.addEventListener("change", function () {
      const file = input.files && input.files[0];
      if (!file || !file.type.startsWith("image/")) return;

      // Oldingi preview ni almashtiramiz.
      let preview = input.parentElement.querySelector(".preview");
      if (!preview) {
        preview = document.createElement("div");
        preview.className = "preview";
        const newImg = document.createElement("img");
        newImg.alt = "Tanlangan rasm";
        preview.appendChild(newImg);
        input.parentElement.appendChild(preview);
      }

      const img = preview.querySelector("img");
      const previousUrl = img.dataset.objectUrl;
      // Eski object URL ni bo'shatamiz — xotira sizib ketmasin.
      if (previousUrl) URL.revokeObjectURL(previousUrl);

      const url = URL.createObjectURL(file);
      img.src = url;
      img.dataset.objectUrl = url;
    });
  });

  /* --------------------------------------------------------------------
     Ko'rishlar grafigi — kutubxonasiz inline SVG
     -------------------------------------------------------------------- */

  const chartHost = document.getElementById("views-chart");

  if (chartHost && chartHost.dataset.chart) {
    let points;
    try {
      points = JSON.parse(chartHost.dataset.chart);
    } catch (error) {
      points = [];
    }

    if (points.length) {
      chartHost.innerHTML = renderChart(points);
    }
  }

  /**
   * Kunlik qiymatlardan chiziqli grafik SVG si yasaydi.
   * @param {Array<{label: string, value: number}>} data
   */
  function renderChart(data) {
    const width = 800;
    const height = 200;
    const padTop = 12;
    const padBottom = 26;
    const usableHeight = height - padTop - padBottom;

    // Eng katta qiymat 0 bo'lsa ham nolga bo'linmasligi uchun kamida 1.
    const max = Math.max.apply(null, data.map(function (d) { return d.value; })) || 1;
    const step = data.length > 1 ? width / (data.length - 1) : width;

    const coords = data.map(function (d, i) {
      const x = i * step;
      const y = padTop + usableHeight - (d.value / max) * usableHeight;
      return { x: x, y: y, label: d.label, value: d.value };
    });

    const line = coords
      .map(function (p, i) { return (i === 0 ? "M" : "L") + p.x.toFixed(1) + " " + p.y.toFixed(1); })
      .join(" ");

    // To'ldirish uchun chiziqni pastdan yopamiz.
    const area =
      line +
      " L" + width + " " + (height - padBottom) +
      " L0 " + (height - padBottom) + " Z";

    const dots = coords
      .map(function (p) {
        return (
          '<circle class="chart__dot" cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) +
          '" r="3"><title>' + p.label + ": " + p.value + " ko'rish</title></circle>"
        );
      })
      .join("");

    // Har bir sanani chizsak siqilib ketadi — bittasini oralatib ko'rsatamiz.
    const labels = coords
      .map(function (p, i) {
        if (i % 2 !== 0 && i !== coords.length - 1) return "";
        const anchor = i === 0 ? "start" : i === coords.length - 1 ? "end" : "middle";
        return (
          '<text class="chart__label" x="' + p.x.toFixed(1) + '" y="' + (height - 8) +
          '" text-anchor="' + anchor + '">' + p.label + "</text>"
        );
      })
      .join("");

    return (
      // preserveAspectRatio berilmaydi — aks holda matn cho'zilib ketadi.
      '<svg class="chart" viewBox="0 0 ' + width + " " + height +
      '" role="img" aria-label="Kunlik ko\'rishlar grafigi">' +
      "<defs><linearGradient id='chart-gradient' x1='0' y1='0' x2='0' y2='1'>" +
      "<stop offset='0%' stop-color='#E50914' stop-opacity='0.35'/>" +
      "<stop offset='100%' stop-color='#E50914' stop-opacity='0'/>" +
      "</linearGradient></defs>" +
      '<path class="chart__area" d="' + area + '"/>' +
      '<path class="chart__line" d="' + line + '"/>' +
      dots +
      labels +
      "</svg>"
    );
  }
})();
