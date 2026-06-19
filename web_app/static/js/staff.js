let pendingStatusUpdate = null;
let pendingAcceptOrderId = null;
let pendingCancelOrderId = null;

function reprintOrder(orderId) {
    postJSON(`/api/orders/${orderId}/reprint/`, {}, 'POST')
        .then(data => {
            if (data.status === 'success') {
                alert('已加入列印佇列');
            }
        })
        .catch(errMsg => { alert(errMsg || '重印失敗，請重試'); });
}

function updateOrderStatus(orderId, newStatus) {
    const statusLabels = { 3: '已完成', 4: '已取消' };
    pendingStatusUpdate = { orderId, newStatus };

    const modalEl = document.getElementById('orderStatusConfirmModal');
    const messageEl = document.getElementById('orderStatusConfirmMessage');
    const confirmBtn = document.getElementById('orderStatusConfirmBtn');

    if (!modalEl || !messageEl || !confirmBtn) {
        submitOrderStatusUpdate(orderId, newStatus);
        return;
    }

    messageEl.textContent = `確定要將訂單 #${orderId} 標記為「${statusLabels[newStatus] || newStatus}」嗎？`;
    confirmBtn.className = newStatus === 4
        ? 'btn btn-outline-danger fw-bold'
        : 'btn btn-yellow fw-bold';
    confirmBtn.innerHTML = newStatus === 4
        ? '<i class="bi bi-x-lg"></i> 確認取消'
        : '<i class="bi bi-check-lg"></i> 確認完成';

    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function submitOrderStatusUpdate(orderId, newStatus) {
    const confirmBtn = document.getElementById('orderStatusConfirmBtn');
    if (confirmBtn) confirmBtn.disabled = true;

    postJSON(`/api/orders/${orderId}/status/`, { status: newStatus }, 'PATCH')
        .then(data => {
            if (data.status === 'success') {
                bootstrap.Modal.getInstance(document.getElementById('orderStatusConfirmModal'))?.hide();
                updateStatusBadges(data.data.status_counts);
                removeOrderCard(orderId);
            }
        })
        .catch(() => {})
        .finally(() => {
            if (confirmBtn) confirmBtn.disabled = false;
            pendingStatusUpdate = null;
        });
}

function notifyReady(orderId) {
    pendingStatusUpdate = { orderId, newStatus: 'ready' };

    const modalEl = document.getElementById('orderStatusConfirmModal');
    const messageEl = document.getElementById('orderStatusConfirmMessage');
    const confirmBtn = document.getElementById('orderStatusConfirmBtn');

    if (!modalEl || !messageEl || !confirmBtn) {
        submitNotifyReady(orderId);
        return;
    }

    messageEl.textContent = `確定要通知顧客訂單 #${orderId} 可以取餐了嗎？`;
    confirmBtn.className = 'btn btn-info fw-bold text-dark';
    confirmBtn.innerHTML = '<i class="bi bi-bell"></i> 確認通知取餐';

    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function submitNotifyReady(orderId) {
    const confirmBtn = document.getElementById('orderStatusConfirmBtn');
    if (confirmBtn) confirmBtn.disabled = true;

    postJSON(`/api/orders/${orderId}/ready/`, {})
        .then(data => {
            if (data.status === 'success') {
                bootstrap.Modal.getInstance(document.getElementById('orderStatusConfirmModal'))?.hide();
                updateStatusBadges(data.data.status_counts);
                removeOrderCard(orderId);
            }
        })
        .catch(() => {})
        .finally(() => {
            if (confirmBtn) confirmBtn.disabled = false;
            pendingStatusUpdate = null;
        });
}

function acceptOrder(orderId) {
    pendingAcceptOrderId = orderId;

    const modalEl = document.getElementById('orderAcceptModal');
    const messageEl = document.getElementById('orderAcceptMessage');
    if (!modalEl) return;

    if (messageEl) messageEl.textContent = `訂單 #${orderId}：請輸入預估等待時間後接單。`;

    const waitInput = document.getElementById('acceptWaitMinutes');
    if (waitInput) waitInput.value = 20;

    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function submitAcceptOrder() {
    const orderId = pendingAcceptOrderId;
    if (!orderId) return;

    const waitInput = document.getElementById('acceptWaitMinutes');
    const minutes = waitInput ? parseInt(waitInput.value, 10) : NaN;

    if (isNaN(minutes) || minutes < 1 || minutes > 180) {
        alert('請輸入 1 到 180 之間的等待時間');
        return;
    }

    const confirmBtn = document.getElementById('orderAcceptConfirmBtn');
    if (confirmBtn) confirmBtn.disabled = true;

    postJSON(`/api/orders/${orderId}/accept/`, { estimated_wait_minutes: minutes })
        .then(data => {
            if (data.status === 'success') {
                bootstrap.Modal.getInstance(document.getElementById('orderAcceptModal'))?.hide();
                updateStatusBadges(data.data.status_counts);
                removeOrderCard(orderId);
            }
        })
        .catch(errMsg => {
            alert(errMsg || '接單失敗，請重試');
        })
        .finally(() => {
            if (confirmBtn) confirmBtn.disabled = false;
            pendingAcceptOrderId = null;
        });
}

function cancelOrder(orderId) {
    pendingCancelOrderId = orderId;
    const modalEl = document.getElementById('orderCancelReasonModal');
    if (!modalEl) { submitCancelOrder(); return; }
    const msgEl = document.getElementById('orderCancelReasonMessage');
    if (msgEl) msgEl.textContent = `確定要取消訂單 #${orderId} 嗎？`;
    const input = document.getElementById('cancelReasonInput');
    if (input) input.value = '';
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function submitCancelOrder() {
    const orderId = pendingCancelOrderId;
    if (!orderId) return;
    const reason = (document.getElementById('cancelReasonInput')?.value || '').trim();
    const confirmBtn = document.getElementById('orderCancelConfirmBtn');
    if (confirmBtn) confirmBtn.disabled = true;

    postJSON(`/api/orders/${orderId}/status/`, { status: 4, cancel_reason: reason }, 'PATCH')
        .then(data => {
            if (data.status === 'success') {
                bootstrap.Modal.getInstance(document.getElementById('orderCancelReasonModal'))?.hide();
                updateStatusBadges(data.data.status_counts);
                removeOrderCard(orderId);
            }
        })
        .catch(errMsg => { alert(errMsg || '取消失敗，請重試'); })
        .finally(() => {
            if (confirmBtn) confirmBtn.disabled = false;
            pendingCancelOrderId = null;
        });
}

function updateStatusBadges(statusCounts) {
    if (!statusCounts) return;
    Object.entries(statusCounts).forEach(([status, count]) => {
        document.querySelectorAll(`[data-status-count="${status}"]`).forEach(badge => {
            badge.textContent = count;
        });
    });
}

function removeOrderCard(orderId) {
    if (window.STAFF_VIEW_MODE === 'kanban') {
        // Kanban: reload so all columns reflect the new status
        setTimeout(() => location.reload(), 300);
        return;
    }
    const card = document.getElementById(`order-${orderId}`);
    if (card) {
        card.style.transition = 'opacity 0.3s';
        card.style.opacity = '0';
        setTimeout(() => {
            card.remove();
            showEmptyStateIfNeeded();
        }, 300);
    }
}

function showEmptyStateIfNeeded() {
    const grid = document.getElementById('staffOrderGrid');
    if (!grid || grid.querySelector('[id^="order-"]')) return;

    const emptyState = document.getElementById('staffOrderEmptyTemplate');
    if (emptyState) emptyState.classList.remove('d-none');
}

// ===== Card Collapse =====

function toggleCardCollapse(orderId) {
    const body = document.getElementById(`card-body-${orderId}`);
    const icon = document.getElementById(`collapse-icon-${orderId}`);
    if (!body) return;

    const isCollapsed = body.classList.contains('d-none');
    if (isCollapsed) {
        body.classList.remove('d-none');
        icon && icon.classList.remove('collapsed');
        localStorage.setItem(`order-collapse-${orderId}`, 'open');
    } else {
        body.classList.add('d-none');
        icon && icon.classList.add('collapsed');
        localStorage.setItem(`order-collapse-${orderId}`, 'closed');
    }
}

function restoreCollapseStates(defaultCollapsed) {
    document.querySelectorAll('[data-order-id]').forEach(el => {
        const orderId = el.dataset.orderId;
        const body = document.getElementById(`card-body-${orderId}`);
        const icon = document.getElementById(`collapse-icon-${orderId}`);
        const saved = localStorage.getItem(`order-collapse-${orderId}`);
        const shouldCollapse = saved ? saved === 'closed' : defaultCollapsed;
        if (shouldCollapse && body) {
            body.classList.add('d-none');
            icon && icon.classList.add('collapsed');
        }
    });
}

// ===== Kanban Drag & Drop =====

function initKanban() {
    // Only adjacent forward transitions are valid
    const VALID_TRANSITIONS = { '0': '1', '1': '2', '2': '3' };

    document.querySelectorAll('.kanban-cards').forEach(container => {
        Sortable.create(container, {
            group: 'kanban',
            animation: 150,
            ghostClass: 'sortable-ghost',
            filter: '.kanban-empty',
            onEnd(evt) {
                const fromStatus = evt.from.dataset.status;
                const toStatus = evt.to.dataset.status;
                const orderId = parseInt(evt.item.dataset.orderId, 10);

                if (fromStatus === toStatus) return;

                // Always snap back — API success triggers removeOrderCard
                revertDrag(evt.item, evt.from, evt.oldIndex);

                if (VALID_TRANSITIONS[fromStatus] !== toStatus) return;

                if (fromStatus === '0') {
                    acceptOrder(orderId);
                } else if (fromStatus === '1') {
                    notifyReady(orderId);
                } else if (fromStatus === '2') {
                    updateOrderStatus(orderId, 3);
                }
            },
        });
    });
}

function revertDrag(item, fromEl, oldIndex) {
    const siblings = fromEl.children;
    if (oldIndex < siblings.length) {
        fromEl.insertBefore(item, siblings[oldIndex]);
    } else {
        fromEl.appendChild(item);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const confirmBtn = document.getElementById('orderStatusConfirmBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
            if (!pendingStatusUpdate) return;
            if (pendingStatusUpdate.newStatus === 'ready') {
                submitNotifyReady(pendingStatusUpdate.orderId);
            } else {
                submitOrderStatusUpdate(
                    pendingStatusUpdate.orderId,
                    pendingStatusUpdate.newStatus
                );
            }
        });
    }

    const acceptConfirmBtn = document.getElementById('orderAcceptConfirmBtn');
    if (acceptConfirmBtn) {
        acceptConfirmBtn.addEventListener('click', submitAcceptOrder);
    }

    const isKanban = window.STAFF_VIEW_MODE === 'kanban';
    restoreCollapseStates(isKanban);
    if (isKanban && typeof Sortable !== 'undefined') {
        initKanban();
    }
});
