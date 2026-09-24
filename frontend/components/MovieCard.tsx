/**
 * Film kartasi — butun saytdagi YAGONA variant, `templates/partials/
 * movie_card.html` bilan bir xil CSS klasslari (`components.css` shu
 * klasslarga mo'ljallangan). Yangi ro'yxat uchun yangi komponent
 * yozmang, shuni ishlating (CLAUDE.md qoidasining Next.js ekvivalenti).
 *
 * Watchlist/Sevimlilar tugmalari bu yerda ATAYLAB yo'q — qo'shish
 * faqat film sahifasidan (`DetailActions`) qilinadi. Kartada faqat
 * holat BELGISI qoladi (`.card__saved`), u tugma emas.
 */

import Image from "next/image";
import Link from "next/link";

import type { MovieCard as MovieCardType } from "@/lib/types";
import Icon from "./Icon";

export default function MovieCard({
  movie,
  progress,
}: {
  movie: MovieCardType;
  /** 0-100 — "davom ettirish" chizig'i uchun (ixtiyoriy). */
  progress?: number;
}) {
  const href = `/movie/${movie.slug}/`;

  return (
    <article className={`card${progress ? " continue-card" : ""}`}>
      <div className="card__media">
        <Link href={href} aria-label={`${movie.title} sahifasi`}>
          {movie.poster ? (
            <Image
              className="card__poster"
              src={movie.poster}
              alt={`${movie.title} posteri`}
              width={300}
              height={450}
              loading="lazy"
            />
          ) : (
            <div className="card__fallback">{movie.title}</div>
          )}
        </Link>

        <div className="card__tags">
          <div className="card__qualities">
            {movie.is_premium && (
              <span className="badge badge--premium">
                <Icon name="crown" /> Premium
              </span>
            )}
          </div>
          <div className="card__saved" title="Watchlist'da" hidden={!movie.in_watchlist}>
            <Icon name="bookmark-filled" />
          </div>
        </div>

        {progress ? (
          <div className="continue-card__bar">
            <div className="continue-card__fill" style={{ width: `${progress}%` }} />
          </div>
        ) : null}
      </div>

      <div className="card__body">
        <h3 className="card__title">
          <Link href={href}>{movie.title}</Link>
        </h3>
        <div className="card__meta">
          <span>{movie.release_year}</span>
          {movie.genres[0] && <span>{movie.genres[0].name}</span>}
          {movie.user_rating_display != null && (
            <span className="card__score" title="Sayt foydalanuvchilari bahosi">
              <Icon name="star" /> {movie.user_rating_display}
            </span>
          )}
        </div>
      </div>
    </article>
  );
}
