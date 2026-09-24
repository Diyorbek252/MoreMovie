"use client";

/** Qidiruv qutisi — `.nav-search`/`.nav-search__box` (`is-open` klassi bilan
 * ochiladi/yopiladi). Live-AJAX taklif (`search.js`) hozircha ko'chirilmagan —
 * forma yuborilganda katalogga `?q=` bilan o'tadi (to'liq ishlaydi, faqat
 * "yozayotganda natija" tezkor ko'rinishi yo'q). */

import { useRouter } from "next/navigation";
import { useState } from "react";

import Icon from "./Icon";

export default function NavSearch() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const router = useRouter();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const query = q.trim();
    router.push(query ? `/katalog/?q=${encodeURIComponent(query)}` : "/katalog/");
    setOpen(false);
  }

  return (
    <div className={`nav-search${open ? " is-open" : ""}`}>
      <button
        className="btn-icon"
        type="button"
        aria-label="Qidiruv"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <Icon name="search" />
      </button>
      <form className="nav-search__box" onSubmit={onSubmit} role="search">
        <label className="sr-only" htmlFor="search-input">
          Film qidirish
        </label>
        <input
          className="nav-search__input"
          type="search"
          id="search-input"
          placeholder="Search movies..."
          autoComplete="off"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </form>
    </div>
  );
}
