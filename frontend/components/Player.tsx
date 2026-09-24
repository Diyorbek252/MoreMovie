"use client";

/**
 * Video pleer — `templates/movies/movie_detail.html` dagi to'liq maxsus
 * boshqaruv paneli (`static/js/player.js`, 455 qator) o'rniga BROWSER'NING
 * o'zining `<video controls>` interfeysi ishlatiladi. Bu ATAYLAB SODDA
 * qilingan versiya — vizual jihatdan farq qiladi, lekin funksional jihatdan
 * to'liq: sifat almashtirish, davom ettirish (resume) va progress
 * kuzatuvi (15 soniyada bir marta + tugatilganda) saqlanib qolgan.
 *
 * TODO(keyingi bosqich): to'liq maxsus UI kerak bo'lsa, shu komponent
 * ichida `player.js` dagi progress-bar/sozlamalar menyusi qayta qurilishi
 * mumkin — API shartnomasi (`/progress/`, `/view/`) allaqachon tayyor.
 */

import { useEffect, useRef, useState } from "react";

import { apiPost } from "@/lib/api-client";
import type { VideoSource } from "@/lib/types";

const PROGRESS_INTERVAL_MS = 15_000;

export default function Player({
  slug,
  sources,
  poster,
  resumeAt,
}: {
  slug: string;
  sources: VideoSource[];
  poster?: string | null;
  resumeAt: number;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [activeQuality, setActiveQuality] = useState(sources[0]?.quality);
  const hasRegisteredView = useRef(false);

  const activeSource = sources.find((s) => s.quality === activeQuality) || sources[0];

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !resumeAt) return;
    const onLoaded = () => {
      video.currentTime = resumeAt;
    };
    video.addEventListener("loadedmetadata", onLoaded);
    return () => video.removeEventListener("loadedmetadata", onLoaded);
    // Faqat manba almashganda emas, boshlang'ich yuklanishda — shuning
    // uchun `activeSource` dependency'siz.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    function sendProgress(finished: boolean) {
      const seconds = Math.floor(video?.currentTime || 0);
      apiPost(`/api/v1/movies/${slug}/progress/`, { seconds, finished }).catch(() => {});
    }

    function onPlay() {
      if (!hasRegisteredView.current) {
        hasRegisteredView.current = true;
        apiPost(`/api/v1/movies/${slug}/view/`).catch(() => {});
      }
    }

    function onEnded() {
      sendProgress(true);
    }

    const interval = window.setInterval(() => {
      if (video && !video.paused) sendProgress(false);
    }, PROGRESS_INTERVAL_MS);

    video.addEventListener("play", onPlay);
    video.addEventListener("ended", onEnded);
    return () => {
      window.clearInterval(interval);
      video.removeEventListener("play", onPlay);
      video.removeEventListener("ended", onEnded);
    };
  }, [slug]);

  if (!activeSource) return null;

  return (
    <div className="player">
      <video ref={videoRef} controls preload="metadata" poster={poster || undefined} playsInline key={activeSource.url}>
        <source src={activeSource.url} />
        Brauzeringiz video ko&apos;rsatishni qo&apos;llab-quvvatlamaydi.
      </video>

      {sources.length > 1 && (
        <div className="player__quality-select" style={{ marginTop: "var(--s-2)" }}>
          {sources.map((source) => (
            <button
              key={source.quality}
              type="button"
              className={`player__menu-item${source.quality === activeQuality ? " is-active" : ""}`}
              onClick={() => setActiveQuality(source.quality)}
            >
              {source.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
