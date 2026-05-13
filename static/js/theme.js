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

(function initTheme() {
    setTheme(getTheme());
})();
