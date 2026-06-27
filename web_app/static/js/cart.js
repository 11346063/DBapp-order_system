/* ─────────────────────────────────────────
   購物車 — localStorage 儲存
   key: 'dbapp_cart'
   item format: { menu_id, name, base_price, options, options_price, unit_price, quantity, subtotal }
   ───────────────────────────────────────── */

const CART_KEY = 'dbapp_cart';

function cartI18n(key, fallback) {
    return (window.CART_I18N && window.CART_I18N[key]) || fallback;
}

function getCart() {
    try {
        return JSON.parse(localStorage.getItem(CART_KEY) || '[]');
    } catch (e) {
        return [];
    }
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    _refreshBadge();
}

function cartCount() {
    return getCart().reduce(function (s, i) { return s + (parseInt(i.quantity) || 0); }, 0);
}

function cartTotal() {
    return getCart().reduce(function (s, i) { return s + (parseInt(i.subtotal) || 0); }, 0);
}

function cartAddItem(item) {
    const cart = getCart();
    cart.push(item);
    saveCart(cart);
}

function cartRemoveItem(index) {
    const cart = getCart();
    cart.splice(index, 1);
    saveCart(cart);
    renderCartPage();
}

function cartUpdateQty(index, delta) {
    const cart = getCart();
    if (index < 0 || index >= cart.length) return;
    const item = cart[index];
    const newQty = Math.max(1, (parseInt(item.quantity) || 1) + delta);
    item.quantity = newQty;
    item.subtotal = item.unit_price * newQty;
    saveCart(cart);
    const qtyEl = document.getElementById('qty-' + index);
    const subtotalEl = document.getElementById('subtotal-' + index);
    const totalEl = document.getElementById('cartTotal');
    if (qtyEl) qtyEl.textContent = newQty;
    if (subtotalEl) subtotalEl.textContent = '$' + item.subtotal;
    if (totalEl) totalEl.textContent = '$' + cartTotal();
}

function _refreshBadge() {
    const count = cartCount();
    const badge = document.getElementById('cartNavBadge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? '' : 'none';
    }
    const mobileCount = document.getElementById('mobileCartSummaryCount');
    if (mobileCount) mobileCount.textContent = count;
    const mobileSummary = document.getElementById('mobileCartSummary');
    if (mobileSummary) mobileSummary.classList.toggle('d-none', count <= 0);
}

// ── 購物車頁渲染 ──────────────────────────

function _renderItem(item, index) {
    const card = document.createElement('div');
    card.className = 'card card-dark mb-3 cart-item';
    card.dataset.index = index;
    card.dataset.unitPrice = item.unit_price;

    const cardBody = document.createElement('div');
    cardBody.className = 'card-body d-flex align-items-center gap-3';

    const infoDiv = document.createElement('div');
    infoDiv.className = 'flex-grow-1';

    const nameH6 = document.createElement('h6');
    nameH6.className = 'text-white mb-1';
    nameH6.textContent = item.name;
    infoDiv.appendChild(nameH6);

    if (item.options && item.options.length) {
        const optsDiv = document.createElement('div');
        optsDiv.className = 'text-secondary small mb-1';
        item.options.forEach(function (o) {
            const span = document.createElement('span');
            span.className = 'me-2';
            span.textContent = '+ ' + o.name;
            optsDiv.appendChild(span);
        });
        infoDiv.appendChild(optsDiv);
    }

    const priceSpan = document.createElement('span');
    priceSpan.className = 'text-yellow fw-bold';
    priceSpan.textContent = '$' + item.unit_price;
    infoDiv.appendChild(priceSpan);

    cardBody.appendChild(infoDiv);

    const qtyDiv = document.createElement('div');
    qtyDiv.className = 'd-flex align-items-center gap-2';

    const minusBtn = document.createElement('button');
    minusBtn.className = 'btn btn-outline-light btn-sm rounded-circle qty-btn';
    minusBtn.innerHTML = '<i class="bi bi-dash"></i>';
    minusBtn.addEventListener('click', function () { cartUpdateQty(index, -1); });
    qtyDiv.appendChild(minusBtn);

    const qtySpan = document.createElement('span');
    qtySpan.className = 'text-white fw-bold';
    qtySpan.id = 'qty-' + index;
    qtySpan.textContent = item.quantity;
    qtyDiv.appendChild(qtySpan);

    const plusBtn = document.createElement('button');
    plusBtn.className = 'btn btn-outline-light btn-sm rounded-circle qty-btn';
    plusBtn.innerHTML = '<i class="bi bi-plus"></i>';
    plusBtn.addEventListener('click', function () { cartUpdateQty(index, 1); });
    qtyDiv.appendChild(plusBtn);

    cardBody.appendChild(qtyDiv);

    const subtotalDiv = document.createElement('div');
    subtotalDiv.className = 'text-end';
    subtotalDiv.style.minWidth = '70px';

    const subtotalVal = document.createElement('div');
    subtotalVal.className = 'text-yellow fw-bold';
    subtotalVal.id = 'subtotal-' + index;
    subtotalVal.textContent = '$' + parseInt(item.subtotal);
    subtotalDiv.appendChild(subtotalVal);
    cardBody.appendChild(subtotalDiv);

    const trashBtn = document.createElement('button');
    trashBtn.className = 'btn btn-outline-danger btn-sm';
    trashBtn.innerHTML = '<i class="bi bi-trash"></i>';
    trashBtn.addEventListener('click', function () { cartRemoveItem(index); });
    cardBody.appendChild(trashBtn);

    card.appendChild(cardBody);
    return card;
}

function _renderPriceAlert(priceChanges, orderingReturnUrl) {
    const card = document.createElement('div');
    card.className = 'card card-dark cart-price-alert mb-3';
    card.id = 'cartPriceChangeAlert';

    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';

    const outerFlex = document.createElement('div');
    outerFlex.className = 'd-flex align-items-start gap-3';

    const iconDiv = document.createElement('div');
    iconDiv.className = 'price-alert-icon';
    iconDiv.innerHTML = '<i class="bi bi-exclamation-triangle"></i>';
    outerFlex.appendChild(iconDiv);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'flex-grow-1';

    const titleH6 = document.createElement('h6');
    titleH6.className = 'text-white mb-1';
    titleH6.textContent = '部分餐點價格已更新';
    contentDiv.appendChild(titleH6);

    const descP = document.createElement('p');
    descP.className = 'text-secondary small mb-3';
    descP.textContent = '請確認最新價格後再結帳。';
    contentDiv.appendChild(descP);

    const changeListDiv = document.createElement('div');
    changeListDiv.className = 'price-change-list';

    priceChanges.forEach(function (c) {
        const row = document.createElement('div');
        row.className = 'price-change-row';

        const leftDiv = document.createElement('div');
        const nameSpan = document.createElement('span');
        nameSpan.className = 'text-white';
        nameSpan.textContent = c.name;
        leftDiv.appendChild(nameSpan);
        const qtySpan = document.createElement('span');
        qtySpan.className = 'text-secondary small ms-2';
        qtySpan.textContent = 'x' + c.quantity;
        leftDiv.appendChild(qtySpan);
        row.appendChild(leftDiv);

        const rightDiv = document.createElement('div');
        rightDiv.className = 'price-change-values';
        const oldSpan = document.createElement('span');
        oldSpan.className = 'text-secondary';
        oldSpan.textContent = '$' + c.old_unit_price;
        rightDiv.appendChild(oldSpan);
        const arrowI = document.createElement('i');
        arrowI.className = 'bi bi-arrow-right-short';
        rightDiv.appendChild(arrowI);
        const newSpan = document.createElement('span');
        newSpan.className = 'text-yellow fw-bold';
        newSpan.textContent = '$' + c.new_unit_price;
        rightDiv.appendChild(newSpan);
        row.appendChild(rightDiv);

        changeListDiv.appendChild(row);
    });
    contentDiv.appendChild(changeListDiv);

    const btnDiv = document.createElement('div');
    btnDiv.className = 'd-flex flex-wrap gap-2 mt-3';

    const acceptBtn = document.createElement('button');
    acceptBtn.type = 'button';
    acceptBtn.className = 'btn btn-yellow btn-sm fw-bold';
    acceptBtn.id = 'acceptCartPriceChanges';
    acceptBtn.innerHTML = '<i class="bi bi-check2-circle"></i> 接受最新價格';
    btnDiv.appendChild(acceptBtn);

    const returnLink = document.createElement('a');
    returnLink.href = orderingReturnUrl;
    returnLink.className = 'btn btn-outline-light btn-sm';
    returnLink.innerHTML = '<i class="bi bi-arrow-left"></i> ' + cartI18n('backToOrdering', '返回點餐');
    btnDiv.appendChild(returnLink);

    contentDiv.appendChild(btnDiv);
    outerFlex.appendChild(contentDiv);
    cardBody.appendChild(outerFlex);
    card.appendChild(cardBody);
    return card;
}

function renderCartPage() {
    const listEl = document.getElementById('cartList');
    const footerEl = document.getElementById('cartFooter');
    if (!listEl) return;

    const cart = getCart();
    const orderingReturnUrl = window.ORDERING_RETURN_URL || '/';

    listEl.innerHTML = '';

    if (!cart.length) {
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'text-center py-5';

        const icon = document.createElement('i');
        icon.className = 'bi bi-cart-x fs-1 text-secondary mb-3 d-block';
        emptyDiv.appendChild(icon);

        const p = document.createElement('p');
        p.className = 'text-secondary';
        p.textContent = cartI18n('emptyCart', '購物車是空的');
        emptyDiv.appendChild(p);

        const link = document.createElement('a');
        link.href = orderingReturnUrl;
        link.className = 'btn btn-outline-light';
        link.textContent = cartI18n('orderNow', '去點餐');
        emptyDiv.appendChild(link);

        listEl.appendChild(emptyDiv);
        if (footerEl) footerEl.innerHTML = '';
        return;
    }

    cart.forEach(function (item, index) {
        listEl.appendChild(_renderItem(item, index));
    });

    const paymentUrl = window.PAYMENT_URL || '/payment/';
    if (footerEl) {
        footerEl.innerHTML = '';

        const footerCard = document.createElement('div');
        footerCard.className = 'cart-footer card card-dark mt-4';

        const footerBody = document.createElement('div');
        footerBody.className = 'card-body d-flex justify-content-between align-items-center';

        const totalDiv = document.createElement('div');
        const totalLabel = document.createElement('span');
        totalLabel.className = 'text-secondary';
        totalLabel.textContent = '總金額';
        totalDiv.appendChild(totalLabel);

        const totalH4 = document.createElement('h4');
        totalH4.className = 'text-yellow mb-0';
        totalH4.id = 'cartTotal';
        totalH4.textContent = '$' + cartTotal();
        totalDiv.appendChild(totalH4);

        footerBody.appendChild(totalDiv);

        const payLink = document.createElement('a');
        payLink.href = paymentUrl;
        payLink.className = 'btn btn-yellow px-4 py-2 fw-bold';
        payLink.innerHTML = '<i class="bi bi-credit-card"></i> 前往付款';
        footerBody.appendChild(payLink);

        footerCard.appendChild(footerBody);
        footerEl.appendChild(footerCard);
    }

    // 驗證價格
    postJSON('/api/v1/cart/validate-prices/', { cart: cart })
        .then(function (res) {
            const data = res.data || {};
            if (data.has_changes && (data.price_changes || []).length) {
                const alertEl = _renderPriceAlert(data.price_changes, orderingReturnUrl);
                listEl.insertBefore(alertEl, listEl.firstChild);

                const acceptBtn = document.getElementById('acceptCartPriceChanges');
                if (acceptBtn) {
                    acceptBtn.addEventListener('click', function () {
                        acceptBtn.disabled = true;
                        acceptBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>更新中...';
                        postJSON('/api/v1/cart/sync-prices/', { cart: getCart() })
                            .then(function (syncRes) {
                                const syncData = syncRes.data || {};
                                if (syncData.cart) {
                                    saveCart(syncData.cart);
                                }
                                renderCartPage();
                            })
                            .catch(function (errMsg) {
                                acceptBtn.disabled = false;
                                acceptBtn.innerHTML = '<i class="bi bi-check2-circle"></i> 接受最新價格';
                                showToast(typeof errMsg === 'string' ? errMsg : '價格同步失敗，請重試');
                            });
                    });
                }
            }
        })
        .catch(function (errMsg) {
            showToast(typeof errMsg === 'string' ? errMsg : '無法驗證價格，請重新整理頁面');
        });
}

// ── 全域曝光 ─────────────────────────────

window.getCart = getCart;
window.saveCart = saveCart;
window.cartAddItem = cartAddItem;
window.cartCount = cartCount;
window.cartTotal = cartTotal;

// ── 頁面初始化 ────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('cartList')) {
        renderCartPage();
    }
    _refreshBadge();
});
