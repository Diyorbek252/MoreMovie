"use client";

/**
 * Fasllar/epizodlar tanlovi + pleer — `templates/series/series_detail.html`
 * bilan bir xil naqsh, faqat `?episode=` query o'rniga client state
 * ishlatiladi (fasl/epizod almashtirilganda sahifa qayta yuklanmaydi).
 *
 * Barcha epizodlar ma'lumoti (jumladan `video_source`) BIR so'rov bilan
 * keladi — HUQUQIY xavfsizlik serializer darajasida (`can_play` har bir
 * epizod uchun alohida tekshiriladi, `video_source` faqat ruxsat
 * berilganda to'ladi), shuning uchun mijozda erkin almashtirish xavfsiz.
 *
 * Progress/resume — Series/Episode uchun umuman yo'q (faqat Movie'da
 * ViewHistory bor): pleer har doim boshidan boshlanadi.
 */

import { useEffect, useRef, useState } from "react";

import { apiPost } from "@/lib/api-client";
import { mediaSrc } from "@/lib/media";
import type { Episode, Season } from "@/lib/types";
import Icon from "./Icon";

function findDefaultEpisode(seasons: Season[]): { season: Season; episode: Episode } | null {
  for (const season of seasons) {
    const playable = season.episodes.find((e) => e.can_watch);
    if (playable) return { season, episode: playable };
  }
  const first = seasons[0];
  return first?.episodes[0] ? { season: first, episode: first.episodes[0] } : null;
}

export default function EpisodePicker({ seriesSlug, seasons }: { seriesSlug: string; seasons: Season[] }) {
  const initial = findDefaultEpisode(seasons);
  const [activeSeasonId, setActiveSeasonId] = useState(initial?.season.id ?? seasons[0]?.id);
  const [currentEpisode, setCurrentEpisode] = useState<Episode | null>(initial?.episode ?? null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const registeredViewFor = useRef<number | null>(null);

  const activeSeason = seasons.find((s) => s.id === activeSeasonId) || seasons[0];

  function selectEpisode(episode: Episode) {
    setCurrentEpisode(episode);
    document.getElementById("player")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !currentEpisode) return;

    function onPlay() {
      if (!currentEpisode || registeredViewFor.current === currentEpisode.id) return;
      registeredViewFor.current = currentEpisode.id;
      apiPost(`/api/v1/series/${seriesSlug}/episodes/${currentEpisode.id}/view/`).catch(() => {});
    }

    video.addEventListener("play", onPlay);
    return () => video.removeEventListener("play", onPlay);
  }, [currentEpisode, seriesSlug]);

  if (!currentEpisode || !activeSeason) {
    return (
      <div className="player__unavailable">
        <Icon name="alert" />
        <p>Hozircha tomosha qilish uchun epizod mavjud emas.</p>
      </div>
    );
  }

  return (
    <>
      <section className="section" id="player">
        {currentEpisode.can_play ? (
          <div className="player">
            <video
              ref={videoRef}
              controls
              preload="metadata"
              poster={mediaSrc(currentEpisode.display_thumbnail_url) || undefined}
              playsInline
              key={currentEpisode.id}
            >
              <source src={currentEpisode.video_source} />
              Brauzeringiz video ko&apos;rsatishni qo&apos;llab-quvvatlamaydi.
            </video>
          </div>
        ) : currentEpisode.can_watch ? (
          <div className="premium-lock">
            <div className="premium-lock__content">
              <div className="premium-lock__icon">
                <Icon name="crown" />
              </div>
              <h3 className="premium-lock__title">Bu kontent Premium obuna uchun</h3>
              <a className="btn btn--primary btn--lg" href="/obuna/">
                <Icon name="crown" /> Obuna rejalarini ko&apos;rish
              </a>
            </div>
          </div>
        ) : (
          <div className="player__unavailable">
            <Icon name="alert" />
            <p>Bu epizod uchun video manba hali qo&apos;shilmagan.</p>
          </div>
        )}
      </section>

      <h2 style={{ marginTop: "var(--s-4)", fontSize: "var(--fs-lg)" }}>
        {activeSeason.display_title} — {currentEpisode.episode_number}-epizod: {currentEpisode.title}
      </h2>
      {currentEpisode.description && (
        <p className="muted" style={{ marginTop: "var(--s-2)" }}>
          {currentEpisode.description}
        </p>
      )}

      <section className="section">
        <div className="section__head">
          <h2 className="section__title">Fasllar va epizodlar</h2>
        </div>

        <div className="episodes">
          {seasons.length > 1 && (
            <div className="season-tabs" role="tablist" aria-label="Fasllar">
              {seasons.map((season) => (
                <button
                  key={season.id}
                  type="button"
                  role="tab"
                  className={`season-tab${season.id === activeSeasonId ? " is-active" : ""}`}
                  aria-selected={season.id === activeSeasonId}
                  onClick={() => setActiveSeasonId(season.id)}
                >
                  {season.display_title}
                  <span className="season-tab__count">{season.episodes.length}</span>
                </button>
              ))}
            </div>
          )}

          <ol className="ep-list">
            {activeSeason.episodes.map((episode) => (
              <li
                key={episode.id}
                className={`ep${currentEpisode.id === episode.id ? " is-current" : ""}${!episode.can_watch ? " is-locked" : ""}`}
              >
                {episode.can_watch ? (
                  <button className="ep__row" type="button" onClick={() => selectEpisode(episode)}>
                    <span className="ep__num">
                      <b>{episode.episode_number}</b>
                      <span className="ep__play">
                        <Icon name="play" />
                      </span>
                    </span>
                    <span className="ep__body">
                      <span className="ep__title">{episode.title}</span>
                      {episode.description && <span className="ep__desc">{episode.description}</span>}
                    </span>
                    <span className="ep__side">
                      {currentEpisode.id === episode.id && (
                        <span className="ep__now" aria-label="Hozir ijro etilmoqda">
                          <i></i>
                          <i></i>
                          <i></i>
                        </span>
                      )}
                      <span className="ep__time">{episode.duration_display}</span>
                    </span>
                  </button>
                ) : (
                  <div className="ep__row">
                    <span className="ep__num">
                      <b>{episode.episode_number}</b>
                    </span>
                    <span className="ep__body">
                      <span className="ep__title">{episode.title}</span>
                      {episode.description && <span className="ep__desc">{episode.description}</span>}
                    </span>
                    <span className="ep__side">
                      <span className="ep__state">Video yo&apos;q</span>
                    </span>
                  </div>
                )}
              </li>
            ))}
          </ol>
        </div>
      </section>
    </>
  );
}
