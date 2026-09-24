import Image from "next/image";
import Link from "next/link";

import type { Genre, SiteSettings } from "@/lib/types";
import Icon from "./Icon";

export default function Footer({
  siteSettings,
  genres,
}: {
  siteSettings: SiteSettings;
  genres: Genre[];
}) {
  const hasSocials =
    siteSettings.instagram || siteSettings.telegram || siteSettings.youtube || siteSettings.facebook;

  return (
    <footer className="footer">
      <div className="container">
        <div className="footer__grid">
          <div>
            <Link className="logo" href="/" aria-label={siteSettings.site_name}>
              {siteSettings.logo ? (
                <Image src={siteSettings.logo} alt={siteSettings.site_name} width={150} height={40} />
              ) : (
                <Image src="/img/logo.svg" alt={siteSettings.site_name} width={114} height={40} />
              )}
            </Link>
            <p className="footer__tagline">
              {siteSettings.site_description ||
                `${siteSettings.site_name} — litsenziyalangan va public domain filmlarni yuqori sifatda, qonuniy tarzda tomosha qiling.`}
            </p>

            {hasSocials && (
              <div className="socials">
                {siteSettings.instagram && (
                  <a className="social" href={siteSettings.instagram} target="_blank" rel="noopener noreferrer" aria-label="Instagram">
                    <Icon name="instagram" />
                  </a>
                )}
                {siteSettings.telegram && (
                  <a className="social" href={siteSettings.telegram} target="_blank" rel="noopener noreferrer" aria-label="Telegram">
                    <Icon name="telegram" />
                  </a>
                )}
                {siteSettings.youtube && (
                  <a className="social" href={siteSettings.youtube} target="_blank" rel="noopener noreferrer" aria-label="YouTube">
                    <Icon name="youtube" />
                  </a>
                )}
                {siteSettings.facebook && (
                  <a className="social" href={siteSettings.facebook} target="_blank" rel="noopener noreferrer" aria-label="Facebook">
                    <Icon name="facebook" />
                  </a>
                )}
              </div>
            )}
          </div>

          <div>
            <h4 className="footer__title">Sayt</h4>
            <ul className="footer__list">
              <li><Link href="/">Home</Link></li>
              <li><Link href="/katalog/?type=movie">Kinolar</Link></li>
              <li><Link href="/katalog/?type=cartoon">Multfilmlar</Link></li>
              <li><Link href="/katalog/?type=series">Seriallar</Link></li>
              <li><Link href="/katalog/">Butun katalog</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="footer__title">Janrlar</h4>
            <ul className="footer__list">
              {genres.slice(0, 5).map((genre) => (
                <li key={genre.id}>
                  <Link href={`/katalog/?genre=${genre.slug}`}>{genre.name}</Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="footer__title">Kompaniya</h4>
            <ul className="footer__list">
              <li><Link href="/about/">About</Link></li>
              <li><Link href="/contact/">Contact</Link></li>
              <li><Link href="/privacy/">Privacy Policy</Link></li>
              <li><Link href="/terms/">Terms</Link></li>
            </ul>
          </div>
        </div>

        <div className="footer__bottom">
          <p>{siteSettings.copyright_text || `© ${new Date().getFullYear()} ${siteSettings.site_name}. Barcha huquqlar himoyalangan.`}</p>
          <p className="footer__legal">
            Platformada faqat public domain, Creative Commons yoki huquq egasi ruxsat bergan kontent namoyish etiladi.
          </p>
        </div>
      </div>
    </footer>
  );
}
