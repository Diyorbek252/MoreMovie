import type { Metadata } from "next";
import { Inter, Poppins } from "next/font/google";

import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import RevealObserver from "@/components/RevealObserver";
import { getCurrentUser, getGenres, getSiteSettings } from "@/lib/api";
import { mediaSrc } from "@/lib/media";

import "./globals.css";

const inter = Inter({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-inter" });
const poppins = Poppins({ subsets: ["latin"], weight: ["600", "700", "800"], variable: "--font-poppins" });

export async function generateMetadata(): Promise<Metadata> {
  const siteSettings = await getSiteSettings();
  return {
    title: {
      default: `${siteSettings.seo_title || siteSettings.site_name} — Cheksiz kino zavqi...`,
      template: `%s — ${siteSettings.site_name}`,
    },
    description:
      siteSettings.seo_description ||
      `${siteSettings.site_name} — litsenziyalangan va public domain filmlarni onlayn tomosha qiling.`,
    keywords: siteSettings.seo_keywords || undefined,
    icons: siteSettings.favicon
      ? [{ url: mediaSrc(siteSettings.favicon)! }]
      : [{ url: "/img/favicon.svg", type: "image/svg+xml" }],
  };
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Uchalasi parallel — bittasi ikkinchisini kutmaydi (Navbar/Footer/
  // sahifaning o'zi bir vaqtda kerak bo'ladigan ma'lumot).
  const [siteSettings, user, genres] = await Promise.all([
    getSiteSettings(),
    getCurrentUser(),
    getGenres(),
  ]);

  return (
    <html lang="uz" className={`${inter.variable} ${poppins.variable}`}>
      <body>
        <a className="skip-link" href="#main">
          Asosiy qismga o&apos;tish
        </a>

        <Navbar siteSettings={siteSettings} user={user} />

        <main id="main">{children}</main>

        <Footer siteSettings={siteSettings} genres={genres} />

        <RevealObserver />

        {/* JS o'chirilgan yoki sekin yuklansa ham `.reveal` bo'limlari
            ko'rinib tursin — `RevealObserver` ishga tushmagan taqdirda ham
            kontent butunlay yo'qolib qolmaydi. */}
        <noscript>
          <style>{`.reveal { opacity: 1 !important; }`}</style>
        </noscript>
      </body>
    </html>
  );
}
