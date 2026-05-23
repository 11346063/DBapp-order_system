function changeExtra(fieldId, delta) {
    const input = document.getElementById(fieldId);
    if (!input) return;
    const newVal = Math.max(0, parseInt(input.value || 0) + delta);
    input.value = newVal;

    const isGarlic = fieldId === 'extra_garlic_qty';
    const displayEl = document.getElementById(isGarlic ? 'extraGarlicDisplay' : 'extraBasilDisplay');
    const priceEl = document.getElementById(isGarlic ? 'extraGarlicPrice' : 'extraBasilPrice');
    if (displayEl) displayEl.textContent = newVal;
    if (priceEl) priceEl.textContent = '+$' + (newVal * 10);

    updateTotal();
}

function updateTotal() {
    const garlic = parseInt(document.getElementById('extra_garlic_qty')?.value || 0);
    const basil = parseInt(document.getElementById('extra_basil_qty')?.value || 0);
    const extra = (garlic + basil) * 10;
    const el = document.getElementById('displayTotal');
    if (el) el.textContent = '$' + ((window.BASE_TOTAL || 0) + extra);
}

window.changeExtra = changeExtra;

function money(value) {
    return '$' + value;
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
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

    listEl.innerHTML = (data.price_changes || []).map(change => `
        <div class="price-change-row">
            <div>
                <span class="text-white">${escapeHtml(change.name)}</span>
                <span class="text-secondary small ms-2">x${escapeHtml(change.quantity)}</span>
            </div>
            <div class="price-change-values">
                <span class="text-secondary">${escapeHtml(money(change.old_unit_price))}</span>
                <i class="bi bi-arrow-right-short"></i>
                <span class="text-yellow fw-bold">${escapeHtml(money(change.new_unit_price))}</span>
            </div>
        </div>
    `).join('');
    totalEl.textContent = money(data.new_total);
}

document.addEventListener('DOMContentLoaded', function () {
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
            postJSON('/api/v1/cart/validate-prices/', {})
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

                postJSON('/api/v1/cart/sync-prices/', {})
                    .then(response => {
                        const data = response.data || {};
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
