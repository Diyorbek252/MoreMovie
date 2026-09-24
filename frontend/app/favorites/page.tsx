import type { Metadata } from "next";
import { redirect } from "next/navigation";

import Icon from "@/components/Icon";
import MovieCard from "@/components/MovieCard";
import { ApiError, getFavorites } from "@/lib/api";

export const metadata: Metadata = { title: "Sevimlilar" };

export default async function FavoritesPage() {
  let favorites;
  try {
    favorites = await getFavorites();
  } catch (err) {
    if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
      redirect("/login/?next=/favorites/");
    }
    throw err;
  }

  return (
    <div className="container" style={{ paddingTop: "var(--s-6)", paddingBottom: "var(--s-8)" }}>
      <h1 className="detail__title" style={{ marginBottom: "var(--s-5)" }}>
        Sevimlilar
      </h1>

      {favorites.results.length > 0 ? (
        <div className="grid">
          {favorites.results.map((movie) => (
            <MovieCard movie={movie} key={movie.id} />
          ))}
        </div>
      ) : (
        <div className="empty">
          <Icon name="heart" />
          <h2 className="empty__title">Sevimlilar bo&apos;sh</h2>
          <p>Yoqtirgan filmlaringizni yurak tugmasi orqali shu yerga qo&apos;shing.</p>
        </div>
      )}
    </div>
  );
}
