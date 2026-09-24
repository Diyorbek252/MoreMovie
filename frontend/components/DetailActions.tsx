"use client";

/**
 * Film sahifasidagi katta "Watchlist" va "Sevimlilar" tugmalari.
 *
 * Watchlist/Sevimlilarga qo'shishning YAGONA joyi — film kartalarida
 * (`MovieCard`, `PremiereSlide`) bu tugmalar ATAYLAB yo'q, u yerda faqat
 * holat belgisi ko'rsatiladi. Uslublar: `styles/detail-actions.css`.
 */

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiPost } from "@/lib/api-client";
import Icon from "./Icon";

type Kind = "watchlist" | "favorite";

const LABELS: Record<Kind, { on: string; off: string; ariaLabel: string }> = {
  watchlist: {
    on: "Saqlangan",
    off: "Watchlist",
    ariaLabel: "Watchlist'ga qo'shish",
  },
  favorite: {
    on: "Sevimlilarda",
    off: "Sevimlilar",
    ariaLabel: "Sevimlilarga qo'shish",
  },
};

function ActionButton({
  kind,
  slug,
  initialActive,
}: {
  kind: Kind;
  slug: string;
  initialActive: boolean;
}) {
  const [active, setActive] = useState(initialActive);
  const [pending, setPending] = useState(false);
  const router = useRouter();
  const labels = LABELS[kind];

  async function toggle() {
    if (pending) return;
    setPending(true);
    // Optimistik yangilash — javobni kutmasdan darhol ko'rinadi.
    setActive((prev) => !prev);
    try {
      await apiPost(`/api/v1/movies/${slug}/${kind}/`);
      // `/watchlist/` va `/favorites/` ro'yxatlari ham yangilanishi uchun.
      router.refresh();
    } catch (err) {
      setActive((prev) => !prev); // orqaga qaytarish
      const status = (err as { status?: number }).status;
      if (status === 401 || status === 403) {
        router.push(`/login/?next=/movie/${slug}/`);
      }
    } finally {
      setPending(false);
    }
  }

  const icon =
    kind === "watchlist"
      ? active
        ? "bookmark-filled"
        : "bookmark"
      : active
        ? "heart-filled"
        : "heart";

  return (
    <button
      className={`action-btn action-btn--${kind}${active ? " is-active" : ""}`}
      type="button"
      onClick={toggle}
      disabled={pending}
      aria-label={labels.ariaLabel}
      aria-pressed={active}
    >
      <Icon name={icon} />
      {active ? labels.on : labels.off}
    </button>
  );
}

export default function DetailActions({
  slug,
  inWatchlist,
  inFavorite,
}: {
  slug: string;
  inWatchlist: boolean;
  inFavorite: boolean;
}) {
  return (
    <div className="action-btns">
      <ActionButton kind="watchlist" slug={slug} initialActive={inWatchlist} />
      <ActionButton kind="favorite" slug={slug} initialActive={inFavorite} />
    </div>
  );
}
