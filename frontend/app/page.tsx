import Link from "next/link";

import HeroWatchlistButton from "@/components/HeroWatchlistButton";
import Icon from "@/components/Icon";
import MovieCard from "@/components/MovieCard";
import Section from "@/components/Section";
import SeriesCard from "@/components/SeriesCard";
import { getCurrentUser, getHome } from "@/lib/api";
import type { Genre, MovieCard as MovieCardType, SeriesCard as SeriesCardType } from "@/lib/types";

export const revalidate = 60;

export default async function HomePage() {
  const [home, user] = await Promise.all([getHome(), getCurrentUser()]);
  const { hero, rail_sections, continue_watching } = home;

  return (
    <>
      {hero && (
        <section className="hero">
          <div className="hero__bg">
            {hero.backdrop ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={hero.backdrop} alt="" fetchPriority="high" width={1600} height={900} />
            ) : hero.poster ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={hero.poster} alt="" fetchPriority="high" />
            ) : null}
          </div>
          <div className="hero__scrim"></div>

          <div className="container hero__content">
            <p className="hero__eyebrow">
              <Icon name="trending" /> Bugungi tanlov
            </p>

            <h1 className="hero__title">{hero.title}</h1>

            <div className="hero__meta">
              {hero.user_rating_display != null && (
                <span className="badge badge--rating" title="Sayt foydalanuvchilari bahosi">
                  <Icon name="star" /> {hero.user_rating_display}/5
                </span>
              )}
              {Number(hero.imdb_rating) > 0 && (
                <span className="badge badge--imdb" title="IMDb reytingi">
                  IMDb {hero.imdb_rating}
                </span>
              )}
              {hero.quality_badges.map((quality) => (
                <span className="badge badge--quality" key={quality}>
                  {quality}
                </span>
              ))}
              <span>{hero.release_year}</span>
              <span>{hero.duration_display}</span>
              {hero.genres.slice(0, 3).map((genre) => (
                <span key={genre.id}>{genre.name}</span>
              ))}
            </div>

            <p className="hero__desc">{hero.short_description}</p>

            <div className="hero__actions">
              {hero.can_watch && (
                <Link className="btn btn--primary btn--lg" href={`/movie/${hero.slug}/#player`}>
                  <Icon name="play" /> Watch Now
                </Link>
              )}
              <Link className="btn btn--ghost btn--lg" href={`/movie/${hero.slug}/`}>
                <Icon name="info" /> More Info
              </Link>
              {user ? (
                <HeroWatchlistButton slug={hero.slug} initialActive={hero.in_watchlist} />
              ) : (
                <Link className="btn btn--ghost btn--lg" href="/register/">
                  <Icon name="plus" /> Add to Watchlist
                </Link>
              )}
            </div>
          </div>
        </section>
      )}

      {continue_watching.length > 0 && (
        <Section title="Davom ettirish">
          {continue_watching.map((entry) => (
            <MovieCard movie={entry} progress={entry.progress_percent} key={entry.id} />
          ))}
        </Section>
      )}

      {rail_sections.map((section) => {
        if (section.items.length === 0) return null;

        if (section.key === "genres") {
          const genres = section.items as Genre[];
          return (
            <Section key={section.key} title={section.title} subtitle={section.subtitle} link={section.link} railClassName="rail--genres">
              {genres.map((genre) => (
                <Link className="genre-tile" href={`/katalog/?genre=${genre.slug}`} key={genre.id}>
                  <span className="genre-tile__glow" aria-hidden="true"></span>
                  <span className="genre-tile__mark" aria-hidden="true">
                    <Icon name="tag" />
                  </span>
                  <span className="genre-tile__name">{genre.name}</span>
                  <span className="genre-tile__go" aria-hidden="true">
                    <Icon name="chevron-right" />
                  </span>
                </Link>
              ))}
            </Section>
          );
        }

        if (section.key === "years") {
          const years = section.items as number[];
          return (
            <Section key={section.key} title={section.title} subtitle={section.subtitle} link={section.link} railClassName="rail--years">
              {years.map((year) => (
                <Link className="year-chip" href={`${section.link}?year=${year}`} key={year}>
                  <span className="year-chip__glow" aria-hidden="true"></span>
                  <span className="year-chip__num">{year}</span>
                </Link>
              ))}
            </Section>
          );
        }

        return (
          <Section key={section.key} title={section.title} subtitle={section.subtitle} link={section.link}>
            {section.is_series
              ? (section.items as SeriesCardType[]).map((series) => <SeriesCard series={series} key={series.id} />)
              : (section.items as MovieCardType[]).map((movie) => <MovieCard movie={movie} key={movie.id} />)}
          </Section>
        );
      })}

      {!user && (
        <section className="section reveal">
          <div className="container">
            <div className="cta">
              <h2 className="cta__title">Cheksiz kino zavqi...</h2>
              <p className="cta__text">
                Bepul ro&apos;yxatdan o&apos;ting — sevimli filmlaringizni saqlang, watchlist tuzing va
                to&apos;xtagan joyingizdan davom ettiring.
              </p>
              <Link className="btn btn--primary btn--lg" href="/register/">
                Hoziroq boshlash
              </Link>
            </div>
          </div>
        </section>
      )}
    </>
  );
}
