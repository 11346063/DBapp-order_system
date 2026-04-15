function reorder(orderId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>加入中...';

    postJSON(window.URLS.reorder, { order_id: orderId })
        .then(data => {
            if (data.success) {
                // Update cart badge in navbar
                const badge = document.querySelector('.navbar .badge');
                if (badge) {
                    badge.textContent = data.cart_count;
                    badge.style.display = '';
                } else {
                    // Create badge if not exists
                    const cartLink = document.querySelector('.nav-icon-link');
                    if (cartLink) {
                        const newBadge = document.createElement('span');
                        newBadge.className = 'position-absolute top-0 start-100 translate-middle badge rounded-pill';
                        newBadge.style.cssText = 'background-color: var(--primary-yellow); color: #000;';
                        newBadge.textContent = data.cart_count;
                        cartLink.appendChild(newBadge);
                    }
                }

                // Show toast
                const toastMsg = document.getElementById('reorderToastMsg');
                toastMsg.textContent = `已將 ${data.added} 項商品加入購物車`;
                const toast = new bootstrap.Toast(document.getElementById('reorderToast'));
                toast.show();

                btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>已加入';
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-cart-plus me-1"></i>再來一份';
                }, 2000);
            }
        })
        .catch(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-cart-plus me-1"></i>再來一份';
        });
}