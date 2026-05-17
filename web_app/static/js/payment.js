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

document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form[action*="order/submit"]');
    if (form) {
        form.addEventListener('submit', function () {
            const btn = form.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>送出中...';
        });
    }
});
