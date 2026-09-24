/**
 * Server-side (Server Component / Route Handler) API mijozi.
 *
 * Faqat serverda ishlaydi — brauzer komponentlari uchun `lib/api-client.ts`
 * ga qarang. Ikkita muhim narsani ta'minlaydi:
 *
 * 1. Kiruvchi so'rovning `Cookie` header'ini Django'ga UZATADI — shu
 *    bilan SSR sahifalar (masalan `/watchlist`) joriy foydalanuvchining
 *    sessiyasini ko'radi.
 * 2. `X-Forwarded-Proto` header'ini qo'shadi — production'da
 *    `DEBUG=False` bo'lganda Django'ning `SECURE_SSL_REDIRECT` sozlamasi
 *    ICHKI (http://127.0.0.1:8000) SSR so'rovini ham HTTPS'ga 301 qilib
 *    yubormasligi uchun (`config/settings.py:SECURE_PROXY_SSL_HEADER`
 *    aynan shu header'ni kutadi). Bu CLAUDE.md rejasidagi 2-tuzoq.
 *
 * MUHIM (serverda sinab ko'rilgan): `Host` header'ini BU YERDA
 * o'rnatib bo'lmaydi — fetch spetsifikatsiyasida u "taqiqlangan header",
 * Node/undici uni jimgina olib tashlaydi va Django baribir URL'dagi
 * hostni (`127.0.0.1:8000`) ko'radi. Shuning uchun serverning `.env`
 * faylidagi `ALLOWED_HOSTS` ro'yxatiga ichki manzil ham qo'shilishi
 * kerak, masalan: `ALLOWED_HOSTS=more-movie.uz,127.0.0.1`.
 */

import { cookies, headers } from "next/headers";

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";
const SITE_PROTO = process.env.SITE_PROTO || "http";
const SITE_HOST = process.env.SITE_HOST || "localhost:3000";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(status: number, payload: unknown, message?: string) {
    super(message || `API xatosi: ${status}`);
    this.status = status;
    this.payload = payload;
  }
}

type FetchOptions = {
  /** Next.js ma'lumot keshi — bosh sahifa/katalog kabi ommaviy ro'yxatlar uchun. */
  revalidate?: number | false;
  /** GET dan boshqa metod (POST/PATCH) kamdan-kam serverda kerak bo'ladi. */
  method?: string;
  body?: unknown;
};

/**
 * Django API'ga serverdan so'rov yuboradi. Har doim joriy so'rovning
 * cookie'sini uzatadi — anonim sahifalarda buning zarari yo'q (bo'sh
 * cookie), autentifikatsiya talab qiladigan sahifalarda esa shart.
 */
export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();

  // MUHIM: `next: { revalidate: false }` Next.js'da "HECH QACHON eskirmaydi"
  // (cheksiz kesh) degani — "keshlanmasin" degani EMAS! Bu ikkalasini
  // aralashtirib, avval `getWatchlist`/`getFavorites`/`getMe` kabi shaxsiy
  // ma'lumotlar CHEKSIZ keshlanib qolgan edi (production'da sinab
  // ko'rilganda topildi: Favorites'dan o'chirilgan film ro'yxatda qolib
  // ketardi). To'g'ri yechim — `cache: "no-store"`, umuman keshlanmasin.
  const isMutation = Boolean(options.method) && options.method !== "GET";
  const cacheOptions: RequestInit =
    isMutation || options.revalidate === false
      ? { cache: "no-store" }
      : { next: { revalidate: options.revalidate ?? 60 } };

  const res = await fetch(`${BACKEND_URL}${path}`, {
    method: options.method || "GET",
    headers: {
      Cookie: cookieHeader,
      "X-Forwarded-Proto": SITE_PROTO,
      ...(options.body ? { "Content-Type": "application/json" } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
    ...cacheOptions,
  });

  if (!res.ok) {
    let payload: unknown = null;
    try {
      payload = await res.json();
    } catch {
      // javob JSON emas — masalan xom HTML xato sahifasi.
    }
    throw new ApiError(res.status, payload);
  }

  // 204 No Content kabi bo'sh javoblar.
  const text = await res.text();
  return (text ? JSON.parse(text) : null) as T;
}

/** Joriy so'rovning `Host`/protokolini olib, mutlaq URL yasash uchun (SEO: canonical, OG). */
export async function getRequestOrigin(): Promise<string> {
  const hdrs = await headers();
  const host = hdrs.get("host") || SITE_HOST;
  const proto = hdrs.get("x-forwarded-proto") || SITE_PROTO;
  return `${proto}://${host}`;
}

// ---------------------------------------------------------------------------
// Tur bo'yicha xavfsiz wrapperlar — har bir DRF endpoint uchun bittadan.
// ---------------------------------------------------------------------------

import type {
  CatalogResponse,
  Genre,
  HomeResponse,
  MovieDetail,
  Notification,
  Order,
  Paginated,
  Plan,
  Product,
  Review,
  SeriesDetail,
  SiteSettings,
  Subscription,
  User,
} from "./types";

/* ---------------------------------------------------------------------------
   KESHLASH QOIDASI (buzilmaydi)

   Next.js Data Cache so'rovni URL bo'yicha kalitlaydi — `Cookie` header'ga
   QARAMAYDI. Shuning uchun javobida FOYDALANUVCHIGA XOS maydon bo'lgan
   har qanday endpoint `revalidate: false` (= `cache: "no-store"`) bilan
   olinishi SHART. Aks holda bir foydalanuvchining javobi boshqasiga
   berilishi mumkin:

     - `in_watchlist` / `in_favorite`  → chalkash tugma holati
     - `can_play` / `video_sources`    → PREMIUM kontent obunasiz odamga
                                          ochilib qolishi (CLAUDE.md dagi
                                          huquqiy qoidaning buzilishi)
     - `resume_at` / `user_rating`     → boshqa odamning ko'rish tarixi

   Faqat hammaga bir xil (`site/settings/`, `genres/`) javoblar
   keshlanadi.
   --------------------------------------------------------------------------- */

export const getHome = () => apiFetch<HomeResponse>("/api/v1/home/", { revalidate: false });

export function getCatalog(searchParams: Record<string, string | string[] | undefined>) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(searchParams)) {
    if (value === undefined) continue;
    params.set(key, Array.isArray(value) ? value.join(",") : value);
  }
  const qs = params.toString();
  return apiFetch<CatalogResponse>(`/api/v1/catalog/${qs ? `?${qs}` : ""}`, { revalidate: false });
}

export const getMovie = (slug: string) =>
  apiFetch<MovieDetail>(`/api/v1/movies/${slug}/`, { revalidate: false });

export const getSeries = (slug: string) =>
  apiFetch<SeriesDetail>(`/api/v1/series/${slug}/`, { revalidate: false });

export function getReviews(target: { movie: string } | { series: string }) {
  // TS eslatmasi: ikkala tomoni ham OPTIONAL bo'lgan union'da `in` orqali
  // ajratib bo'lmaydi (bo'sh obyekt ikkalasiga ham strukturaviy mos keladi) —
  // shuning uchun maydonlar shu yerda MAJBURIY, chaqiruvchi ANIQ bittasini beradi.
  const params = "movie" in target ? `movie=${target.movie}` : `series=${target.series}`;
  return apiFetch<Paginated<Review>>(`/api/v1/reviews/?${params}`, { revalidate: 30 });
}

export const getSiteSettings = () =>
  apiFetch<SiteSettings>("/api/v1/site/settings/", { revalidate: 300 });

export const getMe = () => apiFetch<User>("/api/v1/auth/me/", { revalidate: false });

/** `getMe()` ning "xatosiz" varianti — anonim foydalanuvchi uchun 401'ni
 * ushlab, `null` qaytaradi. Navbar/layout kabi HAR sahifada chaqiriladigan
 * joylarda ishlatiladi — u yerda 401 kutilgan holat, xato emas. */
export async function getCurrentUser(): Promise<User | null> {
  try {
    return await getMe();
  } catch (err) {
    if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
      return null;
    }
    throw err;
  }
}

export const getGenres = () => apiFetch<Genre[]>("/api/v1/genres/", { revalidate: 300 });

export const getWatchlist = () =>
  apiFetch<Paginated<MovieDetail>>("/api/v1/me/watchlist/", { revalidate: false });

export const getFavorites = () =>
  apiFetch<Paginated<MovieDetail>>("/api/v1/me/favorites/", { revalidate: false });

export const getNotifications = () =>
  apiFetch<{ results: Notification[]; unread_count: number }>("/api/v1/me/notifications/", {
    revalidate: false,
  });

export const getPlans = () => apiFetch<Paginated<Plan>>("/api/v1/subscriptions/plans/", { revalidate: 300 });

export const getMySubscriptions = () =>
  apiFetch<Paginated<Subscription>>("/api/v1/subscriptions/me/", { revalidate: false });

export const getProducts = (searchParams: Record<string, string | undefined>) => {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(searchParams)) {
    if (value) params.set(key, value);
  }
  const qs = params.toString();
  // `?affordable=1` foydalanuvchi balansiga qarab filtrlaydi — ya'ni bu
  // javob ham foydalanuvchiga xos, keshlanmaydi.
  return apiFetch<Paginated<Product>>(`/api/v1/shop/products/${qs ? `?${qs}` : ""}`, {
    revalidate: false,
  });
};

export const getOrders = () => apiFetch<Paginated<Order>>("/api/v1/shop/orders/", { revalidate: false });
