from django.http import JsonResponse

from web_app.services import cart as cart_service


def request_response_demo(request):
    cart = cart_service.get_cart(request.user, request.session)
    count = cart_service.cart_count(cart)

    return JsonResponse(
        {
            "method": request.method,
            "path": request.path,
            "query": request.GET.dict(),
            "is_authenticated": request.user.is_authenticated,
            "cart_count": count,
        },
        json_dumps_params={"ensure_ascii": False},
    )
