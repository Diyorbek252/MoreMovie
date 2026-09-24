"use client";

/** `.rate-box` — yulduzli baho + sharh formasi. `movies/api_v1.py` va
 * `reviews/api_v1.py` ga POST qiladi (movie) yoki (series) — `target` prop
 * orqali qaysi turini belgilaydi. */

import { useState } from "react";

import { apiPost, type ApiClientError } from "@/lib/api-client";
import Icon from "./Icon";

const STARS = [1, 2, 3, 4, 5];

export default function RatingBox({
  target,
  initialUserRating,
  initialComment,
  isPending,
}: {
  target: { movie: number } | { series: number };
  initialUserRating: number;
  initialComment: string;
  isPending: boolean;
}) {
  const [score, setScore] = useState(initialUserRating);
  const [hoverScore, setHoverScore] = useState(0);
  const [ratingStatus, setRatingStatus] = useState(
    initialUserRating ? `Sizning bahoyingiz: ${initialUserRating}/5` : "Hali baholamagansiz"
  );
  const [comment, setComment] = useState(initialComment);
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState(isPending);
  const [error, setError] = useState<string | null>(null);

  async function rate(value: number) {
    setScore(value);
    try {
      const res = await apiPost<{ user_rating: string | null }>("/api/v1/ratings/", {
        ...target,
        score: value,
      });
      setRatingStatus(`Sizning bahoyingiz: ${value}/5`);
      void res;
    } catch (err) {
      setError((err as ApiClientError).message);
    }
  }

  async function submitReview(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await apiPost("/api/v1/reviews/create/", { ...target, comment });
      setNotice("Sharhingiz moderatsiyaga yuborildi. Tasdiqlangach shu yerda paydo bo'ladi.");
      setPending(true);
    } catch (err) {
      setError((err as ApiClientError).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rate-box" style={{ marginBottom: "var(--s-5)" }}>
      <div className="rate-box__head">
        <Icon name="star" />
        <h3 className="rate-box__title">Filmni baholang</h3>
      </div>

      <div className="row" style={{ marginBottom: "var(--s-5)" }}>
        <div className="stars stars--input" role="group" aria-label="1 dan 5 gacha baho">
          {STARS.map((star) => (
            <button
              type="button"
              key={star}
              aria-label={`${star} yulduz`}
              onClick={() => rate(star)}
              onMouseEnter={() => setHoverScore(star)}
              onMouseLeave={() => setHoverScore(0)}
              className={star <= (hoverScore || score) ? "is-active" : ""}
            >
              <Icon name="star" />
            </button>
          ))}
        </div>
        <span className="muted" style={{ fontSize: "var(--fs-sm)" }}>
          {ratingStatus}
        </span>
      </div>

      <form className="stack" onSubmit={submitReview}>
        <label className="field__label" htmlFor="review-text">
          Sharhingiz
        </label>
        <textarea
          className="textarea"
          id="review-text"
          rows={4}
          placeholder="Film haqidagi fikringizni yozing (kamida 10 ta belgi)..."
          maxLength={2000}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />

        <div className="row" style={{ justifyContent: "space-between" }}>
          <p className="field__help">
            {error ? <span style={{ color: "var(--red)" }}>{error}</span> : "Sharhlar moderatsiyadan o'tgach chop etiladi."}
          </p>
          <button className="btn btn--primary" type="submit" disabled={submitting || comment.trim().length < 10}>
            {initialComment ? "Sharhni yangilash" : "Yuborish"}
          </button>
        </div>

        {notice && (
          <div className="alert alert--info">
            <Icon name="info" /> {notice}
          </div>
        )}
      </form>

      {pending && !notice && (
        <div className="alert alert--info" style={{ marginTop: "var(--s-4)" }}>
          <Icon name="clock" /> Sharhingiz hozirda moderatsiyada.
        </div>
      )}
    </div>
  );
}
