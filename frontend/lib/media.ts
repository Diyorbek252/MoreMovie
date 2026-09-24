/**
 * SSR paytida Django (`request.build_absolute_uri()` orqali) media
 * URL'larni SERVER ko'radigan ICHKI manzil bilan qaytaradi — masalan
 * `http://127.0.0.1:8000/media/backdrops/...`. Bu server ichida (Next
 * ↔ Django) to'g'ri, lekin BRAUZERGA yuborilsa, brauzer `127.0.0.1`ni
 * O'ZINING kompyuteri deb tushunadi va rasm hech qachon yuklanmaydi.
 *
 * `next/image` bu muammoni o'zi ko'rmaydi — uning optimallashtiruvchisi
 * rasmni SERVER tomonidan (Node jarayoni ichida) yuklab oladi, u yerda
 * 127.0.0.1 to'g'ri manzil. Muammo FAQAT brauzerda to'g'ridan-to'g'ri
 * ishlatiladigan oddiy `<img src>` teglarida — ular uchun shu funksiya
 * orqali ichki prefiks olib tashlanadi, qolgan nisbiy yo'lni esa
 * nginx/dev-proxy brauzerning o'zi orqali to'g'ri topadi.
 */
export function mediaSrc(url: string | null | undefined): string | undefined {
  if (!url) return undefined;
  return url.replace(/^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?/, "");
}
