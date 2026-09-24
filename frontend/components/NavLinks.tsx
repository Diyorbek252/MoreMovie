"use client";

/**
 * Navbar'dagi markaziy menyu — joriy sahifani `is-active` klassi bilan
 * belgilaydi (`templates/partials/navbar.html` dagi
 * `{% if request.resolver_match.url_name == 'home' %}is-active{% endif %}`
 * mantig'ining ekvivalenti).
 *
 * Kinolar/Multfilmlar/Seriallar uchchalasi ham BITTA katalogga olib
 * boradi, farqi faqat `?type=` da — shuning uchun faollik pathname
 * bilan birga query parametriga ham qaraydi.
 */

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import Icon from "./Icon";

const CATALOG_LINKS = [
  { type: "movie", label: "Kinolar", icon: "film" },
  { type: "cartoon", label: "Multfilmlar", icon: "sparkle" },
  { type: "series", label: "Seriallar", icon: "tv" },
];

export default function NavLinks() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentType = searchParams.get("type");

  const isCatalog = pathname === "/katalog" || pathname === "/katalog/";
  const isHome = pathname === "/";
  const isShop = pathname?.startsWith("/shop");

  return (
    <nav className="nav__menu" aria-label="Asosiy menyu">
      <Link className={`nav__link${isHome ? " is-active" : ""}`} href="/">
        <Icon name="home" /> Bosh sahifa
      </Link>

      {CATALOG_LINKS.map((item) => (
        <Link
          key={item.type}
          className={`nav__link${isCatalog && currentType === item.type ? " is-active" : ""}`}
          href={`/katalog/?type=${item.type}`}
        >
          <Icon name={item.icon} /> {item.label}
        </Link>
      ))}

      <Link className={`nav__link${isShop ? " is-active" : ""}`} href="/shop/">
        <Icon name="coin" /> Do&apos;kon
      </Link>
    </nav>
  );
}
