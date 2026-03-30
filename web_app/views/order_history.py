import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from web_app.models import Order, OrderItem, Menu


@login_required
def order_history_view(request):
    """Display the current user's past orders (newest first)."""
    orders = (
        Order.objects
        .filter(user=request.user)
        .order_by('-create_time')
    )

    for order in orders:
        order.items = OrderItem.objects.filter(order=order).select_related('menu')

    return render(request, 'order_history.html', {'orders': orders})


@login_required
@require_POST
def reorder(request):
    """Copy all items from a past order into the session cart."""
    data = json.loads(request.body)
    order_id = data.get('order_id')
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order).select_related('menu')

    cart = request.session.get('cart', [])

    added = 0
    for item in items:
        try:
            menu = item.menu
            cart.append({
                'menu_id': menu.pk,
                'name': menu.name,
                'base_price': menu.price,
                'options': [],
                'options_price': 0,
                'unit_price': menu.price,
                'quantity': item.amount,
                'subtotal': menu.price * item.amount,
            })
            added += item.amount
        except Menu.DoesNotExist:
            continue

    request.session['cart'] = cart
    cart_count = sum(i['quantity'] for i in cart)

    return JsonResponse({'success': True, 'added': added, 'cart_count': cart_count})
