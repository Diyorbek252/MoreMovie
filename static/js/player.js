/* ==========================================================================
   MORE-MOVIE — Video player
   Custom HTML5 boshqaruv: play/pause, progress, volume, fullscreen,
   klaviatura yorliqlari va ko'rish progressini serverga saqlash.
   ========================================================================== */

(function () {
  "use strict";

  const root = document.getElementById("player");
  if (!root) return;

  const video = root.querySelector("video");
  if (!video) return;

  const MM = window.MM || {};

  // Elementlar
  const playBtn = root.querySelector(".js-play");
  const centerBtn = root.querySelector(".js-center-play");
  const muteBtn = root.querySelector(".js-mute");
  const fullBtn = root.querySelector(".js-fullscreen");
  const volumeInput = root.querySelector(".js-volume");
  const progress = root.querySelector(".js-progress");
  const played = root.querySelector(".js-played");
  const buffered = root.querySelector(".js-buffered");
  const thumb = root.querySelector(".js-thumb");
  const timeLabel = root.querySelector(".js-time");

  const movieId = root.dataset.movie;
  const resumeAt = parseInt(root.dataset.resume || "0", 10);
  const progressUrl = document.body.dataset.urlProgress || "/api/progress/";

  /* --------------------------------------------------------------------
     Yordamchilar
     -------------------------------------------------------------------- */

  /** 125 -> "2:05",  3725 -> "1:02:05" */
  function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) seconds = 0;

    const total = Math.floor(seconds);
    const hrs = Math.floor(total / 3600);
    const mins = Math.floor((total % 3600) / 60);
    const secs = total % 60;

    const pad = function (n) { return n < 10 ? "0" + n : String(n); };

    if (hrs > 0) return hrs + ":" + pad(mins) + ":" + pad(secs);
    return mins + ":" + pad(secs);
  }

  /**
   * Tugma ichidagi ikkita ikonkadan birini ko'rsatadi.
   * Shablonda ular <span data-icon="play"> / <span data-icon="pause"> ko'rinishida.
   */
  function setIcon(button, name) {
    if (!button) return;
    button.querySelectorAll("[data-icon]").forEach(function (holder) {
      holder.hidden = holder.dataset.icon !== name;
    });
  }

  /* --------------------------------------------------------------------
     Play / pause
     -------------------------------------------------------------------- */

  function togglePlay() {
    if (video.paused) {
      // play() promise qaytaradi — brauzer bloklasa xato bermasin.
      const promise = video.play();
      if (promise && promise.catch) promise.catch(function () {});
    } else {
      video.pause();
    }
  }

  if (playBtn) playBtn.addEventListener("click", togglePlay);
  if (centerBtn) centerBtn.addEventListener("click", togglePlay);

  // Videoning o'ziga bosish ham play/pause qiladi.
  video.addEventListener("click", togglePlay);

  video.addEventListener("play", function () {
    root.classList.remove("is-paused");
    setIcon(playBtn, "pause");
  });

  video.addEventListener("pause", function () {
    root.classList.add("is-paused");
    setIcon(playBtn, "play");
  });

  /* --------------------------------------------------------------------
     Progress bar
     -------------------------------------------------------------------- */

  function updateProgress() {
    const duration = video.duration;
    if (!isFinite(duration) || duration === 0) return;

    const percent = (video.currentTime / duration) * 100;

    if (played) played.style.width = percent + "%";
    if (thumb) thumb.style.left = percent + "%";
    if (timeLabel) {
      timeLabel.textContent = formatTime(video.currentTime) + " / " + formatTime(duration);
    }

    // Bufferlangan qism.
    if (buffered && video.buffered.length) {
      const end = video.buffered.end(video.buffered.length - 1);
      buffered.style.width = (end / duration) * 100 + "%";
    }
  }

  video.addEventListener("timeupdate", updateProgress);
  video.addEventListener("progress", updateProgress);
  video.addEventListener("loadedmetadata", function () {
    updateProgress();
    // Oldingi safar to'xtagan joydan davom ettiramiz.
    if (resumeAt > 5 && resumeAt < video.duration - 10) {
      video.currentTime = resumeAt;
      if (MM.toast) {
        MM.toast(formatTime(resumeAt) + " dan davom ettirilmoqda", "info");
      }
    }
  });

  /** Bosilgan nuqtaga mos vaqtni hisoblaydi. */
  function seekTo(event) {
    if (!progress || !isFinite(video.duration)) return;
    const rect = progress.getBoundingClientRect();
    const ratio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
    video.currentTime = ratio * video.duration;
  }

  if (progress) {
    progress.addEventListener("click", seekTo);

    // Bosib turib sudrash bilan seek.
    let dragging = false;

    progress.addEventListener("mousedown", function (event) {
      dragging = true;
      seekTo(event);
    });

    document.addEventListener("mousemove", function (event) {
      if (dragging) seekTo(event);
    });

    document.addEventListener("mouseup", function () {
      dragging = false;
    });
  }

  /* --------------------------------------------------------------------
     Ovoz
     -------------------------------------------------------------------- */

  function syncVolumeUi() {
    const muted = video.muted || video.volume === 0;
    setIcon(muteBtn, muted ? "mute" : "volume");
    if (volumeInput) volumeInput.value = muted ? 0 : video.volume;
  }

  if (muteBtn) {
    muteBtn.addEventListener("click", function () {
      video.muted = !video.muted;
      // Ovoz 0 da qolgan bo'lsa eshitiladigan darajaga qaytaramiz.
      if (!video.muted && video.volume === 0) video.volume = 0.6;
      syncVolumeUi();
    });
  }

  if (volumeInput) {
    volumeInput.addEventListener("input", function () {
      video.volume = parseFloat(volumeInput.value);
      video.muted = video.volume === 0;
      setIcon(muteBtn, video.muted ? "mute" : "volume");
    });
  }

  video.addEventListener("volumechange", syncVolumeUi);

  /* --------------------------------------------------------------------
     Fullscreen
     -------------------------------------------------------------------- */

  if (fullBtn) {
    fullBtn.addEventListener("click", function () {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else if (root.requestFullscreen) {
        root.requestFullscreen().catch(function () {});
      } else if (video.webkitEnterFullscreen) {
        // iOS Safari faqat video elementini to'liq ekranga chiqaradi.
        video.webkitEnterFullscreen();
      }
    });
  }

  /* --------------------------------------------------------------------
     Boshqaruv panelini avtomatik yashirish
     -------------------------------------------------------------------- */

  let idleTimer = null;

  function wake() {
    root.classList.remove("is-idle");
    clearTimeout(idleTimer);
    // Faqat video o'ynayotganda yashiramiz.
    if (!video.paused) {
      idleTimer = setTimeout(function () {
        root.classList.add("is-idle");
      }, 2600);
    }
  }

  root.addEventListener("mousemove", wake);
  root.addEventListener("touchstart", wake, { passive: true });
  video.addEventListener("play", wake);
  video.addEventListener("pause", function () {
    clearTimeout(idleTimer);
    root.classList.remove("is-idle");
  });

  /* --------------------------------------------------------------------
     Klaviatura yorliqlari
     -------------------------------------------------------------------- */

  document.addEventListener("keydown", function (event) {
    const tag = (event.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;

    switch (event.key) {
      case " ":
      case "k":
        event.preventDefault();
        togglePlay();
        break;
      case "ArrowRight":
        event.preventDefault();
        video.currentTime = Math.min(video.currentTime + 10, video.duration || 0);
        break;
      case "ArrowLeft":
        event.preventDefault();
        video.currentTime = Math.max(video.currentTime - 10, 0);
        break;
      case "ArrowUp":
        event.preventDefault();
        video.volume = Math.min(video.volume + 0.1, 1);
        break;
      case "ArrowDown":
        event.preventDefault();
        video.volume = Math.max(video.volume - 0.1, 0);
        break;
      case "m":
        video.muted = !video.muted;
        break;
      case "f":
        if (fullBtn) fullBtn.click();
        break;
      default:
        break;
    }
  });

  /* --------------------------------------------------------------------
     Ko'rish progressini serverga saqlash
     -------------------------------------------------------------------- */

  let lastSaved = 0;

  /** Progressni yuboradi. `finished` — video oxirigacha ko'rilgan. */
  function saveProgress(finished) {
    if (!movieId || !MM.postJSON) return;

    const seconds = Math.floor(video.currentTime);
    // Har 15 soniyada bir marta — serverga ortiqcha yuk bermaslik uchun.
    if (!finished && Math.abs(seconds - lastSaved) < 15) return;

    lastSaved = seconds;

    MM.postJSON(progressUrl, {
      movie: movieId,
      seconds: seconds,
      finished: Boolean(finished),
    }).catch(function () {
      // Tarmoq xatosi ko'rishga xalaqit bermasligi kerak — jim o'tkazamiz.
    });
  }

  video.addEventListener("timeupdate", function () {
    saveProgress(false);
  });

  video.addEventListener("ended", function () {
    saveProgress(true);
    root.classList.add("is-paused");
  });

  // Sahifadan chiqishda oxirgi holatni yuboramiz.
  window.addEventListener("pagehide", function () {
    if (!movieId || video.currentTime < 5 || !navigator.sendBeacon) return;

    // sendBeacon header qo'sha olmaydi, shuning uchun CSRF tokenini
    // form maydoni sifatida yuboramiz (view POST ni ham o'qiy oladi).
    const form = new FormData();
    form.append("movie", movieId);
    form.append("seconds", String(Math.floor(video.currentTime)));
    form.append("finished", "");
    form.append("csrfmiddlewaretoken", MM.getCsrfToken ? MM.getCsrfToken() : "");

    navigator.sendBeacon(progressUrl, form);
  });

  // Boshlang'ich holat.
  root.classList.add("is-paused");
  syncVolumeUi();
  updateProgress();
})();
