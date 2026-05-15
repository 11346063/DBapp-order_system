let pendingStatusUpdate = null;

function updateOrderStatus(orderId, newStatus) {
    const statusLabels = { 0: '等待中', 1: '完成', 2: '取消' };
    pendingStatusUpdate = { orderId, newStatus };

    const modalEl = document.getElementById('orderStatusConfirmModal');
    const messageEl = document.getElementById('orderStatusConfirmMessage');
    const confirmBtn = document.getElementById('orderStatusConfirmBtn');

    if (!modalEl || !messageEl || !confirmBtn) {
        submitOrderStatusUpdate(orderId, newStatus);
        return;
    }

    messageEl.textContent = `確定要將訂單 #${orderId} 標記為「${statusLabels[newStatus]}」嗎？`;
    confirmBtn.className = newStatus === 2
        ? 'btn btn-outline-danger fw-bold'
        : 'btn btn-yellow fw-bold';
    confirmBtn.innerHTML = newStatus === 2
        ? '<i class="bi bi-x-lg"></i> 確認取消'
        : '<i class="bi bi-check-lg"></i> 確認完成';

    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function submitOrderStatusUpdate(orderId, newStatus) {
    const confirmBtn = document.getElementById('orderStatusConfirmBtn');
    if (confirmBtn) {
        confirmBtn.disabled = true;
    }

    postJSON(`/api/orders/${orderId}/status/`, { status: newStatus }, 'PATCH')
        .then(data => {
            if (data.status === 'success') {
                const modalEl = document.getElementById('orderStatusConfirmModal');
                if (modalEl) {
                    bootstrap.Modal.getInstance(modalEl)?.hide();
                }
                updateStatusBadges(data.data.status_counts);
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
        })
        .catch(() => {})
        .finally(() => {
            if (confirmBtn) {
                confirmBtn.disabled = false;
            }
            pendingStatusUpdate = null;
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

function showEmptyStateIfNeeded() {
    const grid = document.getElementById('staffOrderGrid');
    if (!grid || grid.querySelector('[id^="order-"]')) return;

    const emptyState = document.getElementById('staffOrderEmptyTemplate');
    if (emptyState) {
        emptyState.classList.remove('d-none');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const confirmBtn = document.getElementById('orderStatusConfirmBtn');
    if (!confirmBtn) return;

    confirmBtn.addEventListener('click', () => {
        if (!pendingStatusUpdate) return;
        submitOrderStatusUpdate(
            pendingStatusUpdate.orderId,
            pendingStatusUpdate.newStatus
        );
    });
});
