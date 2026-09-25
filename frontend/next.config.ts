import type { NextConfig } from "next";

// Django backend'ning ICHKI manzili — server komponentlari (SSR) va dev
// rejimidagi proxy shu yerga murojaat qiladi. Production'da nginx
// `/api/`, `/media/`, `/static/` ni to'g'ridan-to'g'ri Django'ga
// yo'naltiradi (bu rewrite faqat DEV uchun kerak — production build'da
// ham zarar keltirmaydi, chunki nginx baribir bu qatlamgacha yetib
// kelmaydi: static build fayllar Next serveridan emas, gunicorn/nginx'dan
// olinadi. MORE_MOVIES/CLAUDE.md rejasi: 0-bosqich).
const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Barcha URL'lar oxirida "/" bilan — Django'dagi (APPEND_SLASH) bilan
  // AYNAN bir xil manzillar saqlanadi: /katalog/, /movie/<slug>/ va h.k.
  // Bu SEO uchun muhim (sitemap.xml allaqachon shu manzillarni beradi) va
  // ichki havolalar ortiqcha 308-yo'naltirishsiz to'g'ridan-to'g'ri ochiladi.
  trailingSlash: true,

  async rewrites() {
    // MUHIM (lokalda sinab ko'rilganda topilgan cheksiz-redirect bug'i):
    // `trailingSlash: true` bilan Next.js so'ralgan URL'ni oxiridagi "/"
    // bilan KUTADI, lekin `:path*` catch-all segmenti proxy destination
    // yasaganda o'sha "/" ni SAQLAMAYDI. Natijada `/api/v1/auth/csrf/`
    // Django'ga SLASHSIZ (`/api/v1/auth/csrf`) boradi, Django
    // (APPEND_SLASH) buni qaytadan slashli manzilga 301 qiladi, brauzer
    // yana `/api/v1/auth/csrf/` ga qaytadi — CHEKSIZ HALQA
    // (ERR_TOO_MANY_REDIRECTS). Yechim: slash bilan va slashsiz
    // so'rovlarni ALOHIDA qoida sifatida yozib, ikkalasida ham destination
    // aynan so'ralganidek "/" bilan tugashini ta'minlaymiz.
    return {
      // Har doim Django'ga — Next'da bunday sahifa bo'lishidan qat'i nazar.
      beforeFiles: [
        { source: "/api/:path*/", destination: `${BACKEND_URL}/api/:path*/` },
        { source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` },
        // Rasm/video fayllar — poster, backdrop, avatar, yuklangan video.
        { source: "/media/:path*", destination: `${BACKEND_URL}/media/:path*` },
      ],
      afterFiles: [],
      // Next'da SAHIFASI YO'Q har qanday yo'l Django'ga (dashboard, admin,
      // do'kon, obuna, profil va h.k. — hali Next'ga ko'chirilmagan
      // sahifalar). Bu production'dagi nginx aralash marshrutining lokal
      // ekvivalenti: u yerda nginx aynan shu yo'llarni gunicorn'ga beradi.
      // Next'ning o'z sahifalari (/, /katalog/, /movie/..., /series/...)
      // bunga tushmaydi — `fallback` faqat mos sahifa topilmaganda ishlaydi.
      fallback: [
        { source: "/:path*/", destination: `${BACKEND_URL}/:path*/` },
        { source: "/:path*", destination: `${BACKEND_URL}/:path*` },
      ],
    };
  },
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "127.0.0.1", port: "8000", pathname: "/media/**" },
      { protocol: "http", hostname: "localhost", port: "3000", pathname: "/media/**" },
      // TODO(production): haqiqiy domenni qo'shing, masalan:
      // { protocol: "https", hostname: "more-movie.uz", pathname: "/media/**" },
    ],
  },
};

export default nextConfig;
