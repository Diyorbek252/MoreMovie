/* ==========================================================================
   MORE-MOVIE — Katta video fayllarni fonda yuklash

   Muammo: 5GB lik videoni odatdagi forma bilan yuborganda brauzer butun
   faylni jo'natib bo'lguncha sahifa qotib turadi va admin hech qanday
   ma'lumot ko'rmaydi.

   Yechim ikki bosqichli:

   1) Film qo'shish/tahrirlash formasi yuborilganda video fayl POST'ga
      QO'SHILMAYDI — shuning uchun saqlash bir zumda o'tadi. Fayl
      brauzerning IndexedDB'siga olinadi (sahifa almashganda ham
      yo'qolmaydi) va dashboardga redirect qilinadi.

   2) Dashboardning istalgan sahifasida shu fayl(lar) fonda, progress
      paneli bilan yuklanadi (`dashboard:api_upload_movie_video`).

   ESLATMA: yuklash brauzer tabida ketadi — dashboarddan butunlay chiqib
   ketilsa uziladi, lekin fayl IndexedDB'da qolgani uchun keyingi safar
   dashboard ochilganda avtomatik davom etadi.
   ========================================================================== */

(function () {
  "use strict";

  const MM = window.MM;
  if (!MM || !window.indexedDB) return;

  const DB_NAME = "mm-uploads";
  const STORE = "pending";

  /* ---------------------------------------------------------------- IndexedDB */

  function openDB() {
    return new Promise(function (resolve, reject) {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = function () {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE)) {
          db.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
        }
      };
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error); };
    });
  }

  function tx(db, mode) {
    return db.transaction(STORE, mode);
  }

  /** Katta blob (video) yozilganda `request.onsuccess` yozuv hali diskka
   *  to'liq committed bo'lmasa ham otishi mumkin. Shu darrov keyin sahifa
   *  almashtirilsa (redirect), yozuv yarim yo'lda uzilib, hech narsa
   *  saqlanmagan bo'lib chiqadi. Shuning uchun har doim TRANZAKSIYANING
   *  o'zi tugashini (`oncomplete`) kutamiz — faqat shundagina yozuv
   *  ishonchli tarzda diskka yozilgani kafolatlanadi. */
  function addRecord(record) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        const transaction = tx(db, "readwrite");
        const request = transaction.objectStore(STORE).add(record);
        let insertedId;
        request.onsuccess = function () { insertedId = request.result; };
        request.onerror = function () { reject(request.error); };
        transaction.oncomplete = function () { resolve(insertedId); };
        transaction.onerror = function () { reject(transaction.error); };
      });
    });
  }

  function allRecords() {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        const request = tx(db, "readonly").objectStore(STORE).getAll();
        request.onsuccess = function () { resolve(request.result || []); };
        request.onerror = function () { reject(request.error); };
      });
    });
  }

  function deleteRecord(id) {
    return openDB().then(function (db) {
      return new Promise(function (resolve) {
        const transaction = tx(db, "readwrite");
        transaction.objectStore(STORE).delete(id);
        transaction.oncomplete = transaction.onerror = function () { resolve(); };
      });
    });
  }

  /* ------------------------------------------------------------- Yordamchilar */

  function formatSize(bytes) {
    if (!bytes) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const power = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return (bytes / Math.pow(1024, power)).toFixed(power ? 1 : 0) + " " + units[power];
  }

  function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) return "—";
    if (seconds < 60) return Math.round(seconds) + " soniya";
    if (seconds < 3600) return Math.round(seconds / 60) + " daqiqa";
    const hours = Math.floor(seconds / 3600);
    return hours + " soat " + Math.round((seconds % 3600) / 60) + " daqiqa";
  }

  /* =============================================================== 1-BOSQICH
     Film formasi — videoni POST'dan ajratib olish
     ======================================================================= */

  const form = document.getElementById("movie-form");

  if (form) {
    /** Formadagi tanlangan video fayllarni topadi.
     *  Har biri: {name, quality, file, rowPrefix} — `rowPrefix` faqat
     *  qo'shimcha sifat qatorlari (videos-N-...) uchun to'ldiriladi. */
    function collectVideoFiles() {
      const found = [];

      const main = form.querySelector('input[type="file"][name="video_file"]');
      if (main && main.files && main.files[0]) {
        found.push({ name: "video_file", quality: "", file: main.files[0], rowPrefix: null });
      }

      form.querySelectorAll('input[type="file"][name^="videos-"][name$="-video_file"]')
        .forEach(function (input) {
          if (!input.files || !input.files[0]) return;
          const prefix = input.name.replace(/-video_file$/, "");
          const select = form.querySelector('[name="' + prefix + '-quality"]');
          found.push({
            name: input.name,
            quality: select ? select.value : "",
            file: input.files[0],
            rowPrefix: prefix,
          });
        });

      return found;
    }

    /** Xatolarni maydonlar yoniga chiqaradi (sahifa qayta yuklanmaydi —
     *  shu sababli tanlangan fayl ham yo'qolmaydi). */
    function renderErrors(errors) {
      form.querySelectorAll(".field__error--js").forEach(function (el) { el.remove(); });

      let first = null;

      Object.keys(errors || {}).forEach(function (key) {
        const message = errors[key][0];

        if (key === "__all__") {
          MM.toast(message, "error");
          return;
        }

        const field = form.querySelector('[name="' + key + '"]');
        if (!field) {
          MM.toast(message, "error");
          return;
        }

        const note = document.createElement("p");
        note.className = "field__error field__error--js";
        note.textContent = message;
        (field.closest(".field") || field.parentNode).appendChild(note);

        if (!first) first = field;
      });

      if (first) {
        // Bosqichli formada maydon yashirin bo'limda bo'lishi mumkin —
        // content-form.js o'sha bo'limni ochib beradi (xatoli tab ham
        // belgilanadi). Boshqa sahifalarda bu funksiya umuman bo'lmaydi.
        if (typeof MM.revealField === "function") MM.revealField(first);

        first.scrollIntoView({ behavior: "smooth", block: "center" });
        if (first.focus) first.focus({ preventScroll: true });
      }
    }

    form.addEventListener("submit", async function (event) {
      const videos = collectVideoFiles();
      if (!videos.length) return; // Video yo'q — odatdagidek yuboriladi.

      event.preventDefault();

      const submitButtons = form.querySelectorAll('button[type="submit"]');
      submitButtons.forEach(function (b) { b.disabled = true; });

      const payload = new FormData(form);

      videos.forEach(function (item) {
        // Katta faylning o'zi POST'ga tushmaydi.
        payload.delete(item.name);

        // Yangi qo'shimcha-sifat qatorini shu POST'da saqlamaymiz — qator
        // fayl yuklab bo'lingach, endpoint tomonidan yaratiladi.
        //
        // Qatorni shunchaki bo'shatib bo'lmaydi: `quality` ning model
        // darajasidagi default qiymati (FHD) bor, shuning uchun bo'sh
        // qiymat "o'zgartirilgan" deb hisoblanadi va Django uni majburiy
        // maydon sifatida tekshirib "This field is required" beradi.
        // DELETE bilan belgilangan qatorni esa formset butunlay chetlab
        // o'tadi — hech qanday tekshiruv ham, yozuv ham bo'lmaydi.
        // Qator allaqachon bazada bo'lsa (id bor) — tegmaymiz, faqat
        // fayli yangilanadi.
        if (item.rowPrefix && !payload.get(item.rowPrefix + "-id")) {
          payload.set(item.rowPrefix + "-DELETE", "on");
        }
      });

      try {
        const response = await fetch(form.action || window.location.href, {
          method: "POST",
          body: payload,
          headers: { "X-Requested-With": "XMLHttpRequest" },
          credentials: "same-origin",
        });

        const data = await response.json();

        if (!data.ok) {
          renderErrors(data.errors);
          submitButtons.forEach(function (b) { b.disabled = false; });
          MM.toast("Formada xatolar bor — tekshirib qayta yuboring.", "error");
          return;
        }

        // Film saqlandi. Endi fayllarni brauzer xotirasiga olib,
        // dashboardga o'tamiz — yuklash o'sha yerda davom etadi.
        for (const item of videos) {
          await addRecord({
            movieId: data.movie_id,
            movieTitle: data.movie_title,
            quality: item.quality,
            fileName: item.file.name,
            fileSize: item.file.size,
            file: item.file,
            createdAt: Date.now(),
          });
        }

        window.location.href = data.redirect;
      } catch (error) {
        submitButtons.forEach(function (b) { b.disabled = false; });
        MM.toast("Saqlashda xatolik: " + error.message, "error");
      }
    });
  }

  /* =============================================================== 2-BOSQICH
     Dashboard — fonda yuklash va progress paneli
     ======================================================================= */

  const endpointTemplate = document.body.dataset.urlUploadVideo;
  if (!endpointTemplate) return;

  let panel = null;
  let activeCount = 0;

  function buildPanel() {
    panel = document.createElement("section");
    panel.className = "upload-panel";
    panel.innerHTML =
      '<div class="upload-panel__head">' +
      '  <strong class="upload-panel__title">Video yuklanmoqda</strong>' +
      '  <button type="button" class="upload-panel__toggle" aria-label="Yig\'ish">–</button>' +
      "</div>" +
      '<div class="upload-panel__body"></div>';

    panel.querySelector(".upload-panel__toggle").addEventListener("click", function () {
      panel.classList.toggle("is-collapsed");
      this.textContent = panel.classList.contains("is-collapsed") ? "+" : "–";
    });

    document.body.appendChild(panel);
    return panel;
  }

  function addItem(record) {
    if (!panel) buildPanel();

    const item = document.createElement("article");
    item.className = "upload-item";
    item.innerHTML =
      '<div class="upload-item__head">' +
      '  <span class="upload-item__name"></span>' +
      '  <span class="upload-item__percent">0%</span>' +
      "</div>" +
      '<div class="upload-item__bar"><span></span></div>' +
      '<div class="upload-item__meta"></div>';

    const quality = record.quality ? " · " + record.quality : "";
    item.querySelector(".upload-item__name").textContent = record.movieTitle + quality;

    panel.querySelector(".upload-panel__body").appendChild(item);
    return item;
  }

  const DISMISS_DELAY = 2600; // "Yuklandi" deb necha ms turib qolsin
  const FADE_DURATION = 400; // components.css dagi transition bilan bir xil

  /** Muvaffaqiyatli yuklangan elementni bir ozdan keyin asta xiralashtirib
   *  panelidan olib tashlaydi. Panel butunlay bo'shab qolsa, o'zi ham
   *  yo'qoladi. */
  function scheduleDismiss(item) {
    setTimeout(function () {
      item.classList.add("is-fading");

      setTimeout(function () {
        item.remove();

        if (panel && !panel.querySelector(".upload-item")) {
          panel.remove();
          panel = null;
        }
      }, FADE_DURATION);
    }, DISMISS_DELAY);
  }

  function uploadRecord(record) {
    return new Promise(function (resolve) {
      const item = addItem(record);
      const bar = item.querySelector(".upload-item__bar span");
      const percentEl = item.querySelector(".upload-item__percent");
      const metaEl = item.querySelector(".upload-item__meta");

      const payload = new FormData();
      payload.append("video", record.file, record.fileName);
      if (record.quality) payload.append("quality", record.quality);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", endpointTemplate.replace("/0/", "/" + record.movieId + "/"));
      xhr.setRequestHeader("X-CSRFToken", MM.getCsrfToken());

      const startedAt = Date.now();

      xhr.upload.addEventListener("progress", function (event) {
        if (!event.lengthComputable) return;

        const percent = Math.round((event.loaded / event.total) * 100);
        bar.style.width = percent + "%";
        percentEl.textContent = percent + "%";

        const elapsed = (Date.now() - startedAt) / 1000;
        const speed = event.loaded / Math.max(elapsed, 0.1);
        const remaining = (event.total - event.loaded) / Math.max(speed, 1);

        metaEl.textContent =
          formatSize(event.loaded) + " / " + formatSize(event.total) +
          " · " + formatSize(speed) + "/s · " + formatTime(remaining) + " qoldi";
      });

      xhr.addEventListener("load", async function () {
        activeCount--;

        if (xhr.status >= 200 && xhr.status < 300) {
          item.classList.add("is-done");
          bar.style.width = "100%";
          percentEl.textContent = "✓";
          metaEl.textContent = "Yuklandi — " + formatSize(record.fileSize);
          await deleteRecord(record.id);

          try {
            const data = JSON.parse(xhr.responseText);
            if (data.message) MM.toast(data.message, "success");
          } catch (e) { /* javob JSON bo'lmasa ham yuklash muvaffaqiyatli */ }

          // Muvaffaqiyatli yozuv bir necha soniya "Yuklandi" deb turadi,
          // keyin asta xiralashib, panelidan olib tashlanadi. Xato bergan
          // yozuvlar esa e'tiborsiz qolmasligi uchun turgan holicha qoladi.
          scheduleDismiss(item);
        } else {
          item.classList.add("is-failed");
          percentEl.textContent = "!";
          metaEl.textContent =
            "Yuklanmadi (" + xhr.status + ") — dashboard qayta ochilganda urinib ko'riladi.";
          MM.toast("«" + record.movieTitle + "» videosi yuklanmadi.", "error");
        }

        resolve();
      });

      xhr.addEventListener("error", function () {
        activeCount--;
        item.classList.add("is-failed");
        metaEl.textContent = "Tarmoq uzildi — dashboard qayta ochilganda davom etadi.";
        resolve();
      });

      activeCount++;
      xhr.send(payload);
    });
  }

  window.addEventListener("beforeunload", function (event) {
    if (activeCount > 0) {
      event.preventDefault();
      event.returnValue = "";
    }
  });

  // Navbatdagi fayllarni birin-ketin yuklaymiz — parallel yuborilsa
  // kanal bo'linib, hammasi sekinlashadi.
  allRecords().then(async function (records) {
    for (const record of records) {
      await uploadRecord(record);
    }
  });
})();
