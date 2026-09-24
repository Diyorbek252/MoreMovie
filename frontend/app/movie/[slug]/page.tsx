import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import DetailActions from "@/components/DetailActions";
import Icon from "@/components/Icon";
import MovieCard from "@/components/MovieCard";
import PeopleTabs from "@/components/PeopleTabs";
import Player from "@/components/Player";
import RatingBox from "@/components/RatingBox";
import Section from "@/components/Section";
import { ApiError, getCurrentUser, getMovie, getReviews } from "@/lib/api";
import { mediaSrc } from "@/lib/media";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  try {
    const movie = await getMovie(slug);
    // OG rasm tashqi xizmatlar (Facebook/Telegram bot) tomonidan
    // yuklanadi — ular ham ICHKI (127.0.0.1) manzilga yeta olmaydi,
    // shuning uchun saytning TASHQI manziliga ulanadi.
    const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "";
    const ogImage = mediaSrc(movie.backdrop || movie.poster);
    return {
      title: `${movie.title} (${movie.release_year})`,
      description: movie.meta_description_text,
      openGraph: {
        type: "video.movie",
        title: `${movie.title} (${movie.release_year})`,
        description: movie.meta_description_text,
        images: ogImage ? [`${siteUrl}${ogImage}`] : undefined,
      },
    };
  } catch {
    return {};
  }
}

export default async function MovieDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let movie;
  try {
    movie = await getMovie(slug);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const [user, reviews] = await Promise.all([getCurrentUser(), getReviews({ movie: slug })]);

  const hasLicenseNotice = movie.license_note || !movie.can_watch;

  return (
    <>
      <section className="detail">
        {movie.backdrop && (
          <div className="detail__bg">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={mediaSrc(movie.backdrop)} alt="" width={1600} height={900} />
          </div>
        )}
        <div className="detail__scrim"></div>

        <div className="container">
          <div className="detail__grid">
            <div className="detail__poster">
              {movie.poster ? (
                <Image src={movie.poster} alt={`${movie.title} posteri`} width={300} height={450} />
              ) : (
                <div className="card__fallback">{movie.title}</div>
              )}
            </div>

            <div>
              <h1 className="detail__title">{movie.title}</h1>
              {movie.original_title && <p className="detail__original">{movie.original_title}</p>}

              <div className="detail__meta">
                {movie.user_rating_display != null && (
                  <span className="badge badge--rating" title="Sayt foydalanuvchilari bahosi">
                    <Icon name="star" />
                    <span>
                      <span>{movie.user_rating_display}</span>/5
                    </span>
                  </span>
                )}
                {movie.quality_badges.map((q) => (
                  <span className="badge badge--quality" key={q}>
                    {q}
                  </span>
                ))}
              </div>

              {movie.genres.length > 0 && (
                <div className="detail__genres">
                  {movie.genres.map((genre) => (
                    <Link className="chip chip--genre" href={`/katalog/?genre=${genre.slug}`} key={genre.id}>
                      <Icon name="tag" /> {genre.name}
                    </Link>
                  ))}
                </div>
              )}

              <p className="detail__desc">{movie.description}</p>

              {hasLicenseNotice && (
                <div className="license-note">
                  <Icon name="shield" />
                  <div>
                    {movie.can_watch ? (
                      <>
                        <strong>Qonuniy kontent.</strong> Bu film{" "}
                        {movie.license_type_display.toLowerCase()} sifatida tarqatiladi.
                        {movie.license_note && (
                          <>
                            <br />
                            {movie.license_note}
                          </>
                        )}
                      </>
                    ) : (
                      <>
                        <strong>To&apos;liq versiya mavjud emas.</strong> Bu yozuv uchun bizda tomosha
                        qilish huquqi yo&apos;q — faqat rasmiy treylerni ko&apos;rishingiz mumkin.
                      </>
                    )}
                  </div>
                </div>
              )}

              <div className="detail__actions">
                {!movie.can_watch && movie.trailer_url && (
                  <a className="btn btn--primary btn--lg" href="#player">
                    <Icon name="play" /> Treylerni ko&apos;rish
                  </a>
                )}

                {user ? (
                  <DetailActions
                    slug={movie.slug}
                    inWatchlist={movie.in_watchlist}
                    inFavorite={movie.in_favorite}
                  />
                ) : (
                  <Link className="action-btn" href={`/login/?next=/movie/${movie.slug}/`}>
                    <Icon name="bookmark" /> Watchlist
                  </Link>
                )}

                {movie.can_download && movie.download_url && (
                  <a className="btn btn--outline btn--lg" href={movie.download_url} target="_blank" rel="noopener noreferrer" download>
                    <Icon name="download" /> Download
                  </a>
                )}
              </div>

              <div className="facts">
                {movie.countries.length > 0 && (
                  <div className="fact">
                    <div className="fact__icon"><Icon name="globe" /></div>
                    <div>
                      <div className="fact__label">Davlat</div>
                      <div className="fact__value">{movie.countries.join(", ")}</div>
                    </div>
                  </div>
                )}
                {movie.language && (
                  <div className="fact">
                    <div className="fact__icon"><Icon name="message" /></div>
                    <div>
                      <div className="fact__label">Til</div>
                      <div className="fact__value">{movie.language}</div>
                    </div>
                  </div>
                )}
                <div className="fact">
                  <div className="fact__icon"><Icon name="clock" /></div>
                  <div>
                    <div className="fact__label">Davomiyligi</div>
                    <div className="fact__value">{movie.duration_display}</div>
                  </div>
                </div>
                {movie.age_rating && (
                  <div className="fact">
                    <div className="fact__icon"><Icon name="user" /></div>
                    <div>
                      <div className="fact__label">Yosh chegarasi</div>
                      <div className="fact__value">{movie.age_rating}</div>
                    </div>
                  </div>
                )}
                {Number(movie.imdb_rating) > 0 && (
                  <div className="fact">
                    <div className="fact__icon"><Icon name="star" /></div>
                    <div>
                      <div className="fact__label">IMDb reytingi</div>
                      <div className="fact__value">{movie.imdb_rating}</div>
                    </div>
                  </div>
                )}
                <div className="fact">
                  <div className="fact__icon"><Icon name="calendar" /></div>
                  <div>
                    <div className="fact__label">Chiqarilgan yili</div>
                    <div className="fact__value">{movie.release_year}</div>
                  </div>
                </div>
                <div className="fact fact--wide">
                  <div className="fact__icon"><Icon name="shield" /></div>
                  <div>
                    <div className="fact__label">Litsenziya</div>
                    <div className="fact__value">{movie.license_type_display}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="container">
        <section className="section" id="player">
          {movie.can_play ? (
            <Player slug={movie.slug} sources={movie.video_sources} poster={mediaSrc(movie.backdrop)} resumeAt={movie.resume_at} />
          ) : movie.can_watch && movie.is_premium ? (
            <div className="premium-lock">
              {movie.backdrop && (
                // eslint-disable-next-line @next/next/no-img-element
                <img className="premium-lock__bg" src={mediaSrc(movie.backdrop)} alt="" width={1600} height={900} />
              )}
              <div className="premium-lock__content">
                <div className="premium-lock__icon">
                  <Icon name="crown" />
                </div>
                <h3 className="premium-lock__title">Bu kontent Premium obuna uchun</h3>
                <p className="premium-lock__text">
                  «{movie.title}» filmini tomosha qilish uchun Premium obunaga ega bo&apos;lishingiz kerak.
                </p>
                <Link className="btn btn--primary btn--lg" href="/obuna/">
                  <Icon name="crown" /> Obuna rejalarini ko&apos;rish
                </Link>
              </div>
            </div>
          ) : movie.trailer_url ? (
            <div className="video-frame">
              <iframe
                src={movie.trailer_url}
                title={`${movie.title} treyleri`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                loading="lazy"
              />
            </div>
          ) : null}
        </section>
      </div>

      <div className="container">
        {(movie.cast.length > 0 || movie.directors.length > 0) && (
          <PeopleTabs cast={movie.cast} directors={movie.directors} />
        )}

        {movie.can_play && movie.trailer_url && (
          <section className="section" id="trailer">
            <div className="section__head">
              <h2 className="section__title">Treyler</h2>
            </div>
            <div className="video-frame">
              <iframe
                src={movie.trailer_url}
                title={`${movie.title} treyleri`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                loading="lazy"
              />
            </div>
          </section>
        )}

        {movie.screenshots.length > 0 && (
          <section className="section">
            <div className="section__head">
              <h2 className="section__title">Kadrlar</h2>
            </div>
            <div className="shots">
              {movie.screenshots.map((shot) => (
                <Image key={shot.id} src={shot.image} alt={shot.caption || movie.title} width={480} height={270} />
              ))}
            </div>
          </section>
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
              target={{ movie: movie.id }}
              initialUserRating={movie.user_rating}
              initialComment=""
              isPending={false}
            />
          ) : (
            <div className="alert alert--info">
              <Icon name="info" /> Baho berish va sharh yozish uchun{" "}
              <Link href={`/login/?next=/movie/${movie.slug}/`} style={{ color: "var(--red)", fontWeight: 600 }}>
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

      {movie.similar_movies.length > 0 && (
        <Section title="Similar Movies">
          {movie.similar_movies.map((similar) => (
            <MovieCard movie={similar} key={similar.id} />
          ))}
        </Section>
      )}
    </>
  );
}
