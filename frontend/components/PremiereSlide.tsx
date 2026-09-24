"use client";

/**
 * Premyera afishasi — `templates/partials/premiere_slide.html` bilan bir
 * xil naqsh. `.card` EMAS — `.premiere-slide` (keng 16:9 kadr, matn
 * rasm ustida). `data-pos` atributi `PremiereCarousel` tomonidan
 * beriladi (sahnadagi o'rni: markaz/chap/o'ng/yashirin).
 */

import Link from "next/link";

import { mediaSrc } from "@/lib/media";
import type { MovieCard } from "@/lib/types";
import Icon from "./Icon";

export default function PremiereSlide({
  movie,
  pos,
  onSelect,
}: {
  movie: MovieCard;
  pos: number;
  onSelect: () => void;
}) {
  const href = `/movie/${movie.slug}/`;
  const image = movie.backdrop || movie.poster;

  return (
    <article className="premiere-slide" data-pos={pos} onPointerDown={onSelect}>
      <Link className="premiere-slide__media" href={href} aria-label={`${movie.title} sahifasi`}>
        {image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            className="premiere-slide__img"
            src={mediaSrc(image)}
            alt={movie.backdrop ? `${movie.title} kadri` : `${movie.title} posteri`}
            loading="lazy"
            width={960}
            height={540}
          />
        ) : (
          <span className="premiere-slide__fallback" aria-hidden="true">
            <Icon name="film" />
          </span>
        )}
      </Link>

      <span className="premiere-slide__scrim" aria-hidden="true"></span>

      <div className="premiere-slide__tags">
        {movie.is_upcoming_premiere && movie.premiere_date && (
          <span className="badge badge--premiere">
            <Icon name="calendar" /> {movie.premiere_label} ·{" "}
            {new Date(movie.premiere_date).toLocaleDateString("uz-UZ")}
          </span>
        )}
        {movie.is_premium && (
          <span className="badge badge--premium">
            <Icon name="crown" /> Premium
          </span>
        )}
      </div>

      <div className="premiere-slide__foot">
        <div className="premiere-slide__body">
          <h3 className="premiere-slide__title">
            <Link href={href}>{movie.title}</Link>
          </h3>
          <div className="premiere-slide__meta">
            <span>{movie.release_year}</span>
            <span>{movie.duration_display}</span>
            {Number(movie.imdb_rating) > 0 && (
              <span className="badge badge--imdb" title="IMDb reytingi">
                IMDb {movie.imdb_rating}
              </span>
            )}
          </div>
        </div>

        {/* Watchlist/Sevimlilar tugmalari bu yerda ATAYLAB yo'q — qo'shish
            faqat film sahifasidan (`DetailActions`). Bu yerda faqat
            tomosha tugmasi qoladi. */}
        {movie.can_watch && (
          <div className="premiere-slide__actions">
            <Link
              className="btn-icon premiere-slide__play"
              href={`${href}#player`}
              aria-label={`${movie.title} — tomosha qilish`}
            >
              <Icon name="play" />
            </Link>
          </div>
        )}
      </div>
    </article>
  );
}
