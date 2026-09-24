import Link from "next/link";

import type { Genre } from "@/lib/types";
import Icon from "./Icon";
import Rail from "./Rail";

/** `templates/partials/genre_rail.html` bilan bir xil naqsh — ko'p tanlovli
 * (OR mantig'i) janr filtri. Vergul bilan ajratilgan `?genre=` ro'yxatini
 * o'zi boshqaradi (checkbox kabi — bosilganda qo'shiladi/olib tashlanadi). */
export default function GenreRail({
  genres,
  selected,
  buildHref,
}: {
  genres: Genre[];
  selected: string[];
  buildHref: (slugs: string[]) => string;
}) {
  if (genres.length === 0) return null;

  function toggleHref(slug: string) {
    const next = selected.includes(slug)
      ? selected.filter((s) => s !== slug)
      : [...selected, slug];
    return buildHref(next);
  }

  return (
    <div className="catalog-rail">
      <div className="catalog-rail__head">
        <span className="catalog-rail__label">
          Janr bo&apos;yicha {selected.length > 0 && <em>{selected.length} ta tanlandi</em>}
        </span>
        {selected.length > 0 && (
          <Link className="section__link" href={buildHref([])}>
            <Icon name="x" /> Tozalash
          </Link>
        )}
      </div>

      <Rail className="rail--genres">
        {genres.map((genre) => {
          const active = selected.includes(genre.slug);
          return (
            <Link
              className={`genre-tile${active ? " is-active" : ""}`}
              href={toggleHref(genre.slug)}
              aria-pressed={active}
              key={genre.id}
            >
              <span className="genre-tile__glow" aria-hidden="true"></span>
              <span className="genre-tile__mark" aria-hidden="true">
                <Icon name="tag" />
              </span>
              <span className="genre-tile__name">{genre.name}</span>
              <span className="genre-tile__go" aria-hidden="true">
                <Icon name="chevron-right" />
              </span>
            </Link>
          );
        })}
      </Rail>
    </div>
  );
}
