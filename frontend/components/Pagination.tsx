import Link from "next/link";

import Icon from "./Icon";

/** `templates/partials/pagination.html` bilan bir xil naqsh — joriy sahifa
 * atrofidagi raqamlar + boshi/oxiri, qolgani "…" bilan qisqartiriladi. */
export default function Pagination({
  currentPage,
  totalPages,
  buildHref,
}: {
  currentPage: number;
  totalPages: number;
  buildHref: (page: number) => string;
}) {
  if (totalPages <= 1) return null;

  const pages: (number | "ellipsis")[] = [];
  for (let num = 1; num <= totalPages; num++) {
    if (
      num === 1 ||
      num === totalPages ||
      (num > currentPage - 3 && num < currentPage + 3)
    ) {
      pages.push(num);
    } else if (num === currentPage - 3 || num === currentPage + 3) {
      pages.push("ellipsis");
    }
  }

  return (
    <nav className="pagination" aria-label="Sahifalar">
      {currentPage > 1 ? (
        <Link href={buildHref(currentPage - 1)} aria-label="Oldingi sahifa" rel="prev">
          <Icon name="chevron-left" />
        </Link>
      ) : (
        <span className="is-disabled" aria-hidden="true">
          <Icon name="chevron-left" />
        </span>
      )}

      {pages.map((num, i) =>
        num === "ellipsis" ? (
          <span className="is-disabled" key={`e${i}`}>
            …
          </span>
        ) : num === currentPage ? (
          <span className="is-current" aria-current="page" key={num}>
            {num}
          </span>
        ) : (
          <Link href={buildHref(num)} key={num}>
            {num}
          </Link>
        )
      )}

      {currentPage < totalPages ? (
        <Link href={buildHref(currentPage + 1)} aria-label="Keyingi sahifa" rel="next">
          <Icon name="chevron-right" />
        </Link>
      ) : (
        <span className="is-disabled" aria-hidden="true">
          <Icon name="chevron-right" />
        </span>
      )}
    </nav>
  );
}
