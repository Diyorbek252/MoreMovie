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
    return [
      // Brauzer client komponentlari doim NISBIY `/api/v1/...` manziliga
      // murojaat qiladi (bir xil origin — production'dagi kabi). Dev
      // rejimida Next shu so'rovlarni Django'ga proxy qiladi, shu bilan
      // localhost:3000 va 127.0.0.1:8000 orasidagi CORS/cookie muammosi
      // butunlay yo'qoladi (loyihada CORS sozlamasi yo'q — bu ataylab).
      { source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` },
      // Rasm/video fayllar — poster, backdrop, avatar, yuklangan video.
      { source: "/media/:path*", destination: `${BACKEND_URL}/media/:path*` },
    ];
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
