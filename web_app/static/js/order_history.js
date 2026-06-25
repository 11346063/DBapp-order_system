function reorder(orderId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>加入中...';

    postJSON(window.URLS.reorder, { order_id: orderId })
        .then(data => {
            if (data.status === 'success') {
                const items = (data.data && data.data.items) || [];
                items.forEach(item => {
                    if (window.cartAddItem) window.cartAddItem(item);
                });

                const cartCount = window.cartCount ? window.cartCount() : items.length;
                const badge = document.querySelector('.navbar a[href="/cart/"] .badge');
                if (badge) {
                    badge.textContent = cartCount;
                    badge.style.display = cartCount > 0 ? '' : 'none';
                }
                const mobileCount = document.getElementById('mobileCartSummaryCount');
                if (mobileCount) mobileCount.textContent = cartCount;
                const mobileSummary = document.getElementById('mobileCartSummary');
                if (mobileSummary) mobileSummary.classList.toggle('d-none', cartCount <= 0);

                const toastMsg = document.getElementById('reorderToastMsg');
                if (toastMsg) toastMsg.textContent = `已將 ${data.data.added} 項商品加入購物車`;
                const toastEl = document.getElementById('reorderToast');
                if (toastEl) new bootstrap.Toast(toastEl).show();

                btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>已加入';
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-cart-plus me-1"></i>再來一份';
                }, 2000);
            }
        })
        .catch(errMsg => {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-cart-plus me-1"></i>再來一份';
            showToast(typeof errMsg === 'string' ? errMsg : '加入購物車失敗，請重試');
        });
}
