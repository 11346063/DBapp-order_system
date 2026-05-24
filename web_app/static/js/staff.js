let pendingStatusUpdate = null;
let pendingAcceptOrderId = null;

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

function updateStatusBadges(statusCounts) {
    if (!statusCounts) return;
    Object.entries(statusCounts).forEach(([status, count]) => {
        document.querySelectorAll(`[data-status-count="${status}"]`).forEach(badge => {
            badge.textContent = count;
        });
    });
}

function removeOrderCard(orderId) {
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
});
