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

document.addEventListener('DOMContentLoaded', function () {
    const acceptBtn = document.getElementById('acceptCartPriceChanges');
    if (!acceptBtn) return;

    acceptBtn.addEventListener('click', function () {
        acceptBtn.disabled = true;
        acceptBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>更新中...';

        postJSON('/api/v1/cart/sync-prices/', {})
            .then(data => {
                if (data.status === 'success') {
                    location.reload();
                    return;
                }
                acceptBtn.disabled = false;
                acceptBtn.innerHTML = '<i class="bi bi-check2-circle"></i> 接受最新價格';
            })
            .catch(() => {
                acceptBtn.disabled = false;
                acceptBtn.innerHTML = '<i class="bi bi-check2-circle"></i> 接受最新價格';
            });
    });
});
