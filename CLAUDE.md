# CLAUDE.md

Bu fayl Claude Code (claude.ai/code) uchun loyiha bo'yicha yo'riqnoma.

## Loyiha

**MORE-MOVIE** — "Cheksiz kino zavqi..." — Django asosidagi kino platformasi.
Qora + qizil cinematic dizayn, custom CSS design system (Bootstrap ishlatilmaydi).

Stek: **Python 3.14 · Django 6.1 · SQLite (dev) · Pillow · python-dotenv · whitenoise**

## HUQUQIY QOIDA (buzilmaydi)

Platforma **faqat qonuniy kontent** uchun. Pirat film, noqonuniy streaming yoki
mualliflik huquqini buzuvchi yuklab olish tizimi **hech qachon qo'shilmaydi**.

Buni kod darajasida `Movie.license_type` ta'minlaydi:

| Qiymat | Ma'nosi | Ko'rish | Yuklash |
|---|---|---|---|
| `public_domain` | Public domain / Creative Commons | ✅ | ✅ (ruxsat bilan) |
| `licensed` | Huquq egasi ruxsat bergan | ✅ | ✅ (ruxsat bilan) |
| `trailer_only` | Faqat rasmiy treyler | ❌ | ❌ |

- `Movie.can_watch` — litsenziya mos **va** video manbasi bor bo'lsagina `True`.
- `Movie.can_download` — litsenziya mos **va** `is_download_allowed=True` **va**
  `download_url` bo'lsagina `True`.
- Shablon va view'larda video/download tugmasi **doim** shu xossalar orqali tekshiriladi,
  hech qachon to'g'ridan-to'g'ri `video_url` bo'yicha emas.
- Seed ma'lumot faqat Blender Foundation ochiq filmlari (CC BY).

## Komandalar

Windows PowerShell, loyiha ildizidan:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_movies          # test ma'lumot
.\.venv\Scripts\python.exe manage.py seed_movies --reset   # tozalab qayta yaratish
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py check --deploy
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

Test superuser: `admin` / `MoreMovie2026!`

## Arxitektura

```
config/     — settings (.env orqali), urls, wsgi/asgi
core/       — home, about, contact, ContactMessage, context_processors
users/      — User(AbstractUser), Profile, EmailOrUsernameBackend, BlockedUserMiddleware
movies/     — Genre, Country, Language, Person, Movie, MovieCast, Screenshot,
              Watchlist, Favorite, ViewHistory
reviews/    — Rating (1-5), Review (moderatsiya bilan)
dashboard/  — staff-only custom boshqaruv paneli (o'z modeli yo'q)
templates/  — loyiha darajasida (app ichida emas)
static/     — css/, js/, img/
media/      — yuklangan fayllar (git'da yo'q)
```

## Muhim konvensiyalar

**Sozlamalar** — `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL` faqat `.env` dan
o'qiladi. `.env` hech qachon commit qilinmaydi. `DATABASE_URL` bo'sh bo'lsa SQLite,
to'ldirilsa PostgreSQL — kod o'zgarmaydi.

**Custom User** — `AUTH_USER_MODEL = "users.User"`. Kodda hech qachon
`django.contrib.auth.models.User` import qilinmaydi; `settings.AUTH_USER_MODEL`
yoki `get_user_model()` ishlatiladi.

**Query optimizatsiyasi** — film ro'yxatlari doim `Movie.objects.published().with_relations()`
orqali olinadi (`MovieQuerySet` da). Yangi ro'yxat view yozganda shuni ishlating,
aks holda har kartada N+1 so'rov paydo bo'ladi.

**Reyting denormalizatsiyasi** — `Movie.avg_rating` va `rating_count` ustunlari
`Rating.save()/delete()` dan `Movie.recalculate_rating()` orqali yangilanadi.
Ularni qo'lda o'zgartirmang; detail sahifada `AVG()` hisoblamang.

**Slug** — barcha modellarda `unique_slugify()` (`movies/models.py`) avtomatik
takrorlanmas slug beradi. `save()` da qo'lda slug yozish shart emas.

**Kartalar** — filmni ko'rsatuvchi yagona shablon `templates/partials/movie_card.html`.
Yangi kartochka varianti yozmang, shuni `include` qiling.

**Watchlist/Favorite holati** — `core.context_processors.site_globals`
`user_watchlist_ids` va `user_favorite_ids` to'plamlarini beradi. Kartada tugma
holatini shu to'plamlar orqali tekshiring, har karta uchun alohida so'rov qilmang.

**CSS** — ranglar va o'lchamlar faqat `static/css/variables.css` dagi CSS
o'zgaruvchilari orqali. Shablonga hardcoded hex rang yozilmaydi.

**Til** — UI matnlari va kod izohlari o'zbek tilida.

## Xavfsizlik

- Barcha POST formalarida `{% csrf_token %}`; AJAX'da `X-CSRFToken` header.
- Foydalanuvchi kiritgan matn shablonda avtomatik escape qilinadi — `|safe` ishlatmang.
- Yozuv o'zgartiruvchi endpointlar: `@login_required` + `@require_POST`.
- Dashboard view'lari `StaffRequiredMixin` bilan himoyalanadi.
- `DEBUG=False` bo'lganda HSTS, SSL redirect, secure cookie'lar avtomatik yoqiladi.
