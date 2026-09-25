import type { Metadata } from "next";

import GenreRail from "@/components/GenreRail";
import Icon from "@/components/Icon";
import MovieCard from "@/components/MovieCard";
import Pagination from "@/components/Pagination";
import SeriesCard from "@/components/SeriesCard";
import YearRail from "@/components/YearRail";
import { getCatalog, getGenres } from "@/lib/api";

const PAGE_SIZE = 24; // config/settings.py::MOVIES_PER_PAGE bilan bir xil.

const TYPE_LABELS: Record<string, string> = {
  all: "Hammasi",
  movie: "Kinolar",
  cartoon: "Multfilmlar",
  series: "Seriallar",
};

export async function generateMetadata({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}): Promise<Metadata> {
  const params = await searchParams;
  const label = TYPE_LABELS[params.type || "all"] || "Katalog";
  return { title: label };
}

export default async function CatalogPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams;
  const [catalog, genres] = await Promise.all([getCatalog(params), getGenres()]);

  const selectedGenres = (params.genre || "").split(",").filter(Boolean);
  const selectedYears = (params.year || "").split(",").filter(Boolean);
  const currentPage = Number(params.page) || 1;
  const totalPages = Math.ceil(catalog.count / PAGE_SIZE);

  function buildHref(overrides: Record<string, string | null>) {
    const next = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value) next.set(key, value);
    }
    for (const [key, value] of Object.entries(overrides)) {
      if (value === null) next.delete(key);
      else next.set(key, value);
    }
    next.delete("page");
    const qs = next.toString();
    return `/katalog/${qs ? `?${qs}` : ""}`;
  }

  return (
    <div className="container catalog">
      <GenreRail
        genres={genres}
        selected={selectedGenres}
        buildHref={(slugs) => buildHref({ genre: slugs.length ? slugs.join(",") : null })}
      />

      <YearRail
        years={catalog.available_years}
        selected={selectedYears}
        buildHref={(years) => buildHref({ year: years.length ? years.join(",") : null })}
      />

      <div className="results-bar">
        <span>
          <strong>{catalog.count}</strong> ta natija
          {params.q && ` — «${params.q}» so'rovi bo'yicha`}
        </span>
        {totalPages > 1 && (
          <span>
            {currentPage} / {totalPages} sahifa
          </span>
        )}
      </div>

      {catalog.results.length > 0 ? (
        <>
          <div className="grid">
            {catalog.results.map((item) =>
              item.kind === "series" ? (
                <SeriesCard series={item} key={`series-${item.id}`} />
              ) : (
                <MovieCard movie={item} key={`movie-${item.id}`} />
              )
            )}
          </div>

          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            buildHref={(page) => {
              const next = new URLSearchParams();
              for (const [key, value] of Object.entries(params)) {
                if (value) next.set(key, value);
              }
              next.set("page", String(page));
              return `/katalog/?${next.toString()}`;
            }}
          />
        </>
      ) : (
        <div className="empty">
          <Icon name="film" />
          <h2 className="empty__title">Hech narsa topilmadi</h2>
          <p>Filtrlarni o&apos;zgartirib yoki boshqa so&apos;z bilan qidirib ko&apos;ring.</p>
          <a className="btn btn--primary" href="/katalog/">
            Filtrlarni tozalash
          </a>
        </div>
      )}
    </div>
  );
}
