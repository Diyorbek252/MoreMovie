import Image from "next/image";
import Link from "next/link";

import type { SiteSettings, User } from "@/lib/types";
import Icon from "./Icon";
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

        <nav className="nav__menu" aria-label="Asosiy menyu">
          <Link className="nav__link" href="/">
            <Icon name="home" /> Bosh sahifa
          </Link>
          <Link className="nav__link" href="/katalog/?type=movie">
            <Icon name="film" /> Kinolar
          </Link>
          <Link className="nav__link" href="/katalog/?type=cartoon">
            <Icon name="sparkle" /> Multfilmlar
          </Link>
          <Link className="nav__link" href="/katalog/?type=series">
            <Icon name="tv" /> Seriallar
          </Link>
          <Link className="nav__link" href="/shop/">
            <Icon name="coin" /> Do&apos;kon
          </Link>
        </nav>

        <div className="nav__actions">
          <NavSearch />
          <NavUserMenu user={user} />
        </div>
      </div>
    </header>
  );
}
