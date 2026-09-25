import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import EpisodePicker from "@/components/EpisodePicker";
import Icon from "@/components/Icon";
import PeopleTabs from "@/components/PeopleTabs";
import RatingBox from "@/components/RatingBox";
import Section from "@/components/Section";
import SeriesCard from "@/components/SeriesCard";
import { ApiError, getCurrentUser, getReviews, getSeries } from "@/lib/api";
import { mediaSrc } from "@/lib/media";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  try {
    const series = await getSeries(slug);
    const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "";
    const ogImage = mediaSrc(series.backdrop || series.poster);
    return {
      title: `${series.title} (${series.release_year})`,
      description: series.short_description,
      openGraph: {
        type: "video.tv_show",
        title: `${series.title} (${series.release_year})`,
        description: series.short_description,
        images: ogImage ? [`${siteUrl}${ogImage}`] : undefined,
      },
    };
  } catch {
    return {};
  }
}

const STATUS_LABELS: Record<string, string> = {
  announced: "E'lon qilingan",
  ongoing: "Davom etmoqda",
  completed: "Tugallangan",
};

export default async function SeriesDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let series;
  try {
    series = await getSeries(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const [user, reviews] = await Promise.all([getCurrentUser(), getReviews({ series: slug })]);

  return (
    <>
      <section className="detail">
        {series.backdrop && (
          <div className="detail__bg">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={mediaSrc(series.backdrop)} alt="" width={1600} height={900} />
          </div>
        )}
        <div className="detail__scrim"></div>

        <div className="container">
          <div className="detail__grid">
            <div className="detail__poster">
              {series.poster ? (
                <Image src={series.poster} alt={`${series.title} posteri`} width={300} height={450} />
              ) : (
                <div className="card__fallback">{series.title}</div>
              )}
            </div>

            <div>
              {/* Serialga XOS yuqori qator: tur yorlig'i + efir holati
                  (jonli nuqta bilan). Filmda bu o'rinda sifat belgilari
                  (1080p/720p) turadi — serialda ular yo'q. */}
              <p className="series-eyebrow">
                <span className="series-eyebrow__tag">
                  <Icon name="tv" /> Serial
                </span>
                <span className="series-eyebrow__status" data-status={series.status}>
                  <span className="series-eyebrow__dot" aria-hidden="true" />
                  {STATUS_LABELS[series.status] || series.status}
                </span>
              </p>

              <h1 className="detail__title">{series.title}</h1>
              {series.original_title && <p className="detail__original">{series.original_title}</p>}

              {series.user_rating_display != null && (
                <div className="detail__meta">
                  <span className="badge badge--rating" title="Sayt foydalanuvchilari bahosi">
                    <Icon name="star" />
                    <span>
                      <span>{series.user_rating_display}</span>/5
                    </span>
                  </span>
                </div>
              )}

              {series.seasons.length > 0 && series.trailer_url && (
                <div className="detail__actions">
                  <a className="btn btn--ghost btn--lg" href="#trailer">
                    <Icon name="info" /> Treyler
                  </a>
                </div>
              )}

              {series.genres.length > 0 && (
                <div className="detail__genres">
                  {series.genres.map((genre) => (
                    <Link className="chip chip--genre" href={`/katalog/?genre=${genre.slug}`} key={genre.id}>
                      <Icon name="tag" /> {genre.name}
                    </Link>
                  ))}
                </div>
              )}

              <p className="detail__desc">{series.description}</p>

              {/* `.facts` — `repeat(auto-fit, minmax(210px, 1fr))` grid,
                  ya'ni kartochkalar kenglikka qarab yonma-yon joylashadi. */}
              <div className="facts">
                <div className="fact">
                  <div className="fact__icon"><Icon name="layers" /></div>
                  <div>
                    <div className="fact__label">Fasllar</div>
                    <div className="fact__value">{series.season_count}</div>
                  </div>
                </div>

                <div className="fact">
                  <div className="fact__icon"><Icon name="film" /></div>
                  <div>
                    <div className="fact__label">Epizodlar</div>
                    <div className="fact__value">{series.episode_count}</div>
                  </div>
                </div>

                {series.countries.length > 0 && (
                  <div className="fact">
                    <div className="fact__icon"><Icon name="globe" /></div>
                    <div>
                      <div className="fact__label">Davlat</div>
                      <div className="fact__value">{series.countries.join(", ")}</div>
                    </div>
                  </div>
                )}

                {series.language && (
                  <div className="fact">
                    <div className="fact__icon"><Icon name="message" /></div>
                    <div>
                      <div className="fact__label">Til</div>
                      <div className="fact__value">{series.language}</div>
                    </div>
                  </div>
                )}

                {series.age_rating && (
                  <div className="fact">
                    <div className="fact__icon"><Icon name="user" /></div>
                    <div>
                      <div className="fact__label">Yosh chegarasi</div>
                      <div className="fact__value">{series.age_rating}</div>
                    </div>
                  </div>
                )}

                {Number(series.imdb_rating) > 0 && (
                  <div className="fact">
                    <div className="fact__icon"><Icon name="star" /></div>
                    <div>
                      <div className="fact__label">IMDb reytingi</div>
                      <div className="fact__value">{series.imdb_rating}</div>
                    </div>
                  </div>
                )}

                <div className="fact">
                  <div className="fact__icon"><Icon name="calendar" /></div>
                  <div>
                    <div className="fact__label">Efir yillari</div>
                    <div className="fact__value">
                      {series.release_year}
                      {series.end_year
                        ? ` — ${series.end_year}`
                        : series.status === "ongoing"
                          ? " — hozirgacha"
                          : ""}
                    </div>
                  </div>
                </div>

                {series.is_premium && (
                  <div className="fact fact--wide">
                    <div className="fact__icon"><Icon name="crown" /></div>
                    <div>
                      <div className="fact__label">Kirish</div>
                      <div className="fact__value">Premium obuna kerak</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="container">
        {series.seasons.length > 0 ? (
          <EpisodePicker seriesSlug={series.slug} seasons={series.seasons} />
        ) : series.trailer_url ? (
          <section className="section" id="player">
            <div className="video-frame">
              <iframe
                src={series.trailer_url}
                title={`${series.title} treyleri`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                loading="lazy"
              />
            </div>
          </section>
        ) : (
          <section className="section" id="player">
            <div className="player__unavailable">
              <Icon name="alert" />
              <p>Hozircha tomosha qilish uchun epizod mavjud emas.</p>
            </div>
          </section>
        )}

        {/* Treyler — epizodlar bor bo'lganda alohida bo'lim (epizod yo'q
            bo'lsa u yuqorida, `#player` o'rnida ko'rsatilgan). Film
            sahifasidagi bilan bir xil naqsh. */}
        {series.seasons.length > 0 && series.trailer_url && (
          <section className="section" id="trailer">
            <div className="section__head">
              <h2 className="section__title">Treyler</h2>
            </div>
            <div className="video-frame">
              <iframe
                src={series.trailer_url}
                title={`${series.title} treyleri`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                loading="lazy"
              />
            </div>
          </section>
        )}

        {(series.cast.length > 0 || series.directors.length > 0) && (
          <PeopleTabs cast={series.cast} directors={series.directors} />
        )}

        <section className="section">
          <div className="section__head">
            <h2 className="section__title">Sharhlar</h2>
            {reviews.results.length > 0 && (
              <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>
                {reviews.results.length} ta sharh
              </span>
            )}
          </div>

          {user ? (
            <RatingBox
              target={{ series: series.id }}
              initialUserRating={0}
              initialComment=""
              isPending={false}
            />
          ) : (
            <div className="alert alert--info">
              <Icon name="info" /> Baho berish va sharh yozish uchun{" "}
              <Link href={`/login/?next=/series/${series.slug}/`} style={{ color: "var(--red)", fontWeight: 600 }}>
                tizimga kiring
              </Link>
              .
            </div>
          )}

          {reviews.results.length > 0 ? (
            <div className="stack">
              {reviews.results.map((review) => (
                <article className="review" key={review.id}>
                  <div className="avatar">
                    {review.user.avatar_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={mediaSrc(review.user.avatar_url)} alt="" width={38} height={38} />
                    ) : (
                      review.user.display_name.slice(0, 2).toUpperCase()
                    )}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div className="review__head">
                      <span className="review__author">{review.user.display_name}</span>
                      {review.user_score != null && (
                        <span className="badge badge--rating">
                          <Icon name="star" /> {review.user_score}/5
                        </span>
                      )}
                      <span className="review__date">
                        {new Date(review.created_at).toLocaleDateString("uz-UZ")}
                      </span>
                    </div>
                    <p className="review__text">{review.comment}</p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty">
              <Icon name="message" />
              <h3 className="empty__title">Hozircha sharhlar yo&apos;q</h3>
              <p>Birinchi bo&apos;lib fikringizni bildiring!</p>
            </div>
          )}
        </section>
      </div>

      {series.similar_series.length > 0 && (
        <Section title="Similar Series">
          {series.similar_series.map((similar) => (
            <SeriesCard series={similar} key={similar.id} />
          ))}
        </Section>
      )}
    </>
  );
}
