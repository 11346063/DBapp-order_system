// In-memory order draft for staff assisted ordering
let orderItems = [];

const garlicPrice = window.GARLIC_PRICE || 0;
const basilPrice = window.BASIL_PRICE || 0;
const submitUrl = window.ASSISTED_ORDER_URL || '/api/v1/orders/staff/';
const cutRequiredIds = new Set(window.CUT_REQUIRED_IDS || []);

// ---------- State management ----------

function _groupKey(menuId, options) {
    const cutOpt = (options || []).find(o => o.name === '切' || o.name === '不切');
    return `${menuId}_${cutOpt ? cutOpt.name : 'none'}`;
}

function addToOrderDraft(menuId, name, price, options, qty) {
    qty = qty || 1;
    const key = _groupKey(menuId, options);
    const existing = orderItems.find(i => i._key === key);
    if (existing) {
        existing.qty += qty;
    } else {
        orderItems.push({ _key: key, menu_id: menuId, name, price, qty, options: options || [] });
    }
    renderOrderDraft();
}

function removeOrderItem(index) {
    orderItems.splice(index, 1);
    renderOrderDraft();
}

function changeOrderItemQty(index, delta) {
    orderItems[index].qty += delta;
    if (orderItems[index].qty <= 0) {
        orderItems.splice(index, 1);
    }
    renderOrderDraft();
}

function clearOrderDraft() {
    orderItems = [];
    renderOrderDraft();
}

// ---------- Rendering ----------

function renderOrderDraft() {
    const list = document.getElementById('orderDraftList');
    const emptyState = document.getElementById('orderEmptyState');
    if (!list) return;

    const existingItems = list.querySelectorAll('.order-draft-item');
    existingItems.forEach(el => el.remove());

    if (orderItems.length === 0) {
        if (emptyState) emptyState.classList.remove('d-none');
        updateTotal();
        return;
    }
    if (emptyState) emptyState.classList.add('d-none');

    orderItems.forEach((item, index) => {
        const cutOpt = item.options.find(o => o.name === '切' || o.name === '不切');
        const cutLabel = cutOpt ? ` (${cutOpt.name})` : '';
        const subtotal = item.price * item.qty;

        const div = document.createElement('div');
        div.className = 'order-draft-item';
        div.innerHTML = `
            <button class="item-delete-btn" onclick="removeOrderItem(${index})" aria-label="刪除">
                <i class="bi bi-x"></i>
            </button>
            <div class="pe-4">
                <span class="item-name">${item.name}</span>
                <span class="item-cut">${cutLabel}</span>
            </div>
            <div class="d-flex justify-content-between align-items-center mt-1">
                <div class="item-qty-controls">
                    <button class="qty-btn" onclick="changeOrderItemQty(${index}, -1)">−</button>
                    <span class="qty-value">${item.qty}</span>
                    <button class="qty-btn" onclick="changeOrderItemQty(${index}, 1)">+</button>
                </div>
                <span class="item-subtotal">$${subtotal}</span>
            </div>
        `;
        list.appendChild(div);
    });

    updateTotal();
    // 自動捲到最底，讓新加入的品項保持可見
    list.scrollTop = list.scrollHeight;
}

function updateTotal() {
    const menuTotal = orderItems.reduce((sum, i) => sum + i.price * i.qty, 0);

    const garlicQty = parseInt(document.getElementById('extra_garlic_qty')?.value || '0', 10);
    const basilQty = parseInt(document.getElementById('extra_basil_qty')?.value || '0', 10);
    const extraTotal = garlicQty * garlicPrice + basilQty * basilPrice;

    let customTotal = 0;
    document.querySelectorAll('.custom-extra-check:checked').forEach(cb => {
        customTotal += parseInt(cb.dataset.price || '0', 10);
    });

    const total = menuTotal + extraTotal + customTotal;
    const el = document.getElementById('assistedTotal');
    if (el) el.textContent = `$${total}`;
}

// ---------- Extra ingredients ----------

function changeExtra(fieldId, delta) {
    const input = document.getElementById(fieldId);
    if (!input) return;
    const current = parseInt(input.value || '0', 10);
    const next = Math.max(0, current + delta);
    input.value = next;
    const displayId = fieldId === 'extra_garlic_qty' ? 'extraGarlicDisplay' : 'extraBasilDisplay';
    const display = document.getElementById(displayId);
    if (display) display.textContent = next;
    updateTotal();
}

// ---------- Submit ----------

async function submitStaffOrder() {
    const phone = (document.getElementById('customerPhone')?.value || '').trim();
    if (!phone) {
        showError('請填寫客人電話');
        return;
    }
    if (orderItems.length === 0) {
        showError('請先加入品項');
        return;
    }

    const spicyLevel = document.querySelector('input[name="ao_spicy"]:checked')?.value || '不辣';
    const garlicQty = parseInt(document.getElementById('extra_garlic_qty')?.value || '0', 10);
    const basilQty = parseInt(document.getElementById('extra_basil_qty')?.value || '0', 10);
    const remark = (document.getElementById('orderRemark')?.value || '').trim();
    const customOptions = Array.from(document.querySelectorAll('.custom-extra-check:checked'))
        .map(cb => parseInt(cb.value, 10));

    const items = orderItems.map(i => ({
        menu_id: i.menu_id,
        qty: i.qty,
        options: i.options.map(o => ({ id: o.id, level: o.level ?? 1, name: o.name, price: o.price ?? 0 })),
    }));

    const btn = document.getElementById('assistedSubmitBtn');
    if (btn) btn.disabled = true;
    hideError();

    const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';

    try {
        const resp = await fetch(submitUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                customer_phone: phone,
                spicy_level: spicyLevel,
                extra_garlic_qty: garlicQty,
                extra_basil_qty: basilQty,
                remark,
                custom_options: customOptions,
                items,
            }),
        });
        const data = await resp.json();
        if (data.status === 'success') {
            clearOrderDraft();
            document.getElementById('customerPhone').value = '';
            document.getElementById('orderRemark').value = '';
            document.querySelector('input[name="ao_spicy"][value="不辣"]').checked = true;
            changeExtra('extra_garlic_qty', -99);
            changeExtra('extra_basil_qty', -99);
            document.querySelectorAll('.custom-extra-check').forEach(cb => { cb.checked = false; });
            showSuccess(data.message || '代客訂單已送出');
        } else {
            showError(data.message || '送出失敗，請再試一次');
        }
    } catch (_e) {
        showError('網路錯誤，請再試一次');
    } finally {
        if (btn) btn.disabled = false;
    }
}

function showError(msg) {
    const el = document.getElementById('assistedError');
    if (!el) return;
    el.textContent = msg;
    el.classList.remove('d-none');
}

function hideError() {
    const el = document.getElementById('assistedError');
    if (el) el.classList.add('d-none');
}

function showSuccess(msg) {
    const el = document.getElementById('assistedError');
    if (!el) return;
    el.textContent = msg;
    el.classList.remove('d-none', 'text-danger');
    el.classList.add('text-success');
    setTimeout(() => {
        el.classList.add('d-none');
        el.classList.remove('text-success');
        el.classList.add('text-danger');
    }, 3000);
}

// ---------- Left panel click handler ----------

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('menuGrid')?.addEventListener('click', function (e) {
        const card = e.target.closest('.assisted-menu-card');
        if (!card) return;
        const menuId = parseInt(card.dataset.menuId, 10);
        const name = card.dataset.menuName;
        const price = parseInt(card.dataset.menuPrice, 10);
        const needsCut = card.dataset.cutRequired === 'true' || cutRequiredIds.has(menuId);

        if (needsCut) {
            openItemDetail(menuId);
        } else {
            addToOrderDraft(menuId, name, price, [], 1);
        }
    });

    // Update total when custom options change
    document.querySelectorAll('.custom-extra-check').forEach(cb => {
        cb.addEventListener('change', updateTotal);
    });
});

// ---------- detail.js hook: intercept addToCart for assisted ordering ----------

window.assistedOrderAddToCart = function (item, qty, selectedOptions) {
    addToOrderDraft(item.id, item.name, item.price, selectedOptions, qty);
    if (typeof closeItemDetail === 'function') closeItemDetail();
};
