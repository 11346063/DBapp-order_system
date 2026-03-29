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
