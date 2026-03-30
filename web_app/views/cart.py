import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST


def cart_view(request):
    cart = request.session.get('cart', [])
    total = sum(item['subtotal'] for item in cart)
    return render(request, 'cart.html', {
        'cart_items': cart,
        'total': total,
    })


@require_POST
def cart_add(request):
    data = json.loads(request.body)
    cart = request.session.get('cart', [])

    menu_id = data['menu_id']
    name = data['name']
    price = data['price']
    quantity = data.get('quantity', 1)
    options = data.get('options', [])

    options_price = sum(opt['price'] for opt in options)
    unit_price = price + options_price
    subtotal = unit_price * quantity

    cart.append({
        'menu_id': menu_id,
        'name': name,
        'base_price': price,
        'options': options,
        'options_price': options_price,
        'unit_price': unit_price,
        'quantity': quantity,
        'subtotal': subtotal,
    })

    request.session['cart'] = cart
    cart_count = sum(item['quantity'] for item in cart)

    return JsonResponse({'success': True, 'cart_count': cart_count})


@require_POST
def cart_update(request):
    data = json.loads(request.body)
    index = data['index']
    quantity = data['quantity']
    cart = request.session.get('cart', [])

    if 0 <= index < len(cart):
        if quantity <= 0:
            cart.pop(index)
        else:
            cart[index]['quantity'] = quantity
            cart[index]['subtotal'] = cart[index]['unit_price'] * quantity

    request.session['cart'] = cart
    total = sum(item['subtotal'] for item in cart)
    cart_count = sum(item['quantity'] for item in cart)

    return JsonResponse({'success': True, 'total': total, 'cart_count': cart_count})


@require_POST
def cart_remove(request):
    data = json.loads(request.body)
    index = data['index']
    cart = request.session.get('cart', [])

    if 0 <= index < len(cart):
        cart.pop(index)

    request.session['cart'] = cart
    total = sum(item['subtotal'] for item in cart)
    cart_count = sum(item['quantity'] for item in cart)

    return JsonResponse({'success': True, 'total': total, 'cart_count': cart_count})
