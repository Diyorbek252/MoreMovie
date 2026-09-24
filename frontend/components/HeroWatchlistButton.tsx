"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiPost } from "@/lib/api-client";
import Icon from "./Icon";

/** Hero bo'limidagi "Add to Watchlist" — matnli katta tugma, `.js-watchlist`
 * bilan bir xil holat klassi, lekin `WatchlistButton` dan farqli ko'rinish. */
export default function HeroWatchlistButton({
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
      await apiPost(`/api/v1/movies/${slug}/watchlist/`);
      router.refresh();
    } catch (err) {
      setActive((prev) => !prev);
      if ((err as { status?: number }).status === 403) {
        router.push("/register/");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <button
      className={`btn btn--ghost btn--lg js-watchlist${active ? " is-active" : ""}`}
      type="button"
      onClick={toggle}
      disabled={pending}
    >
      <Icon name="plus" /> {active ? "Watchlist'da" : "Add to Watchlist"}
    </button>
  );
}
