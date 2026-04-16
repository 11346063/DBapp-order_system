function updateCartQty(index, delta) {
    const qtyEl = document.getElementById(`qty-${index}`);
    let qty = parseInt(qtyEl.textContent) + delta;
    if (qty < 1) qty = 1;

    postJSON('/cart/update/', { index: index, quantity: qty })
        .then(data => {
            if (data.success) {
                qtyEl.textContent = qty;
                document.getElementById('cartTotal').textContent = `$${data.total}`;
                location.reload();
            }
        })
        .catch(() => {});
}

function removeCartItem(index) {
    postJSON('/cart/remove/', { index: index })
        .then(data => {
            if (data.success) {
                location.reload();
            }
        })
        .catch(() => {});
}
