let currentItem = null;
let currentQty = 1;

function openItemDetail(menuId) {
    fetch(`/api/menu/${menuId}/`)
        .then(res => res.json())
        .then(data => {
            currentItem = data;
            currentQty = 1;
            fillDetail(data);

            if (window.innerWidth < 768) {
                const offcanvas = new bootstrap.Offcanvas(document.getElementById('itemOffcanvas'));
                offcanvas.show();
            } else {
                const modal = new bootstrap.Modal(document.getElementById('itemModal'));
                modal.show();
            }
        });
}

function fillDetail(data) {
    const isStaff = window.IS_STAFF === true;

    const setContent = (prefix) => {
        const nameEl = document.getElementById(`${prefix}ItemName`);
        const priceEl = document.getElementById(`${prefix}ItemPrice`);
        const infoEl = document.getElementById(`${prefix}ItemInfo`);
        const qtyEl = document.getElementById(`${prefix}Qty`);
        const optEl = document.getElementById(`${prefix}Options`);
        const statusBadge = document.getElementById(`${prefix}StatusBadge`);

        if (nameEl) nameEl.textContent = data.name;
        if (priceEl) priceEl.textContent = `$${data.price}`;
        if (infoEl) {
            infoEl.textContent = data.info || '';
            infoEl.style.display = data.info ? '' : 'none';
        }
        if (qtyEl) qtyEl.textContent = '1';

        if (optEl) {
            if (!isStaff && data.options && data.options.length > 0) {
                optEl.innerHTML = data.options.map(opt => `
                    <label class="option-check">
                        <input type="checkbox" value="${opt.id}" data-price="${opt.price}">
                        <span>${opt.name}</span>
                        <span class="option-price">+$${opt.price}</span>
                    </label>
                `).join('');
                optEl.style.display = '';
            } else {
                optEl.innerHTML = '';
                optEl.style.display = 'none';
            }
        }

        if (statusBadge) {
            if (data.status) {
                statusBadge.textContent = '上架中';
                statusBadge.className = 'badge fs-6 px-3 py-2 bg-success';
            } else {
                statusBadge.textContent = '已下架';
                statusBadge.className = 'badge fs-6 px-3 py-2 bg-danger';
            }
        }
    };

    setContent('offcanvas');
    setContent('modal');

    // 依身份切換操作區
    document.querySelectorAll('.customer-actions').forEach(el => {
        el.classList.toggle('d-none', isStaff);
    });
    document.querySelectorAll('.staff-actions').forEach(el => {
        el.classList.toggle('d-none', !isStaff);
    });
}

function changeQty(delta) {
    currentQty = Math.max(1, currentQty + delta);
    const offQty = document.getElementById('offcanvasQty');
    const modQty = document.getElementById('modalQty');
    if (offQty) offQty.textContent = currentQty;
    if (modQty) modQty.textContent = currentQty;
}

function closeItemDetail() {
    const offcanvasEl = document.getElementById('itemOffcanvas');
    const modalEl = document.getElementById('itemModal');

    if (!window.bootstrap) return;

    if (offcanvasEl && offcanvasEl.classList.contains('show')) {
        bootstrap.Offcanvas.getOrCreateInstance(offcanvasEl).hide();
    }
    if (modalEl && modalEl.classList.contains('show')) {
        bootstrap.Modal.getOrCreateInstance(modalEl).hide();
    }
}

function continueOrdering() {
    closeItemDetail();
}

function dismissCartFeedback() {
    closeItemDetail();
}

function updateCartBadge(cartCount) {
    const cartLink = document.querySelector('.navbar a[href="/cart/"]');
    if (!cartLink) {
        updateMobileCartSummary(cartCount);
        return;
    }

    let badge = cartLink.querySelector('.badge');
    if (!badge) {
        badge = document.createElement('span');
        badge.className = 'position-absolute badge rounded-pill';
        badge.style.top = '-4px';
        badge.style.right = '-4px';
        badge.style.backgroundColor = 'var(--primary-yellow)';
        badge.style.color = '#000';
        badge.style.fontSize = '0.65rem';
        cartLink.appendChild(badge);
    }

    badge.textContent = cartCount;
    badge.style.display = cartCount > 0 ? '' : 'none';
    updateMobileCartSummary(cartCount);
}

function updateMobileCartSummary(cartCount) {
    const summary = document.getElementById('mobileCartSummary');
    const count = document.getElementById('mobileCartSummaryCount');
    if (!summary || !count) return;

    count.textContent = cartCount;
    summary.classList.toggle('d-none', cartCount <= 0);
}

function showCartFeedback(data) {
    const feedback = document.getElementById('cartFeedback');
    const feedbackText = document.getElementById('cartFeedbackText');
    if (!feedback) return;

    if (feedbackText) {
        feedbackText.textContent = `購物車目前有 ${data.cart_count} 件商品。`;
    }

    feedback.classList.remove('d-none');
}

function getSelectedOptions() {
    const container = window.innerWidth < 768
        ? document.getElementById('offcanvasOptions')
        : document.getElementById('modalOptions');

    if (!container) return [];

    const checked = container.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checked).map(cb => ({
        id: parseInt(cb.value),
        name: cb.parentElement.querySelector('span').textContent,
        price: parseInt(cb.dataset.price),
    }));
}

function addToCart() {
    if (!currentItem) return;

    const selectedOptions = getSelectedOptions();

    postJSON('/cart/add/', {
        menu_id: currentItem.id,
        name: currentItem.name,
        price: currentItem.price,
        quantity: currentQty,
        options: selectedOptions,
    }).then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            closeItemDetail();
            showCartFeedback(data);
        }
    }).catch(() => {});
}

document.addEventListener('click', function (event) {
    const actionButton = event.target.closest('[data-cart-action]');
    if (!actionButton) return;

    const action = actionButton.dataset.cartAction;
    if (action === 'continue') {
        continueOrdering();
    }
    if (action === 'dismiss-feedback') {
        dismissCartFeedback();
    }
});

window.continueOrdering = continueOrdering;
window.dismissCartFeedback = dismissCartFeedback;
