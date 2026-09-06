# MORE-MOVIE

> **Cheksiz kino zavqi...**

Django asosidagi zamonaviy kino platformasi. Qora + qizil cinematic dizayn,
to'liq responsive interfeys, custom video player, watchlist/favorites,
reyting va sharh tizimi hamda professional boshqaruv paneli.

**Stek:** Python 3.14 · Django 6.1 · SQLite (dev) / PostgreSQL (prod) · Pillow · WhiteNoise
**Frontend:** custom CSS design system (Bootstrap ishlatilmagan) · vanilla JavaScript

---

## ⚖️ Huquqiy qoida

Platforma **faqat qonuniy tarqatiladigan kontent** uchun mo'ljallangan.
Pirat film, noqonuniy streaming yoki mualliflik huquqini buzuvchi yuklab olish
tizimi bu loyihada **yo'q va bo'lmaydi**.

Buni model darajasida `Movie.license_type` maydoni ta'minlaydi:

| Litsenziya | Ko'rish | Yuklab olish |
|---|:---:|:---:|
| `public_domain` — Public domain / Creative Commons | ✅ | ✅ (admin ruxsati bilan) |
| `licensed` — huquq egasi ruxsat bergan | ✅ | ✅ (admin ruxsati bilan) |
| `trailer_only` — faqat rasmiy treyler | ❌ | ❌ |

- `Movie.can_watch` — litsenziya mos **va** video manbasi mavjud bo'lsagina `True`.
- `Movie.can_download` — yuqoridagilarga qo'shimcha `is_download_allowed` **va** havola kerak.
- Watch sahifasi bu shartni buzgan so'rovga `403` qaytaradi.
- Test ma'lumot sifatida faqat **Blender Foundation** ochiq filmlari (CC BY) ishlatiladi.

---

## 🚀 Ishga tushirish

### 1. Virtual muhit va paketlar

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Muhit sozlamalari

```powershell
copy .env.example .env
```

`.env` ichidagi `SECRET_KEY` ni o'zingiznikiga almashtiring:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

### 3. Baza va test ma'lumot

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_movies
.\.venv\Scripts\python.exe manage.py createsuperuser
```

`seed_movies` 10 ta janr, 12 ta public-domain film va ular uchun
posterlarni (Pillow bilan, internetsiz) yaratadi.
Qaytadan tozalab yaratish: `manage.py seed_movies --reset`

### 4. Serverni ishga tushirish

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

→ <http://127.0.0.1:8000/>

---

## 📁 Struktura

```
More_Movies/
├── config/          # settings (.env), urls, wsgi/asgi
├── core/            # home, about, contact, huquqiy sahifalar, sitemap
├── users/           # User(AbstractUser), Profile, auth, middleware
├── movies/          # Movie, Genre, Person, Watchlist, Favorite, ViewHistory
├── reviews/         # Rating (1-5), Review (moderatsiya bilan)
├── dashboard/       # staff-only boshqaruv paneli
├── templates/       # loyiha darajasidagi shablonlar
├── static/          # css/, js/, img/
├── media/           # yuklangan fayllar (git'da yo'q)
└── scripts/         # brend rasmlarini yaratuvchi yordamchi skript
```

---

## 🎨 Brend va logo

| Fayl | Vazifasi |
|---|---|
| `static/img/logo.svg` | Navbar, footer, loading ekrani, xato sahifalari |
| `static/img/favicon.svg` | Brauzer tab ikonkasi |
| `static/img/logo-full.png` | Login/register sahifasining fon paneli |
| `static/img/logo-share.png` | Open Graph ulashish rasmi |

`logo-full.png` va `logo-share.png` — **placeholder**. O'zingizning logo
rasmingizni shu nomlar bilan `static/img/` ga saqlasangiz, kod o'zgarmaydi.
Placeholder'larni qayta yaratish:

```powershell
.\.venv\Scripts\python.exe scripts\make_brand_images.py
```

### Rang palitrasi

Barcha ranglar `static/css/variables.css` da CSS o'zgaruvchilari sifatida.
Shablonga hardcoded hex rang yozilmaydi.

```
Fon:     #000000  #0B0B0B  #121212  #1A1A1A
Accent:  #E50914  #FF2A00  #FF0000
Matn:    #FFFFFF  #B3B3B3
```

---

## 🔗 URL lar

| Yo'l | Sahifa |
|---|---|
| `/` | Bosh sahifa (hero + karusellar) |
| `/movies/` | Katalog — filtr, saralash, sahifalash |
| `/movie/<slug>/` | Film sahifasi |
| `/watch/<slug>/` | Video player (login + litsenziya talab qiladi) |
| `/genres/`, `/genre/<slug>/` | Janrlar |
| `/search/?q=` | Qidiruv natijalari |
| `/login/`, `/register/`, `/logout/` | Autentifikatsiya |
| `/password-reset/` | Parolni tiklash |
| `/profile/`, `/profile/edit/` | Profil |
| `/watchlist/`, `/favorites/` | Foydalanuvchi to'plamlari |
| `/dashboard/` | Boshqaruv paneli (staff-only) |
| `/admin/` | Django admin |
| `/sitemap.xml`, `/robots.txt` | SEO |

### AJAX endpointlar

Barchasi `POST` + `login_required` + CSRF (`X-CSRFToken` header):

```
POST /api/watchlist/toggle/   {"movie": id}
POST /api/favorite/toggle/    {"movie": id}
POST /api/progress/           {"movie": id, "seconds": n, "finished": bool}
POST /api/rate/               {"movie": id, "score": 1..5}
POST /api/review/             {"movie": id, "comment": "..."}
GET  /api/search/?q=          (ochiq, jonli qidiruv)
```

---

## 🎬 Video player

Custom HTML5 player (`static/js/player.js`), tashqi kutubxonasiz:

- Play/pause, progress bar (bosib va sudrab seek), ovoz, to'liq ekran
- Boshqaruv paneli 2.6 soniyadan keyin avtomatik yashirinadi
- Ko'rish pozitsiyasi har 15 soniyada `ViewHistory` ga yoziladi → **davom ettirish**
- Sahifadan chiqishda `sendBeacon` bilan oxirgi holat yuboriladi

**Klaviatura:** `Space`/`K` — play/pause · `←`/`→` — 10s · `↑`/`↓` — ovoz · `M` — mute · `F` — fullscreen

Saytda: `/` — qidiruvni ochish · `Esc` — panellarni yopish

---

## 🛡 Xavfsizlik

- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL` faqat `.env` da
- Barcha formalarda CSRF tokeni; AJAX'da `X-CSRFToken` header
- Parollar Django hasher orqali; login username **yoki** email bilan
- `BlockedUserMiddleware` — bloklangan foydalanuvchi joriy sessiyadan chiqariladi
- Dashboard `StaffRequiredMixin` bilan himoyalangan
- Saralash parametri lug'atdan tekshiriladi — `order_by()` ga bevosita uzatilmaydi
- `DEBUG=False` bo'lganda HSTS, SSL redirect va secure cookie'lar avtomatik yoqiladi

---

## ⚡ Performance

- `Movie.objects.published().with_relations()` — `select_related` + `prefetch_related`
- Bosh sahifa bo'limlari 5 daqiqaga keshlanadi (LocMem)
- `avg_rating` / `rating_count` denormalizatsiya qilingan — detail sahifada `AVG()` yo'q
- Watchlist/Favorite holati bir marta `set` sifatida olinadi (context processor)
- Barcha rasmlarda `loading="lazy"` va aniq `width`/`height`
- `Meta.indexes` — chop etish holati, ko'rishlar, reyting va yil bo'yicha

---

## 🚢 Production'ga chiqarish

### 1. Muhit

```env
DEBUG=False
SECRET_KEY=<yangi-tasodifiy-kalit>
ALLOWED_HOSTS=more-movie.uz,www.more-movie.uz
CSRF_TRUSTED_ORIGINS=https://more-movie.uz
DATABASE_URL=postgres://user:parol@host:5432/moremovie
EMAIL_HOST=smtp.provayder.uz
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

`DATABASE_URL` to'ldirilishi bilan loyiha PostgreSQL ga o'tadi — **kod o'zgarmaydi**.
PostgreSQL uchun qo'shimcha: `pip install psycopg[binary]`

### 2. Tayyorlash

```powershell
$env:DEBUG="False"
.\.venv\Scripts\python.exe manage.py check --deploy
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

> ⚠️ `collectstatic` ni **`DEBUG=False`** bilan ishga tushiring — hashlangan
> manifest faqat shunda yaratiladi.

### 3. Ishga tushirish

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

Statik fayllarni WhiteNoise xizmat qiladi (nginx shart emas).
Media fayllar uchun nginx yoki S3 tavsiya etiladi.

### Deploy oldidan tekshiruv ro'yxati

- [ ] `.env` yaratilgan, `SECRET_KEY` yangi va maxfiy
- [ ] `DEBUG=False`, `ALLOWED_HOSTS` to'g'ri
- [ ] `manage.py check --deploy` toza chiqadi
- [ ] `collectstatic` `DEBUG=False` bilan bajarilgan
- [ ] Baza migratsiyalari qo'llangan
- [ ] HTTPS sertifikati o'rnatilgan
- [ ] `media/` uchun zaxira nusxa sozlangan

---

## 🧪 Tekshirish

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Qo'lda tekshiriladigan yo'l:
`/` → `/movies/` (filtr + saralash) → `/movie/<slug>/` → `/register/` →
`/watch/<slug>/` → watchlist/favorite/rating/review → `/profile/` →
`/dashboard/` → mavjud bo'lmagan URL (404)

Responsive: brauzer devtools'da **375px**, **768px**, **1440px**.

---

## 📄 Litsenziya

Loyiha kodi o'quv maqsadida yaratilgan.
Namunadagi filmlar — Blender Foundation ochiq loyihalari,
Creative Commons Attribution litsenziyasi ostida.

© 2026 MORE-MOVIE
