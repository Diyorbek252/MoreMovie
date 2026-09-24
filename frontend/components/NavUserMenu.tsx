"use client";

/**
 * Foydalanuvchi dropdown menyusi + mobil burger/drawer.
 * `.user-menu.is-open`, `.nav__burger.is-open`, `.drawer.is-open` — CSS
 * `is-open` klassini kutadi (`static/css/pages.css`), shu bilan bir xil
 * vizual naqsh saqlanadi.
 */

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiPost } from "@/lib/api-client";
import { mediaSrc } from "@/lib/media";
import type { User } from "@/lib/types";
import Icon from "./Icon";

export default function NavUserMenu({ user }: { user: User | null }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const router = useRouter();

  async function logout() {
    try {
      await apiPost("/api/v1/auth/logout/");
    } finally {
      router.push("/");
      router.refresh();
    }
  }

  if (!user) {
    return (
      <>
        <Link className="btn btn--ghost btn--sm" href="/login/">
          Login
        </Link>
        <Link className="btn btn--primary btn--sm" href="/register/">
          Register
        </Link>
        <button
          className={`nav__burger${drawerOpen ? " is-open" : ""}`}
          type="button"
          aria-label="Menyu"
          aria-expanded={drawerOpen}
          onClick={() => setDrawerOpen((v) => !v)}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
        <div className={`drawer${drawerOpen ? " is-open" : ""}`}>
          <nav className="container" aria-label="Mobil menyu">
            <a className="drawer__link" href="/katalog/?type=movie">
              <Icon name="film" /> Kinolar
            </a>
            <a className="drawer__link" href="/katalog/?type=cartoon">
              <Icon name="sparkle" /> Multfilmlar
            </a>
            <a className="drawer__link" href="/katalog/?type=series">
              <Icon name="tv" /> Seriallar
            </a>
            <a className="drawer__link" href="/shop/">
              <Icon name="coin" /> Do&apos;kon
            </a>
            <div className="stack" style={{ marginTop: "var(--s-5)" }}>
              <Link className="btn btn--primary btn--block" href="/register/">
                Ro&apos;yxatdan o&apos;tish
              </Link>
              <Link className="btn btn--ghost btn--block" href="/login/">
                Kirish
              </Link>
            </div>
          </nav>
        </div>
      </>
    );
  }

  return (
    <>
      <Link className="btn-icon" href="/favorites/" aria-label="Sevimlilar" title="Favorites">
        <Icon name="heart" />
      </Link>
      <Link className="btn-icon" href="/watchlist/" aria-label="Watchlist" title="Watchlist">
        <Icon name="bookmark" />
      </Link>
      <Link className="btn-icon cinepoint-chip" href="/shop/" aria-label="Cinepoint balansi" title="Cinepoint">
        <Icon name="coin" />
        <span>{user.profile.balance}</span>
      </Link>

      <div className={`user-menu${menuOpen ? " is-open" : ""}`}>
        <button
          className="avatar"
          type="button"
          aria-label="Foydalanuvchi menyusi"
          aria-expanded={menuOpen}
          aria-haspopup="true"
          onClick={() => setMenuOpen((v) => !v)}
        >
          {user.profile.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={mediaSrc(user.profile.avatar_url)} alt="" width={38} height={38} />
          ) : (
            user.initials
          )}
        </button>

        <div className="user-menu__panel" role="menu">
          <div className="user-menu__head">
            <div className="user-menu__name">{user.display_name}</div>
            <div className="user-menu__email">{user.email}</div>
          </div>

          <Link className="user-menu__item" href="/profile/" role="menuitem">
            <Icon name="user" /> Profil
          </Link>
          <Link className="user-menu__item" href="/watchlist/" role="menuitem">
            <Icon name="bookmark" /> Watchlist
          </Link>
          <Link className="user-menu__item" href="/favorites/" role="menuitem">
            <Icon name="heart" /> Favorites
          </Link>
          <Link className="user-menu__item" href="/shop/purchases/" role="menuitem">
            <Icon name="coin" /> Xaridlarim
          </Link>
          <Link className="user-menu__item" href="/obuna/mening/" role="menuitem">
            <Icon name="crown" /> Mening obunam
          </Link>
          {user.is_staff && (
            // Dashboard hali Django shablonlarida — to'g'ridan-to'g'ri backend'ga.
            <a className="user-menu__item" href="/dashboard/" role="menuitem">
              <Icon name="grid" /> Dashboard
            </a>
          )}
          <button
            className="user-menu__item user-menu__item--danger"
            type="button"
            role="menuitem"
            onClick={logout}
          >
            <Icon name="logout" /> Chiqish
          </button>
        </div>
      </div>

      <button
        className={`nav__burger${drawerOpen ? " is-open" : ""}`}
        type="button"
        aria-label="Menyu"
        aria-expanded={drawerOpen}
        onClick={() => setDrawerOpen((v) => !v)}
      >
        <span></span>
        <span></span>
        <span></span>
      </button>
      <div className={`drawer${drawerOpen ? " is-open" : ""}`}>
        <nav className="container" aria-label="Mobil menyu">
          <a className="drawer__link" href="/katalog/?type=movie">
            <Icon name="film" /> Kinolar
          </a>
          <a className="drawer__link" href="/katalog/?type=cartoon">
            <Icon name="sparkle" /> Multfilmlar
          </a>
          <a className="drawer__link" href="/katalog/?type=series">
            <Icon name="tv" /> Seriallar
          </a>
          <a className="drawer__link" href="/shop/">
            <Icon name="coin" /> Do&apos;kon
          </a>
          <Link className="drawer__link" href="/watchlist/">
            Watchlist
          </Link>
          <Link className="drawer__link" href="/favorites/">
            Favorites
          </Link>
          <Link className="drawer__link" href="/profile/">
            Profil
          </Link>
          <button className="btn btn--ghost btn--block" type="button" style={{ marginTop: "var(--s-5)" }} onClick={logout}>
            Chiqish
          </button>
        </nav>
      </div>
    </>
  );
}
