"use client";

/**
 * Watchlist tugmasi — `templates/partials/movie_card.html` dagi
 * `.js-watchlist` tugmasi bilan bir xil vizual holat (`is-active` klassi,
 * ikkita ikonka almashinuvi). Server komponentidan `initialActive` orqali
 * boshlang'ich holat olinadi (SSR — hech qanday "yaltirash" bo'lmaydi).
 */

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiPost } from "@/lib/api-client";
import Icon from "./Icon";

export default function WatchlistButton({
  slug,
  initialActive,
}: {
  slug: string;
  initialActive: boolean;
}) {
  const [active, setActive] = useState(initialActive);
  const [pending, setPending] = useState(false);
  const router = useRouter();

  async function toggle() {
    if (pending) return;
    setPending(true);
    // Optimistik yangilash — server javobi kelguncha darhol ko'rinadi.
    setActive((prev) => !prev);
    try {
      await apiPost<{ added: boolean }>(`/api/v1/movies/${slug}/watchlist/`);
    } catch (err) {
      setActive((prev) => !prev); // orqaga qaytarish
      const status = (err as { status?: number }).status;
      if (status === 403 || status === 401) {
        router.push(`/login?next=/movie/${slug}/`);
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <button
      className={`btn-icon js-watchlist${active ? " is-active" : ""}`}
      type="button"
      onClick={toggle}
      disabled={pending}
      aria-label="Watchlist'ga qo'shish"
      aria-pressed={active}
    >
      <span data-icon="outline" hidden={active}>
        <Icon name="bookmark" />
      </span>
      <span data-icon="filled" hidden={!active}>
        <Icon name="bookmark-filled" />
      </span>
    </button>
  );
}
