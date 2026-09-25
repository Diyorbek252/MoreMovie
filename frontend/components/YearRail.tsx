import Link from "next/link";

import Icon from "./Icon";
import Rail from "./Rail";

/** `templates/partials/year_rail.html` bilan bir xil naqsh — ko'p tanlovli
 * (OR mantig'i) yil filtri. Vergul bilan ajratilgan `?year=` ro'yxatini
 * o'zi boshqaradi (checkbox kabi — bosilganda qo'shiladi/olib tashlanadi). */
export default function YearRail({
  years,
  selected,
  buildHref,
}: {
  years: number[];
  selected: string[];
  buildHref: (years: string[]) => string;
}) {
  if (years.length === 0) return null;

  function toggleHref(year: string) {
    const next = selected.includes(year)
      ? selected.filter((y) => y !== year)
      : [...selected, year];
    return buildHref(next);
  }

  return (
    <div className="catalog-rail">
      <div className="catalog-rail__head">
        <span className="catalog-rail__label">
          Yil bo&apos;yicha {selected.length > 0 && <em>{selected.length} ta tanlandi</em>}
        </span>
        {selected.length > 0 && (
          <Link className="section__link" href={buildHref([])}>
            <Icon name="x" /> Tozalash
          </Link>
        )}
      </div>

      <Rail className="rail--years">
        {years.map((year) => {
          const value = String(year);
          const active = selected.includes(value);
          return (
            <Link
              className={`year-chip${active ? " is-active" : ""}`}
              href={toggleHref(value)}
              aria-pressed={active}
              key={year}
            >
              <span className="year-chip__glow" aria-hidden="true"></span>
              <span className="year-chip__num">{year}</span>
            </Link>
          );
        })}
      </Rail>
    </div>
  );
}
