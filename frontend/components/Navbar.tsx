import Image from "next/image";
import Link from "next/link";
import { Suspense } from "react";

import type { SiteSettings, User } from "@/lib/types";
import NavLinks from "./NavLinks";
import NavSearch from "./NavSearch";
import NavUserMenu from "./NavUserMenu";

export default function Navbar({
  siteSettings,
  user,
}: {
  siteSettings: SiteSettings;
  user: User | null;
}) {
  return (
    <header className="nav" id="navbar">
      <div className="container nav__inner">
        <Link className="logo" href="/" aria-label={`${siteSettings.site_name} — bosh sahifa`}>
          {siteSettings.logo ? (
            <Image src={siteSettings.logo} alt={siteSettings.site_name} width={140} height={38} />
          ) : (
            <Image src="/img/logo.svg" alt={siteSettings.site_name} width={108} height={38} />
          )}
        </Link>

        <Suspense fallback={<nav className="nav__menu" aria-label="Asosiy menyu" />}>
          <NavLinks />
        </Suspense>

        <div className="nav__actions">
          <NavSearch />
          <NavUserMenu user={user} />
        </div>
      </div>
    </header>
  );
}
