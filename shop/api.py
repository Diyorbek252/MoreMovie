"""AJAX endpoint: mahsulot xaridi.

POST + login talab qiladi. Balans debeti va zaxira kamayishi atomik
tranzaksiya ichida amalga oshiriladi — race condition holatida ham
tugagan mahsulot sotilmaydi va balans manfiyga tushmaydi.
"""

import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import CinepointTransaction, Order, Product
from .services import InsufficientBalanceError, adjust_balance


def _payload(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST


@login_required
@require_POST
def purchase_product(request):
    """POST /api/shop/purchase/  body: {"product": <id>}"""
    data = _payload(request)
    product_id = data.get("product")

    if not product_id:
        return JsonResponse({"error": "mahsulot ko'rsatilmagan"}, status=400)

    product = get_object_or_404(Product, pk=product_id, is_active=True)

    with transaction.atomic():
        # Zaxira cheklangan bo'lsa, shartli UPDATE orqali atomik kamaytiramiz —
        # 0 qator qaytsa mahsulot ayni shu lahzada tugagan.
        if product.stock is not None:
            rows = Product.objects.filter(pk=product.pk, stock__gte=1).update(
                stock=F("stock") - 1
            )
            if not rows:
                return JsonResponse({"error": "Mahsulot zaxirasi tugagan."}, status=400)

        order = Order.objects.create(
            user=request.user,
            product=product,
            product_name=product.name,
            price_paid=product.price,
            status=Order.Status.PENDING,
        )

        try:
            adjust_balance(
                request.user,
                -product.price,
                CinepointTransaction.Reason.PURCHASE,
                note=f"«{product.name}» xaridi",
                related=order,
            )
        except InsufficientBalanceError:
            # Balans yetmadi — buyurtma va zaxira kamayishini bekor qilamiz.
            transaction.set_rollback(True)
            return JsonResponse({"error": "Balansingiz yetarli emas."}, status=400)

    request.user.profile.refresh_from_db(fields=["balance"])

    return JsonResponse(
        {
            "ok": True,
            "balance": request.user.profile.balance,
            "message": f"«{product.name}» xarid qilindi — buyurtmangiz tez orada yetkaziladi.",
        }
    )
