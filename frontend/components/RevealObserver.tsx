"use client";

/**
 * `.reveal` klassidagi bo'limlarni skroll qilinganda ko'rsatadi.
 *
 * MUHIM: `static/css/base.css` da `.reveal { opacity: 0; }` — asl saytda
 * `static/js/main.js` IntersectionObserver orqali ko'rinishga kirgan
 * elementga `.is-visible` qo'shadi (shunda CSS animatsiyasi ishga
 * tushadi). Bu React ekvivalenti — root layout'da BIR MARTA
 * o'rnatiladi va butun sahifadagi barcha `.reveal` elementlarni kuzatadi
 * (Next.js sahifa navigatsiyasida yangi elementlar qo'shilsa ham).
 */

import { useEffect } from "react";

export default function RevealObserver() {
  useEffect(() => {
    const seen = new Set<Element>();

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.05, rootMargin: "0px 0px -5% 0px" }
    );

    function observeAll() {
      document.querySelectorAll(".reveal").forEach((el) => {
        if (!seen.has(el)) {
          seen.add(el);
          observer.observe(el);
        }
      });
    }

    observeAll();

    // Yangi bo'lim DOM'ga keyinroq qo'shilsa (masalan client-side
    // navigatsiya) ham kuzatilishi uchun.
    const mutationObserver = new MutationObserver(observeAll);
    mutationObserver.observe(document.body, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
      mutationObserver.disconnect();
    };
  }, []);

  return null;
}
