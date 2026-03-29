let currentItem = null;
let currentQty = 1;

function openItemDetail(menuId) {
    fetch(`/api/menu/${menuId}/`)
        .then(res => res.json())
        .then(data => {
            currentItem = data;
            currentQty = 1;
            fillDetail(data);

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
    const setContent = (prefix) => {
        const nameEl = document.getElementById(`${prefix}ItemName`);
        const priceEl = document.getElementById(`${prefix}ItemPrice`);
        const infoEl = document.getElementById(`${prefix}ItemInfo`);
        const qtyEl = document.getElementById(`${prefix}Qty`);
        const optEl = document.getElementById(`${prefix}Options`);

        if (nameEl) nameEl.textContent = data.name;
        if (priceEl) priceEl.textContent = `$${data.price}`;
        if (infoEl) {
            infoEl.textContent = data.info || '';
            infoEl.style.display = data.info ? '' : 'none';
        }
        if (qtyEl) qtyEl.textContent = '1';

        if (optEl) {
            if (data.options && data.options.length > 0) {
                optEl.innerHTML = data.options.map(opt => `
                    <label class="option-check">
                        <input type="checkbox" value="${opt.id}" data-price="${opt.price}">
                        <span>${opt.name}</span>
                        <span class="option-price">+$${opt.price}</span>
                    </label>
                `).join('');
                optEl.style.display = '';
            } else {
                optEl.innerHTML = '';
                optEl.style.display = 'none';
            }
        }
    };

    setContent('offcanvas');
    setContent('modal');
}

function changeQty(delta) {
    currentQty = Math.max(1, currentQty + delta);
    const offQty = document.getElementById('offcanvasQty');
    const modQty = document.getElementById('modalQty');
    if (offQty) offQty.textContent = currentQty;
    if (modQty) modQty.textContent = currentQty;
}

function getSelectedOptions() {
    const container = window.innerWidth < 768
        ? document.getElementById('offcanvasOptions')
        : document.getElementById('modalOptions');

    if (!container) return [];

    const checked = container.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checked).map(cb => ({
        id: parseInt(cb.value),
        name: cb.parentElement.querySelector('span').textContent,
        price: parseInt(cb.dataset.price),
    }));
}

function addToCart() {
    if (!currentItem) return;

    const selectedOptions = getSelectedOptions();

    postJSON('/cart/add/', {
        menu_id: currentItem.id,
        name: currentItem.name,
        price: currentItem.price,
        quantity: currentQty,
        options: selectedOptions,
    }).then(data => {
        if (data.success) {
            // Update cart badge
            const badge = document.querySelector('.navbar .badge');
            if (badge) {
                badge.textContent = data.cart_count;
                badge.style.display = '';
            } else {
                // Reload to show badge
                location.reload();
            }

            // Close modal/offcanvas
            const offcanvasEl = document.getElementById('itemOffcanvas');
            const modalEl = document.getElementById('itemModal');
            if (window.innerWidth < 768 && offcanvasEl) {
                bootstrap.Offcanvas.getInstance(offcanvasEl)?.hide();
            } else if (modalEl) {
                bootstrap.Modal.getInstance(modalEl)?.hide();
            }
        }
    });
}
