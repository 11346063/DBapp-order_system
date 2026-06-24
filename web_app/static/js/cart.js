/* ─────────────────────────────────────────
   購物車 — localStorage 儲存
   key: 'dbapp_cart'
   item format: { menu_id, name, base_price, options, options_price, unit_price, quantity, subtotal }
   ───────────────────────────────────────── */

const CART_KEY = 'dbapp_cart';

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
    // 更新 UI
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

function _escHtml(str) {
    return String(str == null ? '' : str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function _renderItem(item, index) {
    const opts = (item.options || []).map(function (o) {
        return '<span class="me-2">+ ' + _escHtml(o.name) + '</span>';
    }).join('');
    const optsHtml = opts
        ? '<div class="text-secondary small mb-1">' + opts + '</div>'
        : '';
    return (
        '<div class="card card-dark mb-3 cart-item" data-index="' + index + '" data-unit-price="' + item.unit_price + '">' +
        '<div class="card-body d-flex align-items-center gap-3">' +
        '<div class="flex-grow-1">' +
        '<h6 class="text-white mb-1">' + _escHtml(item.name) + '</h6>' +
        optsHtml +
        '<span class="text-yellow fw-bold">$' + item.unit_price + '</span>' +
        '</div>' +
        '<div class="d-flex align-items-center gap-2">' +
        '<button class="btn btn-outline-light btn-sm rounded-circle qty-btn" onclick="cartUpdateQty(' + index + ', -1)">' +
        '<i class="bi bi-dash"></i></button>' +
        '<span class="text-white fw-bold" id="qty-' + index + '">' + item.quantity + '</span>' +
        '<button class="btn btn-outline-light btn-sm rounded-circle qty-btn" onclick="cartUpdateQty(' + index + ', 1)">' +
        '<i class="bi bi-plus"></i></button>' +
        '</div>' +
        '<div class="text-end" style="min-width:70px">' +
        '<div class="text-yellow fw-bold" id="subtotal-' + index + '">$' + parseInt(item.subtotal) + '</div>' +
        '</div>' +
        '<button class="btn btn-outline-danger btn-sm" onclick="cartRemoveItem(' + index + ')">' +
        '<i class="bi bi-trash"></i></button>' +
        '</div></div>'
    );
}

function _renderPriceAlert(priceChanges, orderingReturnUrl) {
    const rows = priceChanges.map(function (c) {
        return (
            '<div class="price-change-row">' +
            '<div><span class="text-white">' + _escHtml(c.name) + '</span>' +
            '<span class="text-secondary small ms-2">x' + c.quantity + '</span></div>' +
            '<div class="price-change-values">' +
            '<span class="text-secondary">$' + c.old_unit_price + '</span>' +
            '<i class="bi bi-arrow-right-short"></i>' +
            '<span class="text-yellow fw-bold">$' + c.new_unit_price + '</span>' +
            '</div></div>'
        );
    }).join('');
    return (
        '<div class="card card-dark cart-price-alert mb-3" id="cartPriceChangeAlert">' +
        '<div class="card-body">' +
        '<div class="d-flex align-items-start gap-3">' +
        '<div class="price-alert-icon"><i class="bi bi-exclamation-triangle"></i></div>' +
        '<div class="flex-grow-1">' +
        '<h6 class="text-white mb-1">部分餐點價格已更新</h6>' +
        '<p class="text-secondary small mb-3">請確認最新價格後再結帳。</p>' +
        '<div class="price-change-list">' + rows + '</div>' +
        '<div class="d-flex flex-wrap gap-2 mt-3">' +
        '<button type="button" class="btn btn-yellow btn-sm fw-bold" id="acceptCartPriceChanges">' +
        '<i class="bi bi-check2-circle"></i> 接受最新價格</button>' +
        '<a href="' + _escHtml(orderingReturnUrl) + '" class="btn btn-outline-light btn-sm">' +
        '<i class="bi bi-arrow-left"></i> 返回點餐</a>' +
        '</div></div></div></div></div>'
    );
}

function renderCartPage() {
    const listEl = document.getElementById('cartList');
    const footerEl = document.getElementById('cartFooter');
    if (!listEl) return;

    const cart = getCart();
    const orderingReturnUrl = window.ORDERING_RETURN_URL || '/';

    if (!cart.length) {
        listEl.innerHTML =
            '<div class="text-center py-5">' +
            '<i class="bi bi-cart-x fs-1 text-secondary mb-3 d-block"></i>' +
            '<p class="text-secondary">購物車是空的</p>' +
            '<a href="' + _escHtml(orderingReturnUrl) + '" class="btn btn-outline-light">去點餐</a>' +
            '</div>';
        if (footerEl) footerEl.innerHTML = '';
        return;
    }

    listEl.innerHTML = cart.map(_renderItem).join('');

    const paymentUrl = window.PAYMENT_URL || '/payment/';
    if (footerEl) {
        footerEl.innerHTML =
            '<div class="cart-footer card card-dark mt-4">' +
            '<div class="card-body d-flex justify-content-between align-items-center">' +
            '<div><span class="text-secondary">總金額</span>' +
            '<h4 class="text-yellow mb-0" id="cartTotal">$' + cartTotal() + '</h4></div>' +
            '<a href="' + _escHtml(paymentUrl) + '" class="btn btn-yellow px-4 py-2 fw-bold">' +
            '<i class="bi bi-credit-card"></i> 前往付款</a>' +
            '</div></div>';
    }

    // 驗證價格
    postJSON('/api/v1/cart/validate-prices/', { cart: cart })
        .then(function (res) {
            const data = res.data || {};
            if (data.has_changes && (data.price_changes || []).length) {
                const alert = document.createElement('div');
                alert.innerHTML = _renderPriceAlert(data.price_changes, orderingReturnUrl);
                listEl.insertBefore(alert.firstChild, listEl.firstChild);

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
                            .catch(function () {
                                acceptBtn.disabled = false;
                                acceptBtn.innerHTML = '<i class="bi bi-check2-circle"></i> 接受最新價格';
                            });
                    });
                }
            }
        })
        .catch(function () {});
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
