function updateCartQty(index, delta) {
    const qtyEl = document.getElementById(`qty-${index}`);
    let qty = parseInt(qtyEl.textContent) + delta;
    if (qty < 1) qty = 1;

    postJSON('/api/cart/update/', { index: index, quantity: qty })
        .then(data => {
            if (data.status === 'success') {
                qtyEl.textContent = qty;
                document.getElementById('cartTotal').textContent = `$${data.data.total}`;
                location.reload();
            }
        })
        .catch(() => {});
}

function removeCartItem(index) {
    postJSON('/api/cart/remove/', { index: index })
        .then(data => {
            if (data.status === 'success') {
                location.reload();
            }
        })
        .catch(() => {});
}
