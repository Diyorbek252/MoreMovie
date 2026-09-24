import type { Metadata } from "next";
import { redirect } from "next/navigation";

import Icon from "@/components/Icon";
import MovieCard from "@/components/MovieCard";
import { ApiError, getWatchlist } from "@/lib/api";

export const metadata: Metadata = { title: "Watchlist" };

export default async function WatchlistPage() {
  let watchlist;
  try {
    watchlist = await getWatchlist();
  } catch (err) {
    if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
      redirect("/login/?next=/watchlist/");
    }
    throw err;
  }

  return (
    <div className="container" style={{ paddingTop: "var(--s-6)", paddingBottom: "var(--s-8)" }}>
      <h1 className="detail__title" style={{ marginBottom: "var(--s-5)" }}>
        Watchlist
      </h1>

      {watchlist.results.length > 0 ? (
        <div className="grid">
          {watchlist.results.map((movie) => (
            <MovieCard movie={movie} key={movie.id} />
          ))}
        </div>
      ) : (
        <div className="empty">
          <Icon name="bookmark" />
          <h2 className="empty__title">Watchlist bo&apos;sh</h2>
          <p>Keyinroq ko&apos;rish uchun filmlarni shu yerga saqlang.</p>
        </div>
      )}
    </div>
  );
}
