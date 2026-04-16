function updateOrderStatus(orderId, newStatus) {
    const statusLabels = { 0: '等待中', 1: '完成', 2: '取消' };
    if (!confirm(`確定要將此訂單標記為「${statusLabels[newStatus]}」嗎？`)) return;

    postJSON(`/staff/orders/${orderId}/status/`, { status: newStatus })
        .then(data => {
            if (data.success) {
                const card = document.getElementById(`order-${orderId}`);
                if (card) {
                    card.style.transition = 'opacity 0.3s';
                    card.style.opacity = '0';
                    setTimeout(() => card.remove(), 300);
                }
            }
        })
        .catch(() => {});
}
