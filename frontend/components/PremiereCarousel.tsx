"use client";

/**
 * Premyeralar — markazlashgan cheksiz («loop») karusel.
 * `static/js/main.js` dagi mantiqning React ekvivalenti (bir xil
 * vaqt oralig'i/xatti-harakat): kartalar ustma-ust turadi, har biriga
 * `data-pos` beriladi (-2 chapda tashqarida, -1 chapda, 0 markazda,
 * +1 o'ngda, +2 o'ngda tashqarida). Yorqin karta doim markazda;
 * belgilangan oraliqda navbat keyingisiga o'tadi, oxiridan keyin yana
 * birinchisi keladi.
 */

import { useEffect, useRef, useState } from "react";

import type { MovieCard } from "@/lib/types";
import Icon from "./Icon";
import PremiereSlide from "./PremiereSlide";

const SPOTLIGHT_MS = 4000;
const SPOTLIGHT_START_DELAY = 900;
const SPOTLIGHT_RESUME_MS = 9000;

function positionOf(slideIndex: number, index: number, total: number): number {
  const offset = (slideIndex - index + total) % total;
  if (offset === 0) return 0;
  // Ikkita karta bo'lganda ikkinchisi faqat O'NGDA — aks holda bitta
  // karta bir vaqtning o'zida ham chapda, ham o'ngda bo'lardi.
  if (offset === 1) return 1;
  if (offset === total - 1) return -1;
  return offset <= total / 2 ? 2 : -2;
}

export default function PremiereCarousel({
  movies,
  isAuthenticated,
}: {
  movies: MovieCard[];
  isAuthenticated: boolean;
}) {
  const total = movies.length;
  const [index, setIndex] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const resumeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reducedRef = useRef(false);

  useEffect(() => {
    reducedRef.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  function stop() {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  function start() {
    // Harakatni kamaytirish so'ralganda karta birinchisida qotib qoladi.
    if (reducedRef.current || timerRef.current || total < 2) return;
    timerRef.current = setInterval(() => {
      setIndex((i) => (i + 1) % total);
    }, SPOTLIGHT_MS);
  }

  function pause() {
    stop();
    if (resumeTimerRef.current) clearTimeout(resumeTimerRef.current);
    resumeTimerRef.current = setTimeout(start, SPOTLIGHT_RESUME_MS);
  }

  function go(step: number) {
    setIndex((i) => (i + step + total) % total);
    pause();
  }

  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap || total < 2) return;

    // Bo'lim ekranda ko'ringandagina aylanadi — ko'rinmayotgan sahnani
    // almashtirib turishning ma'nosi yo'q (batareya tejaladi).
    if (!("IntersectionObserver" in window)) {
      const t = setTimeout(start, SPOTLIGHT_START_DELAY);
      return () => clearTimeout(t);
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setTimeout(start, SPOTLIGHT_START_DELAY);
          } else {
            stop();
          }
        });
      },
      { threshold: 0.3 }
    );
    observer.observe(wrap);

    return () => {
      observer.disconnect();
      stop();
      if (resumeTimerRef.current) clearTimeout(resumeTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [total]);

  if (total === 0) return null;

  return (
    <div className="rail-wrap" ref={wrapRef} onPointerEnter={stop} onPointerLeave={start}>
      <button className="rail-btn rail-btn--prev" type="button" aria-label="Orqaga" onClick={() => go(-1)}>
        <Icon name="chevron-left" />
      </button>

      <div className="premiere-stage">
        {movies.map((movie, slideIndex) => (
          <PremiereSlide
            movie={movie}
            pos={positionOf(slideIndex, index, total)}
            isAuthenticated={isAuthenticated}
            onSelect={() => {
              if (slideIndex !== index) setIndex(slideIndex);
              pause();
            }}
            key={movie.id}
          />
        ))}
      </div>

      <button className="rail-btn rail-btn--next" type="button" aria-label="Oldinga" onClick={() => go(1)}>
        <Icon name="chevron-right" />
      </button>
    </div>
  );
}
