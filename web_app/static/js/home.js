document.addEventListener('DOMContentLoaded', function () {
    const pills = document.querySelectorAll('.category-pill');
    const items = document.querySelectorAll('.menu-item');

    pills.forEach(pill => {
        pill.addEventListener('click', function () {
            pills.forEach(p => p.classList.remove('active'));
            this.classList.add('active');

            const typeId = this.dataset.typeId;

            items.forEach(item => {
                if (typeId === 'all' || item.dataset.typeId === typeId) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
});
