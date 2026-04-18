document.addEventListener('DOMContentLoaded', function () {
    const pills = document.querySelectorAll('.category-pill');
    const items = document.querySelectorAll('.menu-item');
    const categoryTabsWrapper = document.querySelector('.category-tabs-wrapper');
    const searchInput = document.getElementById('menu-search');

    function applyTabFilter() {
        const activePill = document.querySelector('.category-pill.active');
        const typeId = activePill ? activePill.dataset.typeId : 'all';
        items.forEach(item => {
            item.style.display = (typeId === 'all' || item.dataset.typeId === typeId) ? '' : 'none';
        });
    }

    pills.forEach(pill => {
        pill.addEventListener('click', function () {
            pills.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            applyTabFilter();
        });
    });

    searchInput.addEventListener('input', function () {
        const q = this.value.trim().toLowerCase();
        if (q) {
            categoryTabsWrapper.style.display = 'none';
            items.forEach(item => {
                const name = item.dataset.name.toLowerCase();
                item.style.display = name.includes(q) ? '' : 'none';
            });
        } else {
            categoryTabsWrapper.style.display = '';
            applyTabFilter();
        }
    });
});
