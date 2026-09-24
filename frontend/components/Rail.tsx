"use client";

/**
 * Gorizontal surish (scroll) qatori — `templates/partials/movie_row.html`
 * dagi `.rail-wrap`/`.rail-btn`/`.rail` bilan bir xil klasslar. Faqat
 * o'q tugmalarining o'zi interaktiv — ichidagi kartalar (`children`)
 * Server Component sifatida keladi.
 */

import { useRef } from "react";

import Icon from "./Icon";

export default function Rail({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  function scroll(direction: 1 | -1) {
    const el = ref.current;
    if (!el) return;
    el.scrollBy({ left: direction * el.clientWidth * 0.8, behavior: "smooth" });
  }

  return (
    <div className="rail-wrap">
      <button
        className="rail-btn rail-btn--prev"
        type="button"
        aria-label="Orqaga"
        onClick={() => scroll(-1)}
      >
        <Icon name="chevron-left" />
      </button>

      <div className={`rail${className ? ` ${className}` : ""}`} ref={ref}>
        {children}
      </div>

      <button
        className="rail-btn rail-btn--next"
        type="button"
        aria-label="Oldinga"
        onClick={() => scroll(1)}
      >
        <Icon name="chevron-right" />
      </button>
    </div>
  );
}
