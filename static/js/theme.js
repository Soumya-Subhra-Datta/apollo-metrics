function getTheme() {
    return localStorage.getItem('apollo-theme') || 'light';
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('apollo-theme', theme);
    const label = document.getElementById('theme-label');
    const icon = document.getElementById('theme-icon');
    if (label) label.textContent = theme === 'dark' ? 'Light' : 'Dark';
    if (icon) icon.innerHTML = theme === 'dark' ? '&#9788;' : '&#9790;';
}

function toggleTheme() {
    const current = getTheme();
    setTheme(current === 'dark' ? 'light' : 'dark');
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;
    const isOpen = sidebar.classList.toggle('open');
    if (overlay) {
        overlay.classList.toggle('active', isOpen);
    }
}

(function initTheme() {
    setTheme(getTheme());
    const overlay = document.createElement('div');
    overlay.id = 'sidebar-overlay';
    overlay.addEventListener('click', function() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('open');
        }
        overlay.classList.remove('active');
    });
    document.body.appendChild(overlay);
})();
