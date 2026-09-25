import Link from "next/link";

import Icon from "./Icon";

/** "Eng yuqori baho" tugmasi — `?sort=rating` ni yoqadi/o'chiradi.
 *
 * Filtr EMAS, saralash: joriy bo'limdagi (kino/multfilm/serial, tanlangan
 * janr va yillar bilan) barcha kontent qoladi, faqat sayt foydalanuvchilari
 * bahosi (`avg_rating`, 0-5) bo'yicha yuqoridan pastga tartiblanadi —
 * core/catalog.py::SORT_OPTIONS["rating"]. Qayta bosilsa sukut bo'yicha
 * saralashga (eng yangi) qaytadi. */
export default function RatingSortToggle({
  active,
  buildHref,
}: {
  active: boolean;
  buildHref: (sort: string | null) => string;
}) {
  return (
    <Link
      className={`sort-toggle${active ? " is-active" : ""}`}
      href={buildHref(active ? null : "rating")}
      aria-pressed={active}
    >
      <Icon name="star" />
      Eng yuqori baho
      {active && <Icon name="x" />}
    </Link>
  );
}
