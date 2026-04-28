function updateOrderStatus(orderId, newStatus) {
    const statusLabels = { 0: '等待中', 1: '完成', 2: '取消' };
    if (!confirm(`確定要將此訂單標記為「${statusLabels[newStatus]}」嗎？`)) return;

    postJSON(`/staff/orders/${orderId}/status/`, { status: newStatus })
        .then(data => {
            if (data.success) {
                updateStatusBadges(data.status_counts);
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
        .catch(() => {});
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
