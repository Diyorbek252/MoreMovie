/* ==========================================================================
   MORE-MOVIE — Navbar bildirishnoma qo'ng'irog'i
   Faqat tizimga kirgan foydalanuvchilar uchun yuklanadi (base.html'ga qarang).
   ========================================================================== */

(function () {
  "use strict";

  const MM = window.MM;
  if (!MM) return;

  const menu = document.getElementById("notif-menu");
  const toggle = document.getElementById("notif-toggle");
  const panel = document.getElementById("notif-panel");
  const list = document.getElementById("notif-list");
  const badge = document.getElementById("notif-badge");
  const markAllBtn = document.getElementById("notif-mark-all");

  if (!menu || !toggle || !panel || !list) return;

  const listUrl = document.body.dataset.urlNotifications;
  const readAllUrl = document.body.dataset.urlNotificationsReadAll;

  let loaded = false;

  /** Server javobidagi o'qilmagan sonini navbar belgisida ko'rsatadi. */
  function updateBadge(count) {
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 99 ? "99+" : String(count);
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  }

  /**
   * Matnni HTML ga xavfsiz joylash uchun escape qiladi — server javobi
   * (bildirishnoma sarlavhasi/matni) to'g'ridan-to'g'ri innerHTML'ga
   * qo'yilmaydi.
   */
  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.innerHTML;
  }

  function renderList(items) {
    if (!items.length) {
      list.innerHTML = '<p class="notif-empty">Hozircha bildirishnoma yo\'q.</p>';
      return;
    }

    list.innerHTML = items
      .map(function (item) {
        const unreadClass = item.is_read ? "" : " notif-item--unread";
        return (
          '<button type="button" class="notif-item' + unreadClass + '"' +
          ' data-id="' + item.id + '" data-read="' + (item.is_read ? "1" : "0") + '"' +
          (item.link ? ' data-link="' + escapeHtml(item.link) + '"' : "") +
          ">" +
          '<div class="notif-item__body">' +
          '<div class="notif-item__title">' + escapeHtml(item.title) + "</div>" +
          '<div class="notif-item__message">' + escapeHtml(item.message) + "</div>" +
          '<div class="notif-item__time">' + escapeHtml(item.created_at) + "</div>" +
          "</div>" +
          "</button>"
        );
      })
      .join("");
  }

  async function fetchNotifications() {
    if (!listUrl) return;
    try {
      const response = await fetch(listUrl, { credentials: "same-origin" });
      if (!response.ok) throw new Error("bad status");
      const data = await response.json();
      renderList(data.results || []);
      updateBadge(data.unread_count || 0);
    } catch (error) {
      list.innerHTML = '<p class="notif-empty">Yuklab bo\'lmadi. Qayta urinib ko\'ring.</p>';
    }
  }

  function open() {
    menu.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
    if (!loaded) {
      loaded = true;
      fetchNotifications();
    }
  }

  function close() {
    menu.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
  }

  toggle.addEventListener("click", function (event) {
    event.stopPropagation();
    if (menu.classList.contains("is-open")) {
      close();
    } else {
      open();
    }
  });

  document.addEventListener("click", function (event) {
    if (!menu.contains(event.target)) close();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") close();
  });

  // Bitta bildirishnomaga bosilganda: o'qilgan deb belgilaymiz, havolasi
  // bo'lsa o'sha sahifaga o'tamiz.
  list.addEventListener("click", async function (event) {
    const item = event.target.closest(".notif-item");
    if (!item) return;

    const id = item.dataset.id;
    const link = item.dataset.link;
    const alreadyRead = item.dataset.read === "1";

    if (!alreadyRead && listUrl) {
      try {
        const data = await MM.postJSON(listUrl + id + "/read/", {});
        item.classList.remove("notif-item--unread");
        item.dataset.read = "1";
        updateBadge(data.unread_count || 0);
      } catch (error) {
        // Jim o'tkazamiz — o'qishga urinish muvaffaqiyatsiz bo'lsa ham
        // foydalanuvchi havolaga o'tishi kerak.
      }
    }

    if (link) {
      window.location.href = link;
    }
  });

  if (markAllBtn) {
    markAllBtn.addEventListener("click", async function () {
      if (!readAllUrl) return;
      try {
        await MM.postJSON(readAllUrl, {});
        list.querySelectorAll(".notif-item--unread").forEach(function (item) {
          item.classList.remove("notif-item--unread");
          item.dataset.read = "1";
        });
        updateBadge(0);
        MM.toast("Barcha bildirishnomalar o'qilgan deb belgilandi", "success");
      } catch (error) {
        MM.toast(error.message, "error");
      }
    });
  }
})();
