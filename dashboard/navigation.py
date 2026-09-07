"""Boshqaruv paneli sidebar'ini ruxsatlar asosida quruvchi modul.

``base_dashboard.html`` endi qo'lda yozilgan havolalar ro'yxati emas,
balki shu yerdagi ``NAV_SECTIONS`` dan ``build_nav(request)`` orqali
chiziladi — foydalanuvchida ruxsat bo'lmagan bandlar avtomatik
yashiriladi, bo'sh qolgan guruhlar butunlay ko'rsatilmaydi.
"""

from dataclasses import dataclass, field

from django.urls import NoReverseMatch, reverse

from core.models import ContactMessage
from reviews.models import Review
from shop.models import Order


@dataclass
class NavItem:
    label: str
    url_name: str
    icon: str
    perms: list[str] = field(default_factory=list)
    # is-active holatini aniqlash uchun prefiks. Bo'sh bo'lsa aniqlangan
    # url'ning o'zi ishlatiladi. Masalan "/dashboard/movies/" prefiksi
    # "/dashboard/movies/add/" va "/dashboard/movies/5/edit/" uchun ham
    # to'g'ri ishlaydi — eski aniq tenglik solishtirishning kamchiligi shu edi.
    match_prefix: str = ""
    count_key: str = ""


NAV_SECTIONS = [
    ("Kontent", [
        NavItem("Umumiy", "dashboard:index", "grid"),
        NavItem("Filmlar", "dashboard:movie_list", "film",
                perms=["movies.view_movie"], match_prefix="/dashboard/movies/"),
        NavItem("Seriallar", "dashboard:series_list", "film",
                perms=["series.view_series"], match_prefix="/dashboard/series/"),
        NavItem("Janrlar", "dashboard:genre_list", "trending",
                perms=["movies.view_genre"], match_prefix="/dashboard/genres/"),
        NavItem("Kategoriyalar", "dashboard:category_list", "grid",
                perms=["movies.view_category"], match_prefix="/dashboard/categories/"),
    ]),
    ("Moderatsiya", [
        NavItem("Foydalanuvchilar", "dashboard:user_list", "users",
                perms=["users.view_user"], match_prefix="/dashboard/users/"),
        NavItem("Sharhlar", "dashboard:review_list", "message",
                perms=["reviews.view_review"], match_prefix="/dashboard/reviews/",
                count_key="reviews_pending"),
        NavItem("Murojaatlar", "dashboard:message_list", "mail",
                perms=["core.view_contactmessage"], match_prefix="/dashboard/messages/",
                count_key="messages_unread"),
    ]),
    ("Do'kon", [
        NavItem("Mahsulotlar", "dashboard:shop_product_list", "star",
                perms=["shop.view_product"], match_prefix="/dashboard/shop/products/"),
        NavItem("Buyurtmalar", "dashboard:shop_order_list", "mail",
                perms=["shop.view_order"], match_prefix="/dashboard/shop/orders/",
                count_key="orders_pending"),
    ]),
    ("Sayt", [
        NavItem("Bosh sahifa", "dashboard:homepage_sections", "grid",
                perms=["dashboard.manage_homepage"], match_prefix="/dashboard/homepage/"),
        NavItem("Bannerlar", "dashboard:banner_list", "star",
                perms=["dashboard.manage_banners"], match_prefix="/dashboard/banners/"),
        NavItem("Bildirishnomalar", "dashboard:notification_list", "message",
                perms=["dashboard.send_notifications"], match_prefix="/dashboard/notifications/"),
        NavItem("Sozlamalar", "dashboard:site_settings", "settings",
                perms=["dashboard.manage_settings"], match_prefix="/dashboard/settings/"),
    ]),
    ("Tizim", [
        NavItem("Analitika", "dashboard:analytics", "trending",
                perms=["dashboard.view_analytics"], match_prefix="/dashboard/analytics/"),
        NavItem("Rollar", "dashboard:role_list", "shield",
                perms=["dashboard.manage_roles"], match_prefix="/dashboard/roles/"),
    ]),
]


def get_nav_counts():
    """Sidebar badge raqamlari. Bo'limlar hali yaratilmagan bo'lsa 0 qaytaradi."""
    return {
        "reviews_pending": Review.objects.filter(status=Review.Status.PENDING).count(),
        "messages_unread": ContactMessage.objects.filter(is_read=False).count(),
        "orders_pending": Order.objects.filter(status=Order.Status.PENDING).count(),
    }


def build_nav(request):
    """Joriy foydalanuvchi uchun ruxsat bo'yicha filtrlangan sidebar tuzilmasi.

    Har bir band uchun URL hali yaratilmagan bo'lishi mumkin (masalan
    Blok A bosqichida "dashboard:series_list" hali mavjud emas) —
    shunday holatda ``NoReverseMatch`` band jimgina o'tkazib yuboriladi,
    shablon xato bermaydi.
    """
    user = request.user
    counts = get_nav_counts()
    result = []

    for group_title, items in NAV_SECTIONS:
        visible_items = []

        for item in items:
            if item.perms and not user.is_superuser:
                if not all(user.has_perm(p) for p in item.perms):
                    continue

            try:
                url = reverse(item.url_name)
            except NoReverseMatch:
                continue

            match = item.match_prefix or url
            # "dashboard:index" ning o'zi "/dashboard/" bo'lib, bu barcha
            # boshqa dashboard sahifalarining prefiksi hamdir — shuning
            # uchun uni startswith bilan solishtirsak, u DOIM faol bo'lib
            # ko'rinib qolardi. Faqat aynan shu sahifada ekanimizda,
            # ya'ni prefiks berilmagan (match == url) holatda, aniq
            # tenglik bilan tekshiramiz; boshqa bandlar uchun prefiks
            # solishtiruvi (sub-sahifalarni ham yoritish uchun) davom etadi.
            if item.match_prefix:
                is_active = request.path.startswith(match)
            else:
                is_active = request.path == match
            count = counts.get(item.count_key, 0) if item.count_key else 0

            visible_items.append({
                "label": item.label,
                "url": url,
                "icon": item.icon,
                "is_active": is_active,
                "count": count,
            })

        if visible_items:
            result.append((group_title, visible_items))

    return result
