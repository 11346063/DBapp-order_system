let currentItem = null;
let currentQty = 1;

function openItemDetail(menuId) {
    fetch(`/api/menu/${menuId}/`)
        .then(res => res.json())
        .then(data => {
            currentItem = data.data;
            currentQty = 1;
            fillDetail(data.data);

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
        const imageEl = document.getElementById(`${prefix}ItemImage`);
        const qtyEl = document.getElementById(`${prefix}Qty`);
        const optEl = document.getElementById(`${prefix}Options`);
        const statusBadge = document.getElementById(`${prefix}StatusBadge`);

        if (nameEl) nameEl.textContent = data.name;
        if (priceEl) priceEl.textContent = `$${data.price}`;
        if (infoEl) {
            infoEl.textContent = data.info || '';
            infoEl.style.display = data.info ? '' : 'none';
        }
        if (imageEl) {
            const iconEl = imageEl.parentElement?.querySelector('i');
            if (data.image_url) {
                imageEl.src = data.image_url;
                imageEl.alt = data.name;
                imageEl.classList.remove('d-none');
                if (iconEl) iconEl.classList.add('d-none');
            } else {
                imageEl.removeAttribute('src');
                imageEl.alt = '';
                imageEl.classList.add('d-none');
                if (iconEl) iconEl.classList.remove('d-none');
            }
        }
        if (qtyEl) qtyEl.textContent = '1';

        if (optEl) {
            // 將「切」從一般 checkbox 選項中篩除，單獨作為切法 radio
            const regularOpts = (data.options || []).filter(o => o.name !== '切');
            const cutOpt = (data.options || []).find(o => o.name === '切');

            let html = '';
            if (regularOpts.length > 0) {
                html += regularOpts.map(opt => `
                    <label class="option-check">
                        <input type="checkbox" value="${opt.id}" data-price="${opt.price}">
                        <span>${opt.name}</span>
                        <span class="option-price">+$${opt.price}</span>
                    </label>
                `).join('');
            }
            if (cutOpt) {
                html += `
                    <div class="text-secondary small mt-2 mb-1">切法 <span class="text-danger">*</span></div>
                    <label class="option-check">
                        <input type="radio" name="${prefix}CutOption" value="0" data-price="0" data-opt-id="${cutOpt.id}">
                        <span>不切</span>
                    </label>
                    <label class="option-check">
                        <input type="radio" name="${prefix}CutOption" value="1" data-price="0" data-opt-id="${cutOpt.id}">
                        <span>切</span>
                    </label>
                    <div class="text-danger small mt-1 d-none" id="${prefix}CutError">請選擇切法</div>
                `;
            }
            optEl.innerHTML = html;
            optEl.style.display = html.trim() ? '' : 'none';
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
        el.classList.remove('d-none');
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
    const options = Array.from(checked).map(cb => ({
        id: parseInt(cb.value),
        name: cb.parentElement.querySelector('span').textContent,
        price: parseInt(cb.dataset.price),
    }));

    const cutRadio = container.querySelector('input[type="radio"][name$="CutOption"]:checked');
    if (cutRadio) {
        options.push({
            id: parseInt(cutRadio.dataset.optId),
            name: cutRadio.value === '1' ? '切' : '不切',
            price: 0,
            level: parseInt(cutRadio.value),
        });
    }

    return options;
}

function addToCart() {
    if (!currentItem) return;

    const hasCutOpt = (currentItem.options || []).some(o => o.name === '切');
    if (hasCutOpt) {
        const prefix = window.innerWidth < 768 ? 'offcanvas' : 'modal';
        const container = document.getElementById(`${prefix}Options`);
        const cutRadio = container ? container.querySelector('input[type="radio"][name$="CutOption"]:checked') : null;
        const errorEl = document.getElementById(`${prefix}CutError`);
        if (!cutRadio) {
            if (errorEl) errorEl.classList.remove('d-none');
            return;
        }
        if (errorEl) errorEl.classList.add('d-none');
    }

    const selectedOptions = getSelectedOptions();

    if (typeof window.assistedOrderAddToCart === 'function') {
        window.assistedOrderAddToCart(currentItem, currentQty, selectedOptions);
        return;
    }

    const optionsPrice = selectedOptions.reduce((s, o) => s + (parseInt(o.price) || 0), 0);
    const unitPrice = currentItem.price + optionsPrice;
    if (window.cartAddItem) {
        window.cartAddItem({
            menu_id: currentItem.id,
            name: currentItem.name,
            base_price: currentItem.price,
            options: selectedOptions,
            options_price: optionsPrice,
            unit_price: unitPrice,
            quantity: currentQty,
            subtotal: unitPrice * currentQty,
        });
    }
    const count = window.cartCount ? window.cartCount() : 0;
    updateCartBadge(count);
    closeItemDetail();
    showCartFeedback({ cart_count: count });
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
