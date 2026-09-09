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
      // Yangi endpointlar generik "state" kalitini qaytaradi — shuning
      // uchun u birinchi tekshiriladi; eski uchta endpoint (publish/
      // featured/blocked) o'z nomlari bilan ishlayveradi.
      const state = data.state !== undefined ? data.state
                  : data.published !== undefined ? data.published
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

    // data-url mavjud bo'lsa o'shani ishlatamiz (yangi shablonlar buni
    // beradi); eski shablonlarda hali yo'q bo'lsa avvalgi qattiq yozilgan
    // yo'lga tushamiz — shu bilan eski review_list.html ham ishlayveradi.
    const url = button.dataset.url || ("/dashboard/api/review/" + reviewId + "/" + action + "/");

    try {
      const data = await MM.postJSON(url, {});

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
     Do'kon — buyurtma amallari (yetkazish / bekor qilish)
     -------------------------------------------------------------------- */

  document.addEventListener("click", async function (event) {
    const button = event.target.closest(".js-order-action");
    if (!button || button.disabled) return;

    if (button.dataset.confirm && !window.confirm(button.dataset.confirm)) {
      return;
    }

    const row = button.closest("[data-order]");
    const buttons = row ? row.querySelectorAll("button") : [button];
    buttons.forEach(function (b) { b.disabled = true; });

    try {
      const data = await MM.postJSON(button.dataset.url, {});
      MM.toast(data.message, "success");

      if (row) {
        row.classList.add("is-gone");
        setTimeout(function () { row.remove(); }, 260);
      }
    } catch (error) {
      MM.toast(error.message, "error");
      buttons.forEach(function (b) { b.disabled = false; });
    }
  });

  /* --------------------------------------------------------------------
     Foydalanuvchi balansini qo'lda tuzatish (modal forma)

     Sahifada bitta umumiy modal bor (#balance-modal) — jadvaldagi har bir
     "Balans" tugmasi bosilganda forma manzili va sarlavha shu tugmaning
     data-atributlaridan dinamik to'ldiriladi (modalni ochish o'zi
     main.js dagi umumiy data-modal-open delegatsiyasi orqali ishlaydi).
     -------------------------------------------------------------------- */

  document.addEventListener("click", function (event) {
    const opener = event.target.closest(".js-balance-open");
    if (!opener) return;

    const form = document.getElementById("balance-adjust-form");
    if (!form) return;

    form.dataset.url = opener.dataset.url;
    form.dataset.userId = opener.dataset.userId;

    const label = document.getElementById("balance-modal-username");
    if (label) label.textContent = opener.dataset.username;
  });

  const balanceForm = document.getElementById("balance-adjust-form");

  if (balanceForm) {
    balanceForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      const submit = balanceForm.querySelector("button[type=submit]");
      const amountInput = balanceForm.querySelector("[name=amount]");
      const noteInput = balanceForm.querySelector("[name=note]");
      const errorBox = balanceForm.querySelector(".js-balance-error");

      submit.disabled = true;
      if (errorBox) errorBox.hidden = true;

      try {
        const data = await MM.postJSON(balanceForm.dataset.url, {
          amount: amountInput.value,
          note: noteInput.value,
        });

        MM.toast(data.message, "success");

        const row = document.querySelector('[data-balance-for="' + balanceForm.dataset.userId + '"]');
        if (row) row.textContent = data.balance;

        const modal = balanceForm.closest(".modal");
        if (modal) modal.classList.remove("is-open");
        amountInput.value = "";
        noteInput.value = "";
      } catch (error) {
        if (errorBox) {
          errorBox.textContent = error.message;
          errorBox.hidden = false;
        } else {
          MM.toast(error.message, "error");
        }
      } finally {
        submit.disabled = false;
      }
    });
  }

  /* --------------------------------------------------------------------
     Rasm yuklashda oldindan ko'rish
     -------------------------------------------------------------------- */

  // Delegatsiya orqali — keyinroq DOM'ga qo'shiladigan fayl maydonlari
  // (masalan formset orqali qo'shilgan epizod qatorlari) uchun ham ishlaydi.
  document.addEventListener("change", function (event) {
    const input = event.target.closest('input[type="file"]');
    if (!input) return;

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

  /* --------------------------------------------------------------------
     Ko'rishlar grafigi — kutubxonasiz inline SVG
     -------------------------------------------------------------------- */

  // Bir sahifada bir nechta grafik bo'lishi mumkin (masalan Analitika
  // sahifasida) — shuning uchun class bo'yicha barchasi qidiriladi.
  // Eski `#views-chart` id'si ham saqlanadi (shablon ikkalasini beradi).
  document.querySelectorAll(".js-chart[data-chart]").forEach(function (chartHost) {
    let points;
    try {
      points = JSON.parse(chartHost.dataset.chart);
    } catch (error) {
      points = [];
    }

    if (points.length) {
      chartHost.innerHTML = renderChart(points);
    }
  });

  /**
   * Kunlik qiymatlardan chiziqli grafik SVG si yasaydi.
   * @param {Array<{label: string, value: number}>} data
   */
  function renderChart(data) {
    const width = 800;
    const height = 200;
    // Nuqta ustidagi son yorlig'i uchun yetarli joy — avval 12px edi va
    // eng baland nuqtaning raqami grafik chegarasidan tashqarida
    // ko'rinmay qolar, hover qilmaguncha son umuman ko'rinmas edi.
    const padTop = 26;
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

    // Sonni faqat hover'da (title tooltip) emas, doim ko'rinadigan
    // qilib nuqta ustiga yozamiz — aks holda foydalanuvchi qiymatni
    // ko'rish uchun har bir nuqtani ustma-ust bosib chiqishi kerak edi.
    const values = coords
      .map(function (p) {
        return (
          '<text class="chart__value" x="' + p.x.toFixed(1) + '" y="' + (p.y - 8).toFixed(1) +
          '" text-anchor="middle">' + p.value + "</text>"
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
      values +
      labels +
      "</svg>"
    );
  }

  /* --------------------------------------------------------------------
     Sudrab tartiblash — bosh sahifa bo'limlari (.sortable)
     Native HTML5 drag-and-drop, tashqi kutubxonasiz.
     -------------------------------------------------------------------- */

  const sortableList = document.getElementById("section-sortable");

  if (sortableList) {
    const getRows = function () {
      return Array.prototype.slice.call(sortableList.querySelectorAll(".sortable__row"));
    };

    getRows().forEach(function (row) {
      row.setAttribute("draggable", "true");
    });

    let draggedRow = null;

    sortableList.addEventListener("dragstart", function (event) {
      const row = event.target.closest(".sortable__row");
      if (!row) return;
      draggedRow = row;
      row.classList.add("is-dragging");
      event.dataTransfer.effectAllowed = "move";
      // Firefox'da dataTransfer.setData chaqirilmasa drag boshlanmaydi.
      event.dataTransfer.setData("text/plain", row.dataset.id);
    });

    sortableList.addEventListener("dragend", function () {
      if (draggedRow) draggedRow.classList.remove("is-dragging");
      getRows().forEach(function (row) { row.classList.remove("is-drop-target"); });
      draggedRow = null;
    });

    sortableList.addEventListener("dragover", function (event) {
      // Standart holatda "drop" hodisasi faqat preventDefault() chaqirilsa ishlaydi.
      event.preventDefault();
      const row = event.target.closest(".sortable__row");
      if (!row || row === draggedRow) return;
      getRows().forEach(function (r) { r.classList.remove("is-drop-target"); });
      row.classList.add("is-drop-target");
      event.dataTransfer.dropEffect = "move";
    });

    sortableList.addEventListener("drop", async function (event) {
      event.preventDefault();
      const target = event.target.closest(".sortable__row");
      if (!target || !draggedRow || target === draggedRow) return;

      const rows = getRows();
      const draggedIndex = rows.indexOf(draggedRow);
      const targetIndex = rows.indexOf(target);

      // Qaysi tomonga tashlanganiga qarab, DOM'da tegishli joyga ko'chiramiz.
      if (draggedIndex < targetIndex) {
        target.after(draggedRow);
      } else {
        target.before(draggedRow);
      }
      target.classList.remove("is-drop-target");

      const order = getRows().map(function (row) { return parseInt(row.dataset.id, 10); });

      try {
        const data = await MM.postJSON(sortableList.dataset.url, { order: order });
        MM.toast(data.message, "success");
      } catch (error) {
        MM.toast(error.message, "error");
      }
    });
  }
})();
