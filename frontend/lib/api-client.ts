/**
 * Brauzer (client component) uchun API mijozi.
 *
 * Server tomonidagi `lib/api.ts` dan farqli — bu yerda `next/headers` yo'q,
 * shuning uchun har doim NISBIY manzilga (`/api/v1/...`) murojaat qilinadi.
 * Bu bitta domen arxitekturasi bilan ishlaydi: dev'da `next.config.ts`
 * rewrite orqali Django'ga proxy qilinadi, production'da esa nginx bir xil
 * domenda `/api/` ni Django'ga yo'naltiradi (CLAUDE.md, 0-bosqich) — shuning
 * uchun bu yerda CORS/cross-origin muammosi umuman yo'q.
 */

import type { ApiErrorPayload } from "./types";

export class ApiClientError extends Error {
  status: number;
  payload: ApiErrorPayload | null;

  constructor(status: number, payload: ApiErrorPayload | null) {
    super(
      (payload && (payload.detail as string)) ||
        (payload && typeof payload === "object" ? firstMessage(payload) : null) ||
        `So'rov bajarilmadi (${status}).`
    );
    this.status = status;
    this.payload = payload;
  }
}

function firstMessage(payload: ApiErrorPayload): string | null {
  for (const value of Object.values(payload)) {
    if (Array.isArray(value) && value.length) return value[0];
    if (typeof value === "string") return value;
  }
  return null;
}

/** `document.cookie` dan bitta qiymatni o'qiydi (masalan `csrftoken`). */
function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * CSRF cookie mavjudligiga ishonch hosil qiladi. Django `ensure_csrf_cookie`
 * shu so'rovda `csrftoken` cookie'sini o'rnatadi (agar hali bo'lmasa).
 */
export async function ensureCsrfCookie(): Promise<void> {
  if (readCookie("csrftoken")) return;
  await fetch("/api/v1/auth/csrf/", { credentials: "same-origin" });
}

type ClientFetchOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE" | "PUT";
  body?: unknown;
  /** `multipart/form-data` — fayl yuklashda (masalan to'lov cheki). */
  formData?: FormData;
};

/**
 * Asosiy brauzer fetch wrapper — CSRF header va cookie'larni avtomatik
 * qo'shadi. Xato holatida `ApiClientError` ko'taradi, forma componentlari
 * uni `catch` qilib maydon xatolarini ko'rsatadi (`error.payload`).
 */
export async function apiClientFetch<T>(path: string, options: ClientFetchOptions = {}): Promise<T> {
  const method = options.method || "GET";
  const isUnsafe = method !== "GET";

  const headers: Record<string, string> = {};
  if (isUnsafe) {
    // MUHIM (lokalda sinab ko'rilganda topilgan bug): `csrftoken` cookie
    // faqat `/auth/csrf/`, `/auth/login/` yoki `/auth/register/` sahifasi
    // ochilganda o'rnatilardi. Foydalanuvchi TO'G'RIDAN-TO'G'RI boshqa
    // sahifaga (masalan film detali) kelsa, cookie umuman yo'q edi —
    // Django "CSRF token missing" bilan 403 qaytarardi, bu esa (401/403
    // ni "avtorizatsiya yo'q" deb talqin qiluvchi tugmalarda) foydalanuvchi
    // ALLAQACHON kirgan bo'lsa ham qayta login sahifasiga otib yuborardi
    // (yoki logout so'rovi jimgina muvaffaqiyatsiz bo'lardi). Endi HAR bir
    // yozish so'rovidan oldin cookie borligi avtomatik ta'minlanadi.
    await ensureCsrfCookie();
    const csrftoken = readCookie("csrftoken");
    if (csrftoken) headers["X-CSRFToken"] = csrftoken;
  }
  if (options.body && !options.formData) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers,
    body: options.formData || (options.body ? JSON.stringify(options.body) : undefined),
  });

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    throw new ApiClientError(res.status, data);
  }
  return data as T;
}

export const apiGet = <T>(path: string) => apiClientFetch<T>(path);
export const apiPost = <T>(path: string, body?: unknown) =>
  apiClientFetch<T>(path, { method: "POST", body });
export const apiPatch = <T>(path: string, body?: unknown) =>
  apiClientFetch<T>(path, { method: "PATCH", body });
