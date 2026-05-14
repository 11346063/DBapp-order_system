from django.http import JsonResponse


def request_response_demo(request):
    cart = request.session.get("cart", [])
    cart_count = sum(item.get("quantity", 0) for item in cart)

    return JsonResponse(
        {
            "method": request.method,
            "path": request.path,
            "query": request.GET.dict(),
            "is_authenticated": request.user.is_authenticated,
            "cart_count": cart_count,
        },
        json_dumps_params={"ensure_ascii": False},
    )

