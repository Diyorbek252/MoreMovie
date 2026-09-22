/* ==========================================================================
   MORE-MOVIE — Umumiy interfeys skripti
   Loader, navbar, mobil menyu, karusellar, toast, modal, reveal animatsiyasi
   ========================================================================== */

(function () {
  "use strict";

  /* --------------------------------------------------------------------
     Umumiy yordamchilar — boshqa skriptlar ham ishlatadi (window.MM)
     -------------------------------------------------------------------- */

  /** Cookie qiymatini o'qiydi (CSRF tokeni uchun). */
  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
    return match ? decodeURIComponent(match[2]) : null;
  }

  /**
   * CSRF tokenini topadi.
   * Avval cookie'dan, topilmasa sahifadagi yashirin input'dan oladi.
   */
  function getCsrfToken() {
    const fromCookie = getCookie("csrftoken");
    if (fromCookie) return fromCookie;
    const input = document.querySelector("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  /**
   * CSRF himoyasi bilan JSON POST so'rovi.
   * @returns {Promise<Object>} javob tanasi
   */
  async function postJSON(url, data) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify(data || {}),
    });

    let payload = {};
    try {
      payload = await response.json();
    } catch (error) {
      payload = {};
    }

    if (!response.ok) {
      const message = payload.error || "So'rov bajarilmadi. Qayta urinib ko'ring.";
      throw new Error(message);
    }
    return payload;
  }

  /** Ekranning o'ng pastida qisqa bildirishnoma ko'rsatadi. */
  function toast(message, type) {
    const holder = document.getElementById("toasts");
    if (!holder || !message) return;

    const el = document.createElement("div");
    el.className = "toast toast--" + (type || "info");
    el.textContent = message;
    holder.appendChild(el);

    // 3.5 soniyadan keyin chiqish animatsiyasi bilan olib tashlanadi.
    setTimeout(function () {
      el.classList.add("is-leaving");
      el.addEventListener("animationend", function () {
        el.remove();
      });
    }, 3500);
  }

  // Boshqa modullar uchun ochiq API.
  window.MM = { getCookie: getCookie, getCsrfToken: getCsrfToken, postJSON: postJSON, toast: toast };

  /* --------------------------------------------------------------------
     Yuklanish ekrani
     -------------------------------------------------------------------- */

  const loader = document.getElementById("loader");
  if (loader) {
    // Sahifa to'liq yuklangach yashiramiz, lekin logo hech bo'lmasa
    // qisqa vaqt ko'rinsin (brend taassuroti uchun).
    const hide = function () {
      loader.classList.add("is-done");
    };
    if (document.readyState === "complete") {
      setTimeout(hide, 300);
    } else {
      window.addEventListener("load", function () {
        setTimeout(hide, 300);
      });
    }
    // Zaxira: nimadir yuklanmay qolsa ham 4 soniyadan keyin ochiladi.
    setTimeout(hide, 4000);
  }

  /* --------------------------------------------------------------------
     Navbar — aylantirishda fon zichlashadi
     -------------------------------------------------------------------- */

  const navbar = document.getElementById("navbar");
  if (navbar) {
    let ticking = false;
    const updateNav = function () {
      navbar.classList.toggle("is-scrolled", window.scrollY > 40);
      ticking = false;
    };
    window.addEventListener(
      "scroll",
      function () {
        if (!ticking) {
          // requestAnimationFrame — scroll paytida ortiqcha ish qilmaslik uchun.
          window.requestAnimationFrame(updateNav);
          ticking = true;
        }
      },
      { passive: true }
    );
    updateNav();
  }

  /* --------------------------------------------------------------------
     Mobil chekma menyu
     -------------------------------------------------------------------- */

  const burger = document.getElementById("burger");
  const drawer = document.getElementById("drawer");

  if (burger && drawer) {
    burger.addEventListener("click", function () {
      const isOpen = drawer.classList.toggle("is-open");
      burger.classList.toggle("is-open", isOpen);
      burger.setAttribute("aria-expanded", String(isOpen));
      document.body.classList.toggle("is-locked", isOpen);
    });

    // Havola bosilganda menyu yopiladi.
    drawer.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        drawer.classList.remove("is-open");
        burger.classList.remove("is-open");
        burger.setAttribute("aria-expanded", "false");
        document.body.classList.remove("is-locked");
      }
    });
  }

  /* --------------------------------------------------------------------
     Foydalanuvchi menyusi
     -------------------------------------------------------------------- */

  const userMenu = document.getElementById("user-menu");
  const userToggle = document.getElementById("user-menu-toggle");

  if (userMenu && userToggle) {
    userToggle.addEventListener("click", function (event) {
      event.stopPropagation();
      const isOpen = userMenu.classList.toggle("is-open");
      userToggle.setAttribute("aria-expanded", String(isOpen));
    });

    // Tashqariga bosilganda yopiladi.
    document.addEventListener("click", function (event) {
      if (!userMenu.contains(event.target)) {
        userMenu.classList.remove("is-open");
        userToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Escape barcha ochiq panellarni yopadi.
  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;

    if (userMenu) userMenu.classList.remove("is-open");
    if (drawer && drawer.classList.contains("is-open")) {
      drawer.classList.remove("is-open");
      if (burger) burger.classList.remove("is-open");
      document.body.classList.remove("is-locked");
    }
    document.querySelectorAll(".modal.is-open").forEach(function (modal) {
      modal.classList.remove("is-open");
      document.body.classList.remove("is-locked");
    });
  });

  /* --------------------------------------------------------------------
     Gorizontal karusellar
     -------------------------------------------------------------------- */

  document.querySelectorAll(".rail-wrap").forEach(function (wrap) {
    const rail = wrap.querySelector(".rail");
    if (!rail) return;

    const prev = wrap.querySelector('[data-rail="prev"]');
    const next = wrap.querySelector('[data-rail="next"]');

    /** Strelkalarni chekka holatlarda yashiradi. */
    const syncButtons = function () {
      const maxScroll = rail.scrollWidth - rail.clientWidth;
      if (prev) prev.disabled = rail.scrollLeft <= 4;
      if (next) next.disabled = rail.scrollLeft >= maxScroll - 4;
    };

    const scrollBy = function (direction) {
      // Bir marta bosilganda ko'rinadigan enning ~85% i siljiydi.
      rail.scrollBy({ left: direction * rail.clientWidth * 0.85, behavior: "smooth" });
    };

    if (prev) prev.addEventListener("click", function () { scrollBy(-1); });
    if (next) next.addEventListener("click", function () { scrollBy(1); });

    rail.addEventListener("scroll", syncButtons, { passive: true });
    window.addEventListener("resize", syncButtons);
    syncButtons();
  });

  /* --------------------------------------------------------------------
     Premyeralar — markazlashgan cheksiz («loop») karusel

     Kartalar ustma-ust turadi (uslublar: pages.css, `.premiere-stage`),
     bu skript esa har biriga `data-pos` atributini qo'yadi:

          -2      -1       0      +1      +2
        sahna    chap   MARKAZ   o'ng    sahna
       tashqari                        tashqari

     Yorqin karta DOIM markazda; belgilangan oraliqda navbat keyingi
     kartaga o'tadi va oxirgisidan keyin yana birinchisi keladi —
     ya'ni aylanishning boshi ham, oxiri ham yo'q.

     `data-pos` FAQAT shu yerdan qo'yiladi: agar JS ishlamasa atribut
     umuman bo'lmaydi va CSS kartalarni oddiy ustun qilib ko'rsatadi
     (zaxira ko'rinish, pages.css dagi `:not([data-pos])` qoidasi).
     -------------------------------------------------------------------- */

  // Bitta karta necha vaqt markazda turadi.
  const SPOTLIGHT_MS = 4000;

  // Bo'lim ekranga kirgach shuncha kutib, keyin aylanish boshlanadi --
  // foydalanuvchi avval sahnani ko'rib olsin.
  const SPOTLIGHT_START_DELAY = 900;

  // Foydalanuvchi aralashgandan keyin aylanish shuncha vaqt to'xtab
  // turadi (o'qiyotgan kartasi tortib olinmasin).
  const SPOTLIGHT_RESUME_MS = 9000;

  document.querySelectorAll(".premiere-stage").forEach(function (stage) {
    const slides = Array.prototype.slice.call(stage.querySelectorAll(".premiere-slide"));
    if (!slides.length) return;

    const total = slides.length;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const wrap = stage.closest(".rail-wrap") || stage;

    let index = 0;
    let timer = null;
    let resumeTimer = null;

    /**
     * Kartaning markazga nisbatan o'rni.
     * Modul arifmetikasi aylanishni ta'minlaydi: oxirgi kartaning
     * "keyingisi" — birinchisi.
     * @returns {number} -2 | -1 | 0 | 1 | 2
     */
    const positionOf = function (slideIndex) {
      const offset = (slideIndex - index + total) % total;

      if (offset === 0) return 0;
      // Ikkita karta bo'lganda ikkinchisi faqat O'NGDA turadi: aks holda
      // bitta karta bir vaqtning o'zida ham chapda, ham o'ngda bo'lardi.
      if (offset === 1) return 1;
      if (offset === total - 1) return -1;

      // Qolganlari sahnadan tashqarida — qaysi tomonga yaqin bo'lsa,
      // o'sha tomonda kutib turadi va navbati kelganda chetdan suzib
      // kiradi.
      return offset <= total / 2 ? 2 : -2;
    };

    const paint = function () {
      slides.forEach(function (slide, slideIndex) {
        slide.setAttribute("data-pos", String(positionOf(slideIndex)));
      });
    };

    const go = function (step) {
      index = (index + step + total) % total;
      paint();
    };

    const start = function () {
      // Harakatni kamaytirish so'ralganda karta birinchisida qotib
      // qoladi — o'z-o'zidan almashinuv bo'lmaydi.
      if (reduced || timer || total < 2) return;
      timer = setInterval(function () { go(1); }, SPOTLIGHT_MS);
    };

    const stop = function () {
      clearInterval(timer);
      timer = null;
    };

    /** Foydalanuvchi aralashdi — vaqtincha to'xtatamiz. */
    const pause = function () {
      stop();
      clearTimeout(resumeTimer);
      resumeTimer = setTimeout(start, SPOTLIGHT_RESUME_MS);
    };

    // Boshlang'ich holat darhol chiziladi: sahna hech qachon "bo'sh"
    // ko'rinmasin (kutish faqat AYLANISHGA tegishli).
    paint();

    // Sichqoncha sahna ustida bo'lganda aylanmaydi.
    wrap.addEventListener("pointerenter", stop);
    wrap.addEventListener("pointerleave", start);

    /* O'q tugmalari. Bu sahna suriladigan tasma emas, shuning uchun
       main.js dagi umumiy `.rail-wrap` mantig'i (u `.rail` ni qidiradi)
       bu yerga tegmaydi — tugmalarni o'zimiz ulaymiz. */
    const prev = wrap.querySelector('[data-rail="prev"]');
    const next = wrap.querySelector('[data-rail="next"]');

    if (prev) prev.addEventListener("click", function () { go(-1); pause(); });
    if (next) next.addEventListener("click", function () { go(1); pause(); });

    // Yon kartani bosish ham uni markazga olib keladi.
    slides.forEach(function (slide, slideIndex) {
      slide.addEventListener("pointerdown", function () {
        if (slideIndex !== index) {
          index = slideIndex;
          paint();
        }
        pause();
      });
    });

    /* Bo'lim ekranda ko'ringandagina aylanadi: ko'rinmayotgan sahnani
       almashtirib turishning ma'nosi yo'q (va telefon batareyasini
       yeydi). */
    if ("IntersectionObserver" in window) {
      const stageObserver = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              setTimeout(start, SPOTLIGHT_START_DELAY);
            } else {
              stop();
            }
          });
        },
        { threshold: 0.25 }
      );
      stageObserver.observe(stage);
    } else {
      setTimeout(start, SPOTLIGHT_START_DELAY);
    }
  });

  /* --------------------------------------------------------------------
     Reveal animatsiyasi — ko'rinish maydoniga kirganda
     -------------------------------------------------------------------- */

  const revealTargets = document.querySelectorAll(".reveal");

  if (revealTargets.length) {
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              observer.unobserve(entry.target);
            }
          });
        },
        { rootMargin: "0px 0px -60px 0px", threshold: 0.05 }
      );
      revealTargets.forEach(function (target) { observer.observe(target); });
    } else {
      // Eski brauzerlarda animatsiyasiz ko'rsatamiz.
      revealTargets.forEach(function (target) { target.classList.add("is-visible"); });
    }
  }

  /* --------------------------------------------------------------------
     Modal oynalar
     data-modal-open="modal-id" / data-modal-close
     -------------------------------------------------------------------- */

  document.addEventListener("click", function (event) {
    const opener = event.target.closest("[data-modal-open]");
    if (opener) {
      const modal = document.getElementById(opener.dataset.modalOpen);
      if (modal) {
        modal.classList.add("is-open");
        document.body.classList.add("is-locked");
      }
      return;
    }

    const closer = event.target.closest("[data-modal-close]");
    if (closer) {
      const modal = closer.closest(".modal");
      if (modal) {
        modal.classList.remove("is-open");
        document.body.classList.remove("is-locked");
      }
      return;
    }

    // Fonga bosilganda yopiladi (panel ichiga bosilganda emas).
    if (event.target.classList.contains("modal")) {
      event.target.classList.remove("is-open");
      document.body.classList.remove("is-locked");
    }
  });

  /* --------------------------------------------------------------------
     Filtr formalari — submit tugmasisiz avtomatik yuborish
     Barcha filtr formalarida (filmlar, seriallar, do'kon, qidiruv)
     bir xil naqsh: select/checkbox/radio o'zgarishi bilanoq, matn
     maydonlari esa yozish to'xtaganda (debounce) formani yuboradi.
     -------------------------------------------------------------------- */

  document.querySelectorAll("form.js-auto-filter").forEach(function (form) {
    form.querySelectorAll("select, input[type=checkbox], input[type=radio]").forEach(function (field) {
      field.addEventListener("change", function () { form.submit(); });
    });

    form.querySelectorAll('input[type=search], input[type=text]').forEach(function (field) {
      let debounceTimer;
      field.addEventListener("input", function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () { form.submit(); }, 600);
      });
    });
  });

  /* --------------------------------------------------------------------
     Aktyorlar / rejissyor tablari — film va serial detali sahifasida
     -------------------------------------------------------------------- */

  document.addEventListener("click", function (event) {
    const tabButton = event.target.closest(".people-tabs__btn");
    if (!tabButton) return;

    const tabs = tabButton.closest(".people-tabs");
    const section = tabButton.closest(".section");
    if (!tabs || !section) return;

    tabs.querySelectorAll(".people-tabs__btn").forEach(function (btn) {
      btn.classList.toggle("is-active", btn === tabButton);
    });

    const target = tabButton.dataset.peopleTab;
    section.querySelectorAll("[data-people-panel]").forEach(function (panel) {
      panel.hidden = panel.dataset.peoplePanel !== target;
    });
  });

  /* --------------------------------------------------------------------
     Fasl tablari — serial detali sahifasida. Bir vaqtda faqat bitta
     faslning epizodlari ko'rinadi (yuqoridagi aktyor tablari bilan bir
     xil naqsh).
     -------------------------------------------------------------------- */

  document.addEventListener("click", function (event) {
    const seasonTab = event.target.closest(".season-tab");
    if (!seasonTab) return;

    const box = seasonTab.closest(".episodes");
    if (!box) return;

    box.querySelectorAll(".season-tab").forEach(function (tab) {
      const active = tab === seasonTab;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
    });

    const target = seasonTab.dataset.seasonTab;
    box.querySelectorAll("[data-season-panel]").forEach(function (panel) {
      panel.hidden = panel.dataset.seasonPanel !== target;
    });
  });

  /* --------------------------------------------------------------------
     Django messages -> toast
     -------------------------------------------------------------------- */

  const serverMessages = document.getElementById("server-messages");
  if (serverMessages) {
    serverMessages.querySelectorAll("[data-level]").forEach(function (item) {
      // Django tag'lari: debug, info, success, warning, error
      let level = item.dataset.level || "info";
      if (level.indexOf("error") !== -1) level = "error";
      else if (level.indexOf("success") !== -1) level = "success";
      else if (level.indexOf("warning") !== -1) level = "warning";
      else level = "info";

      toast(item.textContent.trim(), level);
    });
  }
})();
