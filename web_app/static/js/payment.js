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

    listEl.innerHTML = '';
    (data.price_changes || []).forEach(function (change) {
        const row = document.createElement('div');
        row.className = 'price-change-row';

        const leftDiv = document.createElement('div');
        const nameSpan = document.createElement('span');
        nameSpan.className = 'text-white';
        nameSpan.textContent = change.name;
        leftDiv.appendChild(nameSpan);
        const qtySpan = document.createElement('span');
        qtySpan.className = 'text-secondary small ms-2';
        qtySpan.textContent = 'x' + parseInt(change.quantity);
        leftDiv.appendChild(qtySpan);
        row.appendChild(leftDiv);

        const rightDiv = document.createElement('div');
        rightDiv.className = 'price-change-values';
        const oldSpan = document.createElement('span');
        oldSpan.className = 'text-secondary';
        oldSpan.textContent = money(change.old_unit_price);
        rightDiv.appendChild(oldSpan);
        const arrowI = document.createElement('i');
        arrowI.className = 'bi bi-arrow-right-short';
        rightDiv.appendChild(arrowI);
        const newSpan = document.createElement('span');
        newSpan.className = 'text-yellow fw-bold';
        newSpan.textContent = money(change.new_unit_price);
        rightDiv.appendChild(newSpan);
        row.appendChild(rightDiv);

        listEl.appendChild(row);
    });

    totalEl.textContent = money(data.new_total);
}

function _renderOrderSummary(cart) {
    if (!cart || !cart.length) return null;

    const card = document.createElement('div');
    card.className = 'card card-dark';

    const header = document.createElement('div');
    header.className = 'card-header border-bottom border-secondary';
    const headerTitle = document.createElement('h6');
    headerTitle.className = 'text-white mb-0';
    headerTitle.textContent = '訂單明細';
    header.appendChild(headerTitle);
    card.appendChild(header);

    const body = document.createElement('div');
    body.className = 'card-body';

    cart.forEach(function (item, i) {
        const isLast = i === cart.length - 1;
        const row = document.createElement('div');
        row.className = 'd-flex justify-content-between align-items-start mb-3' +
            (isLast ? '' : ' pb-3 border-bottom border-secondary');

        const leftDiv = document.createElement('div');
        const nameSpan = document.createElement('span');
        nameSpan.className = 'text-white';
        nameSpan.textContent = item.name;
        leftDiv.appendChild(nameSpan);

        const qtySpan = document.createElement('span');
        qtySpan.className = 'text-secondary small ms-2';
        qtySpan.textContent = 'x' + parseInt(item.quantity);
        leftDiv.appendChild(qtySpan);

        if (item.options && item.options.length) {
            const optsDiv = document.createElement('div');
            optsDiv.className = 'text-secondary small';
            item.options.forEach(function (o) {
                const span = document.createElement('span');
                span.className = 'me-2';
                span.textContent = '+ ' + o.name;
                optsDiv.appendChild(span);
            });
            leftDiv.appendChild(optsDiv);
        }

        row.appendChild(leftDiv);

        const subtotalSpan = document.createElement('span');
        subtotalSpan.className = 'text-yellow fw-bold';
        subtotalSpan.textContent = '$' + parseInt(item.subtotal);
        row.appendChild(subtotalSpan);

        body.appendChild(row);
    });

    card.appendChild(body);
    return card;
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
    if (summaryEl) {
        const summaryNode = _renderOrderSummary(cart);
        if (summaryNode) summaryEl.appendChild(summaryNode);
    }

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
                .catch(errMsg => {
                    isSubmitting = false;
                    setSubmitValidating(btn, false);
                    showToast(typeof errMsg === 'string' ? errMsg : '驗證價格失敗，請稍後再試');
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
                    .catch((errMsg) => {
                        isSubmitting = false;
                        acceptBtn.disabled = false;
                        acceptBtn.innerHTML = '<i class="bi bi-check2-circle"></i> 接受最新價格並送出';
                        showToast(typeof errMsg === 'string' ? errMsg : '價格同步失敗，請稍後再試');
                    });
            });
        }
    }
});
