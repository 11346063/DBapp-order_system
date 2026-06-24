function changeExtra(fieldId, delta) {
    const input = document.getElementById(fieldId);
    if (!input) return;
    const newVal = Math.max(0, parseInt(input.value || 0) + delta);
    input.value = newVal;

    const extraCost = window.EXTRA_INGREDIENT_COST || 10;
    const isGarlic = fieldId === 'extra_garlic_qty';
    const displayEl = document.getElementById(isGarlic ? 'extraGarlicDisplay' : 'extraBasilDisplay');
    const priceEl = document.getElementById(isGarlic ? 'extraGarlicPrice' : 'extraBasilPrice');
    if (displayEl) displayEl.textContent = newVal;
    if (priceEl) priceEl.textContent = '+$' + (newVal * extraCost);

    updateTotal();
}

function updateTotal() {
    const garlic = parseInt(document.getElementById('extra_garlic_qty')?.value || 0);
    const basil = parseInt(document.getElementById('extra_basil_qty')?.value || 0);
    const extraCost = window.EXTRA_INGREDIENT_COST || 10;
    const extra = (garlic + basil) * extraCost;

    let customTotal = 0;
    document.querySelectorAll('.custom-extra-check:checked').forEach(cb => {
        customTotal += parseInt(cb.dataset.price || 0);
    });

    const el = document.getElementById('displayTotal');
    if (el) el.textContent = '$' + ((window.BASE_TOTAL || 0) + extra + customTotal);
}

window.changeExtra = changeExtra;

function money(value) {
    return '$' + value;
}

function _escHtml(str) {
    return String(str == null ? '' : str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function setSubmitLoading(button, isLoading) {
    if (!button) return;
    button.disabled = isLoading;
    button.innerHTML = isLoading
        ? '<span class="spinner-border spinner-border-sm me-2"></span>送出中...'
        : '<i class="bi bi-check-circle"></i> 確認送出訂單';
}

function setSubmitValidating(button, isValidating) {
    if (!button) return;
    button.disabled = isValidating;
    button.innerHTML = isValidating
        ? '<span class="spinner-border spinner-border-sm me-2"></span>確認價格中...'
        : '<i class="bi bi-check-circle"></i> 確認送出訂單';
}

function renderPriceChanges(data) {
    const listEl = document.getElementById('paymentPriceChangeList');
    const totalEl = document.getElementById('paymentPriceChangeTotal');
    if (!listEl || !totalEl) return;

    listEl.innerHTML = (data.price_changes || []).map(change =>
        '<div class="price-change-row">' +
        '<div>' +
        '<span class="text-white">' + _escHtml(change.name) + '</span>' +
        '<span class="text-secondary small ms-2">x' + parseInt(change.quantity) + '</span>' +
        '</div>' +
        '<div class="price-change-values">' +
        '<span class="text-secondary">' + _escHtml(money(change.old_unit_price)) + '</span>' +
        '<i class="bi bi-arrow-right-short"></i>' +
        '<span class="text-yellow fw-bold">' + _escHtml(money(change.new_unit_price)) + '</span>' +
        '</div>' +
        '</div>'
    ).join('');
    totalEl.textContent = money(data.new_total);
}

function _renderOrderSummary(cart) {
    if (!cart || !cart.length) return '';
    const rows = cart.map(function (item, i) {
        const opts = (item.options || []).map(o =>
            '<span class="me-2">+ ' + _escHtml(o.name) + '</span>'
        ).join('');
        const optsHtml = opts ? '<div class="text-secondary small">' + opts + '</div>' : '';
        const isLast = i === cart.length - 1;
        return (
            '<div class="d-flex justify-content-between align-items-start mb-3' +
            (isLast ? '' : ' pb-3 border-bottom border-secondary') + '">' +
            '<div><span class="text-white">' + _escHtml(item.name) + '</span>' +
            '<span class="text-secondary small ms-2">x' + parseInt(item.quantity) + '</span>' +
            optsHtml + '</div>' +
            '<span class="text-yellow fw-bold">$' + parseInt(item.subtotal) + '</span>' +
            '</div>'
        );
    }).join('');
    return (
        '<div class="card card-dark"><div class="card-header border-bottom border-secondary">' +
        '<h6 class="text-white mb-0">訂單明細</h6></div>' +
        '<div class="card-body">' + rows + '</div></div>'
    );
}

document.addEventListener('DOMContentLoaded', function () {
    // 讀購物車
    const cart = window.getCart ? window.getCart() : [];
    if (!cart.length) {
        window.location.href = '/';
        return;
    }

    // 渲染訂單摘要
    const summaryEl = document.getElementById('paymentCartSummary');
    if (summaryEl) summaryEl.innerHTML = _renderOrderSummary(cart);

    // 設定總金額基準
    window.BASE_TOTAL = window.cartTotal ? window.cartTotal() : 0;
    updateTotal();

    document.querySelectorAll('.custom-extra-check').forEach(cb => {
        cb.addEventListener('change', updateTotal);
    });

    const form = document.querySelector('form[action*="order/submit"]');
    if (form) {
        let bypassPriceValidation = false;
        let isSubmitting = false;
        const btn = form.querySelector('button[type="submit"]');
        const modalEl = document.getElementById('cartPriceChangeModal');
        const modal = modalEl && window.bootstrap
            ? window.bootstrap.Modal.getOrCreateInstance(modalEl)
            : null;
        const acceptBtn = document.getElementById('acceptPaymentPriceChanges');

        form.addEventListener('submit', function (event) {
            // 填入 cart_json
            const cartInput = document.getElementById('cartJsonInput');
            if (cartInput) cartInput.value = JSON.stringify(window.getCart ? window.getCart() : []);

            if (isSubmitting) {
                event.preventDefault();
                return;
            }

            if (bypassPriceValidation) {
                isSubmitting = true;
                setSubmitLoading(btn, true);
                return;
            }

            event.preventDefault();
            isSubmitting = true;
            setSubmitValidating(btn, true);
            const currentCart = window.getCart ? window.getCart() : [];
            postJSON('/api/v1/cart/validate-prices/', { cart: currentCart })
                .then(response => {
                    const data = response.data || {};
                    if (!data.has_changes) {
                        bypassPriceValidation = true;
                        setSubmitLoading(btn, true);
                        form.submit();
                        return;
                    }
                    renderPriceChanges(data);
                    isSubmitting = false;
                    setSubmitValidating(btn, false);
                    if (modal) modal.show();
                })
                .catch(() => {
                    bypassPriceValidation = true;
                    setSubmitLoading(btn, true);
                    form.submit();
                });
        });

        if (acceptBtn) {
            acceptBtn.addEventListener('click', function () {
                acceptBtn.disabled = true;
                acceptBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>更新中...';

                const currentCart = window.getCart ? window.getCart() : [];
                postJSON('/api/v1/cart/sync-prices/', { cart: currentCart })
                    .then(response => {
                        const data = response.data || {};
                        if (data.cart && window.saveCart) {
                            window.saveCart(data.cart);
                        }
                        if (typeof data.total !== 'undefined') {
                            window.BASE_TOTAL = data.total;
                            updateTotal();
                        }
                        bypassPriceValidation = true;
                        if (modal) modal.hide();
                        setSubmitLoading(btn, true);
                        form.submit();
                    })
                    .catch(() => {
                        isSubmitting = false;
                        acceptBtn.disabled = false;
                        acceptBtn.innerHTML = '<i class="bi bi-check2-circle"></i> 接受最新價格並送出';
                    });
            });
        }
    }
});
