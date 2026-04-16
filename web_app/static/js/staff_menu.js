// 員工/管理員菜單管理功能
// 依賴 detail.js 的 currentItem 變數與 window.URLS、window.TYPES

let staffMenuMode = null; // 'edit' | 'create'

function toggleItemStatus() {
    if (!currentItem) return;

    const url = window.URLS.menuToggle.replace('{id}', currentItem.id);
    postJSON(url, {}).then(data => {
        currentItem.status = data.status;
        ['offcanvas', 'modal'].forEach(prefix => {
            const badge = document.getElementById(`${prefix}StatusBadge`);
            if (!badge) return;
            if (data.status) {
                badge.textContent = '上架中';
                badge.className = 'badge fs-6 px-3 py-2 bg-success';
            } else {
                badge.textContent = '已下架';
                badge.className = 'badge fs-6 px-3 py-2 bg-danger';
            }
        });
        _refreshCardBadge(currentItem.id, data.status);
    }).catch(errMsg => {
        _showDetailError(errMsg);
    });
}

function _showDetailError(msg) {
    ['offcanvas', 'modal'].forEach(prefix => {
        const badge = document.getElementById(`${prefix}StatusBadge`);
        if (!badge) return;
        const origClass = badge.className;
        const origText = badge.textContent;
        badge.className = 'badge fs-6 px-3 py-2 bg-warning text-dark';
        badge.textContent = msg || '發生錯誤，請再試一次';
        setTimeout(() => {
            badge.className = origClass;
            badge.textContent = origText;
        }, 3000);
    });
}

function _refreshCardBadge(menuId, status) {
    // 找到對應的卡片，重新渲染下架標示
    const cards = document.querySelectorAll('.menu-item');
    cards.forEach(card => {
        const btn = card.querySelector('.item-card');
        if (!btn) return;
        const onclickAttr = btn.getAttribute('onclick') || '';
        if (!onclickAttr.includes(`(${menuId})`)) return;

        const placeholder = card.querySelector('.card-img-top-placeholder');
        if (!placeholder) return;

        let existingBadge = placeholder.querySelector('.badge.bg-danger');
        if (!status) {
            btn.classList.add('item-card-inactive');
            if (!existingBadge) {
                const badge = document.createElement('span');
                badge.className = 'badge bg-danger position-absolute top-0 start-0 m-2';
                badge.textContent = '已下架';
                placeholder.appendChild(badge);
            }
        } else {
            btn.classList.remove('item-card-inactive');
            if (existingBadge) existingBadge.remove();
        }
    });
}

function openEditForm() {
    if (!currentItem) return;
    staffMenuMode = 'edit';

    document.getElementById('staffMenuModalTitle').textContent = '編輯品項';
    document.getElementById('staffMenuSubmitBtn').textContent = '儲存';
    document.getElementById('staffMenuError').classList.add('d-none');

    _populateTypeSelect(currentItem.type_id);
    document.getElementById('staffMenuName').value = currentItem.name;
    document.getElementById('staffMenuPrice').value = currentItem.price;
    document.getElementById('staffMenuInfo').value = currentItem.info || '';
    document.getElementById('staffMenuRemark').value = currentItem.remark || '';

    // 關閉詳情 modal/offcanvas，開啟編輯 modal
    _closeDetailPanel();
    const modal = new bootstrap.Modal(document.getElementById('staffMenuModal'));
    modal.show();
}

function openCreateForm() {
    staffMenuMode = 'create';

    document.getElementById('staffMenuModalTitle').textContent = '新增品項';
    document.getElementById('staffMenuSubmitBtn').textContent = '新增';
    document.getElementById('staffMenuError').classList.add('d-none');

    _populateTypeSelect(null);
    document.getElementById('staffMenuName').value = '';
    document.getElementById('staffMenuPrice').value = '';
    document.getElementById('staffMenuInfo').value = '';
    document.getElementById('staffMenuRemark').value = '';

    const modal = new bootstrap.Modal(document.getElementById('staffMenuModal'));
    modal.show();
}

function _populateTypeSelect(selectedTypeId) {
    const select = document.getElementById('staffMenuType');
    select.innerHTML = (window.TYPES || []).map(t =>
        `<option value="${t.id}"${t.id === selectedTypeId ? ' selected' : ''}>${t.name}</option>`
    ).join('');
}

function submitStaffMenuForm() {
    const errorEl = document.getElementById('staffMenuError');
    errorEl.classList.add('d-none');

    const name = document.getElementById('staffMenuName').value.trim();
    const price = document.getElementById('staffMenuPrice').value;
    const typeId = parseInt(document.getElementById('staffMenuType').value);
    const info = document.getElementById('staffMenuInfo').value.trim();
    const remark = document.getElementById('staffMenuRemark').value.trim();

    const priceInt = parseInt(price);
    if (!name || price === '') {
        errorEl.textContent = '名稱與價格為必填';
        errorEl.classList.remove('d-none');
        return;
    }
    if (isNaN(priceInt) || priceInt < 0) {
        errorEl.textContent = '價格不能為負數';
        errorEl.classList.remove('d-none');
        return;
    }

    const payload = { name, price: priceInt, type_id: typeId, info, remark };

    let url, successHandler;
    if (staffMenuMode === 'edit' && currentItem) {
        url = window.URLS.menuEdit.replace('{id}', currentItem.id);
        successHandler = (data) => {
            // 更新 currentItem
            Object.assign(currentItem, data);
            // 更新卡片上的品名與金額
            _refreshCardInfo(data.id, data.name, data.price);
            bootstrap.Modal.getInstance(document.getElementById('staffMenuModal'))?.hide();
        };
    } else {
        url = window.URLS.menuCreate;
        successHandler = (data) => {
            // 新增卡片到 DOM
            _appendNewCard(data);
            bootstrap.Modal.getInstance(document.getElementById('staffMenuModal'))?.hide();
        };
    }

    postJSON(url, payload).then(data => {
        if (data.error) {
            errorEl.textContent = data.error;
            errorEl.classList.remove('d-none');
        } else {
            successHandler(data);
        }
    }).catch(errMsg => {
        errorEl.textContent = errMsg || '發生錯誤，請再試一次';
        errorEl.classList.remove('d-none');
    });
}

function _refreshCardInfo(menuId, newName, newPrice) {
    document.querySelectorAll('.menu-item').forEach(card => {
        const btn = card.querySelector('.item-card');
        if (!btn) return;
        if (!(btn.getAttribute('onclick') || '').includes(`(${menuId})`)) return;
        const titleEl = card.querySelector('.card-title');
        const priceEl = card.querySelector('.badge-yellow');
        if (titleEl) titleEl.textContent = newName;
        if (priceEl) priceEl.textContent = `$${newPrice}`;
    });
}

function _appendNewCard(item) {
    const grid = document.getElementById('menuGrid');
    if (!grid) return;

    const col = document.createElement('div');
    col.className = 'col-6 col-md-4 col-lg-3 menu-item';
    col.dataset.typeId = item.type_id;
    col.innerHTML = `
        <div class="card card-dark h-100 item-card" role="button" onclick="openItemDetail(${item.id})">
            <div class="card-img-top-placeholder d-flex align-items-center justify-content-center position-relative">
                <i class="bi bi-egg-fried fs-1 text-secondary"></i>
            </div>
            <div class="card-body p-3">
                <h6 class="card-title mb-2 text-white">${item.name}</h6>
                <span class="badge badge-yellow">$${item.price}</span>
            </div>
        </div>
    `;
    grid.appendChild(col);

    // 隱藏「目前沒有餐點」訊息（若存在）
    const empty = grid.nextElementSibling;
    if (empty && empty.classList.contains('text-center')) {
        empty.style.display = 'none';
    }
}

function _closeDetailPanel() {
    const offcanvasEl = document.getElementById('itemOffcanvas');
    const modalEl = document.getElementById('itemModal');
    if (offcanvasEl) bootstrap.Offcanvas.getInstance(offcanvasEl)?.hide();
    if (modalEl) bootstrap.Modal.getInstance(modalEl)?.hide();
}
