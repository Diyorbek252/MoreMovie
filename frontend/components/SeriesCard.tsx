/** `templates/partials/series_card.html` bilan bir xil naqsh — watchlist/
 * favorite tugmalari yo'q, bu modellar hozircha faqat Movie'ga bog'langan. */

import Image from "next/image";
import Link from "next/link";

import type { SeriesCard as SeriesCardType } from "@/lib/types";
import Icon from "./Icon";

export default function SeriesCard({ series }: { series: SeriesCardType }) {
  const href = `/series/${series.slug}/`;

  return (
    <article className="card">
      <div className="card__media">
        <Link href={href} aria-label={`${series.title} sahifasi`}>
          {series.poster ? (
            <Image
              className="card__poster"
              src={series.poster}
              alt={`${series.title} posteri`}
              width={300}
              height={450}
              loading="lazy"
            />
          ) : (
            <div className="card__fallback">{series.title}</div>
          )}
        </Link>

        {series.is_premium && (
          <div className="card__tags">
            <div className="card__qualities">
              <span className="badge badge--premium">
                <Icon name="crown" /> Premium
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="card__body">
        <h3 className="card__title">
          <Link href={href}>{series.title}</Link>
        </h3>
        <div className="card__meta">
          <span>{series.release_year}</span>
          {series.genres[0] && <span>{series.genres[0].name}</span>}
          {series.user_rating_display != null && (
            <span className="card__score" title="Sayt foydalanuvchilari bahosi">
              <Icon name="star" /> {series.user_rating_display}
            </span>
          )}
        </div>
      </div>
    </article>
  );
}
