"use client";

/** `.js-favorite` bilan bir xil naqsh — `WatchlistButton.tsx` ga qarang. */

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiPost } from "@/lib/api-client";
import Icon from "./Icon";

export default function FavoriteButton({
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
    setActive((prev) => !prev);
    try {
      await apiPost<{ added: boolean }>(`/api/v1/movies/${slug}/favorite/`);
      // `/favorites/` sahifasidagi ro'yxat ham yangilanishi uchun
      // (qarang: WatchlistButton).
      router.refresh();
    } catch (err) {
      setActive((prev) => !prev);
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
      className={`btn-icon js-favorite${active ? " is-active" : ""}`}
      type="button"
      onClick={toggle}
      disabled={pending}
      aria-label="Sevimlilarga qo'shish"
      aria-pressed={active}
    >
      <Icon name={active ? "heart-filled" : "heart"} />
    </button>
  );
}
