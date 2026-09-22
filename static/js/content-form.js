/* ==========================================================================
   MORE-MOVIE — Kontent formasi (film, serial, fasl, epizod)

   Forma bitta `<form>` bo'lib qoladi (submit hamma maydonni yuboradi),
   bu skript esa faqat ko'rinish bilan ishlaydi:

     · bosqich (tab) almashtirish va xatoli bo'limni belgilash
     · fayl maydonlari — sudrab tashlash, oldindan ko'rish
     · janr/kategoriya/rejissyor ro'yxatlarida qidiruv va hisob
     · belgilar hisoblagichi, jonli karta ko'rinishi
     · litsenziya/video holatiga qarab "ko'rish / yuklash" natijasi

   `<form data-content-form>` bo'lgan har qanday sahifada ishlaydi.
   Bo'limlar, ro'yxatlar yoki fayl maydonlari bo'lmasa — tegishli qism
   o'zini o'zi chetlab o'tadi.
   ========================================================================== */

(function () {
  "use strict";

  const form = document.querySelector("form[data-content-form]");
  if (!form) return;

  const MM = window.MM || {};

  // Oxirgi ochilgan bo'lim shu film uchun alohida eslab qolinadi.
  const STEP_KEY = "mm-movie-step:" + window.location.pathname;

  /** Qulaylik uchun qisqartma. */
  function $(selector, root) {
    return (root || form).querySelector(selector);
  }

  function $$(selector, root) {
    return Array.prototype.slice.call((root || form).querySelectorAll(selector));
  }

  /* ====================================================================
     1. Bosqichlar (tablar)
     ==================================================================== */

  const tabs = $$(".mtab");
  const steps = $$(".mform__step");
  const prevBtn = $("[data-step-prev]");
  const nextBtn = $("[data-step-next]");
  const saveBtn = $("[data-step-save]");
  const progress = $("[data-step-progress]");

  /** Bo'lim nomi bo'yicha indeks. */
  function stepIndex(name) {
    for (let i = 0; i < steps.length; i++) {
      if (steps[i].dataset.step === name) return i;
    }
    return 0;
  }

  function activate(name, scroll) {
    // Bosqichsiz forma (fasl, epizod) — almashtiradigan narsa yo'q.
    if (!steps.length) return;

    steps.forEach(function (step) {
      const on = step.dataset.step === name;
      step.hidden = !on;
      step.classList.toggle("is-active", on);
    });

    tabs.forEach(function (tab) {
      const on = tab.dataset.tab === name;
      tab.classList.toggle("is-active", on);
      tab.setAttribute("aria-selected", on ? "true" : "false");
    });

    const index = stepIndex(name);
    if (prevBtn) prevBtn.hidden = index === 0;
    if (nextBtn) nextBtn.hidden = index === steps.length - 1;
    if (saveBtn) saveBtn.hidden = index !== steps.length - 1;
    if (progress) {
      progress.textContent = index + 1 + " / " + steps.length + " bosqich";
    }

    // Oxirgi ochilgan bo'lim eslab qolinadi — saqlashda xato chiqsa
    // yoki sahifa yangilansa admin o'sha joyidan davom etadi.
    try {
      sessionStorage.setItem(STEP_KEY, name);
    } catch (error) {
      /* private rejim — eslab qolmasak ham forma ishlayveradi */
    }

    if (scroll) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      activate(tab.dataset.tab, true);
    });
  });

  if (prevBtn) {
    prevBtn.addEventListener("click", function () {
      const current = stepIndex(form.querySelector(".mform__step.is-active").dataset.step);
      if (current > 0) activate(steps[current - 1].dataset.step, true);
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      const current = stepIndex(form.querySelector(".mform__step.is-active").dataset.step);
      if (current < steps.length - 1) activate(steps[current + 1].dataset.step, true);
    });
  }

  /** Xato bo'lgan bo'limlarning tabiga qizil nuqta qo'yadi. */
  function markInvalidTabs() {
    let firstBroken = null;

    steps.forEach(function (step) {
      const broken = !!step.querySelector(".field__error, .alert--error");
      const tab = tabs.filter(function (t) { return t.dataset.tab === step.dataset.step; })[0];
      if (tab) tab.classList.toggle("is-invalid", broken);
      if (broken && !firstBroken) firstBroken = step.dataset.step;
    });

    return firstBroken;
  }

  /** Xato maydoni yashirin bo'limda bo'lsa — o'sha bo'limni ochib beramiz.
   *  upload-manager.js AJAX bilan qaytgan xatolarni joylashtirganda
   *  shu funksiyani chaqiradi. */
  MM.revealField = function (element) {
    const step = element && element.closest ? element.closest(".mform__step") : null;
    if (step && step.hidden) activate(step.dataset.step, false);
    markInvalidTabs();
  };
  window.MM = MM;

  /* ====================================================================
     2. Fayl maydonlari (dropzone)
     ==================================================================== */

  function humanSize(bytes) {
    if (!bytes) return "";
    const units = ["B", "KB", "MB", "GB"];
    const power = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return (bytes / Math.pow(1024, power)).toFixed(power ? 1 : 0) + " " + units[power];
  }

  $$("[data-drop]").forEach(function (drop) {
    const input = drop.querySelector('input[type="file"]');
    if (!input) return;

    const image = drop.querySelector("[data-drop-img]");
    const meta = drop.querySelector("[data-drop-meta]");
    const sub = drop.querySelector("[data-drop-sub]");
    const clear = drop.querySelector("[data-drop-clear]");
    const opener = drop.querySelector("[data-drop-open]");

    // Tanlov bekor qilinganda qaytariladigan boshlang'ich holat.
    const initial = {
      src: image ? image.getAttribute("src") : "",
      meta: meta ? meta.textContent.trim() : "",
      filled: drop.classList.contains("is-filled"),
    };

    if (opener) {
      opener.addEventListener("click", function () { input.click(); });
    }

    ["dragenter", "dragover"].forEach(function (type) {
      drop.addEventListener(type, function (event) {
        event.preventDefault();
        drop.classList.add("is-over");
      });
    });

    ["dragleave", "drop"].forEach(function (type) {
      drop.addEventListener(type, function (event) {
        event.preventDefault();
        if (type === "dragleave" && drop.contains(event.relatedTarget)) return;
        drop.classList.remove("is-over");
      });
    });

    drop.addEventListener("drop", function (event) {
      const files = event.dataTransfer && event.dataTransfer.files;
      if (!files || !files.length) return;

      // `input.files` ni to'g'ridan-to'g'ri yozib bo'lmaydi — DataTransfer
      // orqali almashtiriladi (barcha zamonaviy brauzerlarda ishlaydi).
      const holder = new DataTransfer();
      holder.items.add(files[0]);
      input.files = holder.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
    });

    input.addEventListener("change", function () {
      const file = input.files && input.files[0];

      if (!file) {
        restore();
        return;
      }

      drop.classList.add("is-filled");
      if (meta) {
        meta.textContent = file.name + " · " + humanSize(file.size);
        meta.title = file.name;
      }
      if (sub) sub.textContent = "Boshqa fayl tanlash uchun bosing";
      if (clear) clear.hidden = false;

      if (image && file.type.indexOf("image/") === 0) {
        if (image.dataset.objectUrl) URL.revokeObjectURL(image.dataset.objectUrl);
        const url = URL.createObjectURL(file);
        image.src = url;
        image.dataset.objectUrl = url;
        image.hidden = false;
      }

      syncPreview();
      syncLegal();
    });

    if (clear) {
      clear.addEventListener("click", function () {
        input.value = "";
        restore();
        syncPreview();
        syncLegal();
      });
    }

    function restore() {
      drop.classList.toggle("is-filled", initial.filled);
      if (meta) meta.textContent = initial.meta || "Fayl tanlanmagan";
      if (sub) sub.textContent = "Bosing yoki faylni tashlang";
      if (clear) clear.hidden = true;

      if (image) {
        if (image.dataset.objectUrl) {
          URL.revokeObjectURL(image.dataset.objectUrl);
          delete image.dataset.objectUrl;
        }
        image.src = initial.src;
        image.hidden = !initial.src;
      }
    }
  });

  /* ====================================================================
     3. Ko'p tanlovli ro'yxatlar (janr / kategoriya / rejissyor)
     ==================================================================== */

  // Ro'yxatlar birinchi bo'lib tayyorlanadi, lekin birinchi hisoblash
  // eng oxirida — `syncPreview()` pastroqda e'lon qilingan o'zgaruvchilarga
  // tayanadi (ular hali tayyor emas).
  const pickerRefreshers = [];

  $$("[data-picker]").forEach(function (picker) {
    const list = picker.querySelector("[data-picker-list]");
    const search = picker.querySelector("[data-picker-search]");
    const count = picker.querySelector("[data-picker-count]");
    const none = picker.querySelector("[data-picker-none]");
    const reset = picker.querySelector("[data-picker-clear]");
    if (!list) return;

    const labels = Array.prototype.slice.call(list.querySelectorAll("label"));

    function refresh() {
      let selected = 0;

      labels.forEach(function (label) {
        const box = label.querySelector('input[type="checkbox"]');
        const on = !!(box && box.checked);
        label.classList.toggle("is-on", on);
        if (on) selected++;
      });

      if (count) {
        count.textContent = selected ? selected + " tanlandi" : "tanlanmagan";
        count.classList.toggle("is-on", selected > 0);
      }
      if (reset) reset.hidden = selected === 0;

      syncPreview();
    }

    function filter() {
      const needle = (search.value || "").trim().toLowerCase();
      let shown = 0;

      labels.forEach(function (label) {
        const box = label.querySelector('input[type="checkbox"]');
        const hit = !needle || label.textContent.toLowerCase().indexOf(needle) !== -1;
        // Tanlangan element qidiruvda ham ko'rinib tursin — aks holda
        // nimalar belgilangani ko'zdan qochadi.
        const visible = hit || (box && box.checked);
        label.parentElement.hidden = !visible;
        if (visible) shown++;
      });

      if (none) none.hidden = shown !== 0;
    }

    list.addEventListener("change", refresh);
    if (search) search.addEventListener("input", filter);

    if (reset) {
      reset.addEventListener("click", function () {
        labels.forEach(function (label) {
          const box = label.querySelector('input[type="checkbox"]');
          if (box) box.checked = false;
        });
        refresh();
      });
    }

    pickerRefreshers.push(refresh);
  });

  /* ====================================================================
     4. Belgilar hisoblagichi
     ==================================================================== */

  $$("[data-counter-for]").forEach(function (badge) {
    const input = document.getElementById(badge.dataset.counterFor);
    if (!input) return;

    const limit = parseInt(input.getAttribute("maxlength"), 10);

    function tick() {
      const used = input.value.length;
      badge.textContent = limit ? used + " / " + limit : used + " belgi";
      badge.classList.toggle("is-warn", !!limit && used > limit - 20);
    }

    input.addEventListener("input", tick);
    tick();
  });

  /* ====================================================================
     5. Jonli karta ko'rinishi
     ==================================================================== */

  const titleInput = $("#id_title");
  const yearInput = $("#id_release_year");
  const qualitySelect = $("#id_quality");

  const previewTitle = $("[data-preview-title]");
  const previewYear = $("[data-preview-year]");
  const previewGenres = $("[data-preview-genres]");
  const previewQuality = $("[data-preview-quality]");
  const previewPoster = $("[data-preview-poster]");
  const previewBlank = $("[data-preview-blank]");

  function syncPreview() {
    if (previewTitle && titleInput) {
      previewTitle.textContent = titleInput.value.trim() || "Film nomi";
    }
    if (previewYear && yearInput) {
      previewYear.textContent = yearInput.value.trim() || "—";
    }
    if (previewQuality) {
      const option = qualitySelect ? qualitySelect.options[qualitySelect.selectedIndex] : null;
      previewQuality.textContent = option ? option.text : "";
      previewQuality.hidden = !option;
    }

    if (previewGenres) {
      const picked = $$("#id_genres input:checked").map(function (box) {
        const label = box.closest("label");
        return label ? label.textContent.trim() : "";
      });

      if (!picked.length) {
        previewGenres.textContent = "janr tanlanmagan";
      } else if (picked.length <= 2) {
        previewGenres.textContent = picked.join(", ");
      } else {
        previewGenres.textContent = picked.slice(0, 2).join(", ") + " +" + (picked.length - 2);
      }
    }

    // Poster maydonidagi rasm — dropzone o'zi ko'rsatib bo'lgan bo'ladi,
    // shu yerda faqat karta ichidagi nusxa yangilanadi.
    if (previewPoster) {
      const source = form.querySelector(".drop--poster [data-drop-img]");
      const src = source && !source.hidden ? source.src : "";
      previewPoster.src = src;
      previewPoster.hidden = !src;
      if (previewBlank) previewBlank.hidden = !!src;
    }
  }

  [titleInput, yearInput].forEach(function (input) {
    if (input) input.addEventListener("input", syncPreview);
  });
  if (qualitySelect) qualitySelect.addEventListener("change", syncPreview);

  /* ====================================================================
     6. Slug — sarlavhadan avtomatik taxmin
     ==================================================================== */

  const slugInput = $("#id_slug");

  if (slugInput && titleInput && !slugInput.value) {
    // Admin slugni qo'lda tegmagan bo'lsa, sarlavhadan taxmin ko'rsatiladi.
    // Bu faqat ko'rinish uchun (placeholder) — haqiqiy slugni server
    // `unique_slugify()` orqali beradi.
    titleInput.addEventListener("input", function () {
      if (slugInput.dataset.touched) return;
      slugInput.placeholder = slugify(titleInput.value) || "avtomatik";
    });
    slugInput.addEventListener("input", function () {
      slugInput.dataset.touched = "1";
    });
  }

  function slugify(text) {
    return String(text)
      .toLowerCase()
      .replace(/['’`]/g, "")
      .replace(/[^a-z0-9а-яё]+/gi, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 60);
  }

  /* ====================================================================
     7. Litsenziya natijasi — `can_watch` / `can_download` ning ko'zgusi
     ==================================================================== */

  const licenseSelect = $("#id_license_type");
  const downloadToggle = $("#id_is_download_allowed");
  const downloadUrl = $("#id_download_url");
  const videoUrl = $("#id_video_url");
  const legalWatch = $("[data-legal-watch]");
  const legalDownload = $("[data-legal-download]");
  const legalNote = $("[data-legal-note]");

  const OPEN_LICENSES = ["public_domain", "licensed"];

  /** Filmda umuman video manbasi bormi? */
  function hasVideoSource() {
    if (videoUrl && videoUrl.value.trim()) return true;

    const fileDrop = form.querySelector(".drop--video");
    if (fileDrop && fileDrop.classList.contains("is-filled")) return true;

    // Qo'shimcha sifat qatorlari ham manba hisoblanadi — yangi tanlangan
    // fayl, kiritilgan havola yoki bazada allaqachon saqlangan fayl.
    return $$('[data-formset-rows="videos"] [data-formset-row]').some(function (row) {
      const gone = row.querySelector('input[name$="-DELETE"]');
      if (gone && gone.checked) return false;
      if (row.hasAttribute("data-has-file")) return true;

      const url = row.querySelector('input[type="url"]');
      const file = row.querySelector('input[type="file"]');
      return !!((url && url.value.trim()) || (file && file.files && file.files.length));
    });
  }

  function paint(chip, on, text) {
    if (!chip) return;
    chip.classList.toggle("is-on", on);
    chip.classList.toggle("is-off", !on);
    const value = chip.querySelector("i");
    if (value) value.textContent = text;
  }

  function syncLegal() {
    if (!legalWatch) return;

    // Epizod formasida litsenziya maydoni yo'q — huquqiy holat serialdan
    // meros bo'lgani uchun bu yerda faqat video va yuklash tekshiriladi.
    const legal = licenseSelect ? OPEN_LICENSES.indexOf(licenseSelect.value) !== -1 : true;
    const video = hasVideoSource();
    const allowed = !!(downloadToggle && downloadToggle.checked);
    const link = !!(downloadUrl && downloadUrl.value.trim());

    paint(legalWatch, legal && video, legal && video ? "ochiq" : "yopiq");
    paint(
      legalDownload,
      legal && allowed && link,
      legal && allowed && link ? "ochiq" : "yopiq"
    );

    let note = "";
    if (!legal) {
      note = "«Faqat treyler» — saytda pleer ham, yuklab olish ham chiqmaydi.";
    } else if (!video) {
      note = "Video manbasi kiritilmagan — pleer ochilmaydi.";
    } else if (allowed && !link) {
      note = "Ruxsat yoqilgan, lekin yuklab olish havolasi bo'sh.";
    } else if (video && !allowed) {
      note = "Film ko'rish uchun ochiq; yuklab olish o'chirilgan.";
    } else {
      note = "Hammasi joyida — film ko'rish va yuklab olish uchun ochiq.";
    }
    if (legalNote) legalNote.textContent = note;

    // Huquqiy qoidaga zid tanlovni darhol ko'rsatamiz (server ham
    // tekshiradi — bu faqat ogohlantirish).
    const conflict = !legal && allowed;
    if (downloadToggle) {
      const row = downloadToggle.closest(".toggle-row");
      if (row) row.classList.toggle("is-blocked", conflict);
    }
  }

  [licenseSelect, downloadToggle].forEach(function (element) {
    if (element) element.addEventListener("change", syncLegal);
  });
  [downloadUrl, videoUrl].forEach(function (element) {
    if (element) element.addEventListener("input", syncLegal);
  });
  form.addEventListener("change", function (event) {
    if (event.target.closest('[data-formset-rows="videos"]')) syncLegal();
  });

  /* ====================================================================
     8. Formset qatorlari — raqamlash va hisob
     (qo'shish/olib tashlashning o'zi dashboard.js da)
     ==================================================================== */

  const LABELS = { videos: "sifat", cast_members: "aktyor" };

  /** Qator bazada bormi yoki admin biror narsa kiritganmi? */
  function isFilled(row) {
    const id = row.querySelector('input[name$="-id"]');
    if (id && id.value) return true;
    if (row.hasAttribute("data-has-file")) return true;

    return $$("input, select, textarea", row).some(function (field) {
      if (field.type === "hidden" || field.name.indexOf("-DELETE") !== -1) return false;
      if (field.type === "file") return !!(field.files && field.files.length);
      if (field.tagName === "SELECT") return !!field.value;
      // Raqamli "tartib" maydoni 0 bilan keladi — u to'ldirilgan hisoblanmaydi.
      return field.type === "number" ? Number(field.value) > 0 : !!field.value.trim();
    });
  }

  function renumber() {
    $$("[data-formset-rows]").forEach(function (holder) {
      const prefix = holder.dataset.formsetRows;
      const rows = $$("[data-formset-row]", holder);
      let live = 0;

      rows.forEach(function (row, index) {
        const num = row.querySelector(".fset__num");
        if (num) num.textContent = index + 1;

        const gone = row.querySelector('input[name$="-DELETE"]');
        row.classList.toggle("is-gone", !!(gone && gone.checked));

        // Hisobga faqat haqiqiy qatorlar kiradi: bazadagi yozuv yoki
        // to'ldirilgan yangi qator. Bo'sh "zaxira" qator sanalmaydi.
        if (gone && gone.checked) return;
        if (isFilled(row)) live++;
      });

      const pill = form.querySelector('[data-fset-count="' + prefix + '"]');
      if (pill) {
        pill.textContent = live
          ? live + " ta " + (LABELS[prefix] || "qator")
          : "hali qo'shilmagan";
      }
    });
  }

  // dashboard.js qator qo'shgandan/olib tashlagandan keyin ishlaydi —
  // ikkala listener ham `document` da, u avval ro'yxatdan o'tgan.
  document.addEventListener("click", function (event) {
    if (event.target.closest("[data-formset-add], [data-formset-remove]")) {
      renumber();
      syncLegal();
    }
  });

  form.addEventListener("change", function (event) {
    if (event.target.name && event.target.name.indexOf("-DELETE") !== -1) renumber();
    if (event.target.closest("[data-formset-row]")) renumber();
  });

  form.addEventListener("input", function (event) {
    if (event.target.closest("[data-formset-row]")) renumber();
  });

  /* ====================================================================
     9. Saqlanmagan o'zgarishlar haqida ogohlantirish
     ==================================================================== */

  let dirty = false;
  let saving = false;

  form.addEventListener("input", function () { dirty = true; });
  form.addEventListener("change", function () { dirty = true; });
  form.addEventListener("submit", function () { saving = true; });

  window.addEventListener("beforeunload", function (event) {
    if (!dirty || saving) return;
    event.preventDefault();
    event.returnValue = "";
  });

  /* ====================================================================
     Ishga tushirish
     ==================================================================== */

  const broken = markInvalidTabs();
  let start = broken;

  if (!start) {
    try {
      const remembered = sessionStorage.getItem(STEP_KEY);
      if (remembered && steps.some(function (s) { return s.dataset.step === remembered; })) {
        start = remembered;
      }
    } catch (error) {
      /* e'tiborsiz */
    }
  }

  if (steps.length) activate(start || steps[0].dataset.step, false);
  pickerRefreshers.forEach(function (refresh) { refresh(); });
  renumber();
  syncPreview();
  syncLegal();
})();
