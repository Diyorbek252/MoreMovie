# MORE-MOVIE — Frontend (Next.js)

Django DRF API (`/api/v1/...`) uchun Next.js 15 (App Router, TypeScript)
frontend. Dizayn sistemasi `../static/css/` dan to'g'ridan-to'g'ri
ko'chirilgan (`styles/`), backend qoidalari `CLAUDE.md` da.

> ⚠️ **Bu kod bu muhitda hech qachon `npm install`/`npm run build` bilan
> ishga tushirilmagan** — mashinada Node.js o'rnatilmagan edi. Kod
> Next.js 15 App Router konvensiyalariga qat'iy amal qiladi va tur
> ta'riflari (`lib/types.ts`) backend serializerlaridan qo'lda, aniq
> tekshirilgan javoblarga qarab yozilgan — ammo hech qachon
> kompilyatsiya/type-check qilinmagan. Birinchi ishga tushirishda
> quyidagi tekshiruv ro'yxatini bajaring.

## O'rnatish

```powershell
# 1. Node.js 20+ o'rnating (https://nodejs.org), keyin:
cd frontend
npm install
cp .env.local.example .env.local
```

`.env.local` dagi `BACKEND_INTERNAL_URL` Django serveringiz manziliga mos
kelishi kerak (dev'da odatda `http://127.0.0.1:8000`).

## Ishga tushirish (dev)

Ikkala server BIRGA kerak:

```powershell
# Terminal 1 — Django (loyiha ildizidan)
.\.venv\Scripts\python.exe manage.py runserver

# Terminal 2 — Next.js (frontend/ papkasidan)
npm run dev
```

`http://localhost:3000` ni oching. `/api/*` va `/media/*` so'rovlari
`next.config.ts` dagi rewrite orqali avtomatik Django'ga proxy qilinadi.

## Birinchi ishga tushirishda tekshiring

1. `npm run build` — TypeScript xatolari, import xatolari shu yerda
   chiqadi (men hech qachon ishga tushira olmadim, shuning uchun bu ENG
   MUHIM qadam). Xato chiqsa, ko'pincha import yo'li yoki JSX sintaksisi
   bilan bog'liq bo'ladi — fayl nomi va qatorga qarab tuzatish oson.
2. `npm run lint` — Next.js standart ESLint qoidalari (`<img>` o'rniga
   `next/image`, hook qoidalari va h.k.). Men ba'zi joyларда ataylab
   oddiy `<img>` qoldirdim (masalan hero fon rasmi) — lint ogohlantirsa,
   `eslint-disable-next-line` izohi allaqachon qo'yilgan.
3. Bosh sahifa (`/`) — hero, "Davom ettirish" (tizimga kirib, bironta
   filmni ko'rgandan keyin), Premyeralar/Kinolar/Multfilmlar/Seriallar/
   Janrlar/Yillar bo'limlari to'g'ri ko'rinishi kerak.
4. `/katalog/?type=movie` — filtr (janr chiplari), saralash, sahifalash.
5. `/movie/<slug>/` — public-domain, premium va (agar test ma'lumotida
   bo'lsa) trailer_only filmlarni sinab ko'ring: video faqat `can_play`
   bo'lganda ko'rinishi SHART (bu loyihaning huquqiy asosi — CLAUDE.md).
6. `/register/` → `/login/` → navbar o'ng tomonida avatar/balans
   ko'rinishi, `/watchlist/`, `/favorites/` bo'sh ro'yxat ko'rsatishi.
7. Filmni watchlist/favoritega qo'shish, reyting va sharh yuborish.

## Nima tayyor, nima yo'q

**Tayyor**: bosh sahifa, katalog (filtr/sort/pagination), film detali
(pleer, litsenziya bildirishnomasi, reyting/sharh, cast/rejissyor,
kadrlar, o'xshash filmlar), login/register, watchlist, favorites, navbar/
footer (sayt sozlamalari, janrlar).

**Hali yo'q** (keyingi bosqich): serial detali sahifasi (`/series/<slug>/`
— backend API tayyor, sahifa yozilmagan), profil va profil tahriri,
do'kon (`/shop/`), obuna (`/obuna/`), about/contact/privacy/terms statik
sahifalari, director/actor/category/genre detail sahifalari, alohida
qidiruv sahifasi (hozircha `/katalog/?q=`ga yo'naltiradi), bildirishnoma
qo'ng'irog'i (backend endpoint bor, UI yo'q), toast xabar tizimi.

**Ataylab soddalashtirilgan**: video pleer brauzerning native
`<video controls>` elementidan foydalanadi (Django'dagi to'liq maxsus
UI — progress bar, sifat/tezlik menyusi — o'rniga); premyera bo'limi
maxsus "stage" karuselisiz oddiy qator sifatida chiqadi; qidiruv
"yozayotganda natija" ko'rsatmaydi, faqat forma yuborilganda ishlaydi.
