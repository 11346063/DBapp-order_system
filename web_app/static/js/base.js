/* ===== CSRF Token ===== */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

function syncBrowserTimezone() {
    if (!window.Intl || !Intl.DateTimeFormat) return;

    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!timezone) return;
    if (
        localStorage.getItem('dbapp_timezone') === timezone &&
        sessionStorage.getItem('dbapp_timezone_synced') === timezone
    ) {
        return;
    }

    fetch('/api/v1/preferences/timezone/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ timezone: timezone }),
    }).then(function (res) {
        if (res.ok) {
            localStorage.setItem('dbapp_timezone', timezone);
            sessionStorage.setItem('dbapp_timezone_synced', timezone);
        }
    }).catch(function () {
        // Timezone sync should never block page usage.
    });
}

function postJSON(url, data, method = 'POST') {
    return fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify(data),
    }).then(res =>
        res.json().then(body => {
            if (!res.ok) return Promise.reject(body.message || '伺服器發生錯誤');
            return body;
        })
    );
}

function postFormData(url, formData, method = 'POST') {
    return fetch(url, {
        method: method,
        headers: {
            'X-CSRFToken': csrftoken,
        },
        body: formData,
    }).then(res =>
        res.json().then(body => {
            if (!res.ok) return Promise.reject(body.message || '伺服器發生錯誤');
            return body;
        })
    );
}

/* ===== Theme Toggle ===== */
function getStoredTheme() {
    return localStorage.getItem('theme') || 'dark';
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);

    const iconLight = document.querySelector('.theme-icon-light');
    const iconDark = document.querySelector('.theme-icon-dark');

    if (iconLight && iconDark) {
        if (theme === 'light') {
            iconLight.style.display = 'inline';
            iconDark.style.display = 'none';
        } else {
            iconLight.style.display = 'none';
            iconDark.style.display = 'inline';
        }
    }
}

// When DOM is ready: apply theme icons + bind toggle button
document.addEventListener('DOMContentLoaded', function () {
    applyTheme(getStoredTheme());
    syncBrowserTimezone();

    // Bind theme toggle button click
    var btn = document.getElementById('themeToggle');
    if (btn) {
        btn.addEventListener('click', toggleTheme);
    }

    document.querySelectorAll('[data-auto-dismiss="success"]').forEach(function (alertEl) {
        setTimeout(function () {
            if (window.bootstrap && window.bootstrap.Alert) {
                window.bootstrap.Alert.getOrCreateInstance(alertEl).close();
            } else {
                alertEl.remove();
            }
        }, 3000);
    });
});

/* ===== Shared Utilities ===== */
function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
}

/**
 * 顯示 Bootstrap Toast 彈出通知。
 * @param {string} message - 要顯示的訊息
 * @param {'danger'|'warning'|'success'} type - Toast 顏色類型，預設 danger（紅色）
 */
function showToast(message, type) {
    const safeType = ['danger', 'warning', 'success'].includes(type) ? type : 'danger';
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const iconMap = { danger: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', success: 'bi-check-circle-fill' };

    const toastEl = document.createElement('div');
    toastEl.className = 'toast align-items-center text-bg-' + safeType + ' border-0 shadow';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    const row = document.createElement('div');
    row.className = 'd-flex';

    const body = document.createElement('div');
    body.className = 'toast-body fw-semibold';
    const iconEl = document.createElement('i');
    iconEl.className = 'bi ' + iconMap[safeType] + ' me-2';
    body.appendChild(iconEl);
    body.appendChild(document.createTextNode(String(message || '發生錯誤，請稍後再試')));

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'btn-close btn-close-white me-2 m-auto';
    closeBtn.setAttribute('data-bs-dismiss', 'toast');
    closeBtn.setAttribute('aria-label', 'Close');

    row.appendChild(body);
    row.appendChild(closeBtn);
    toastEl.appendChild(row);
    container.appendChild(toastEl);

    const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', function () { toastEl.remove(); });
}
