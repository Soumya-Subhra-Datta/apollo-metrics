async function apiCall(url, method, body) {
    try {
        const options = { method, headers: { 'Content-Type': 'application/json' } };
        if (body) options.body = JSON.stringify(body);
        const res = await fetch(url, options);
        const data = await res.json();
        return { ok: res.ok, status: res.status, data };
    } catch (err) {
        return { ok: false, status: 0, data: { error: 'Network error. Please check your connection.' } };
    }
}

function showError(msg) {
    const el = document.getElementById('error-message');
    if (el) el.innerHTML = `<div class="alert alert-error">${msg}</div>`;
}

function showSuccess(msg) {
    const el = document.getElementById('error-message');
    if (el) el.innerHTML = `<div class="alert alert-success">${msg}</div>`;
}

// Register
const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const full_name = document.getElementById('full_name').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirm_password = document.getElementById('confirm_password').value;

        if (!full_name || !email || !password) {
            showError('All fields are required.');
            return;
        }
        if (password !== confirm_password) {
            showError('Passwords do not match.');
            return;
        }
        if (password.length < 6) {
            showError('Password must be at least 6 characters.');
            return;
        }

        const { ok, data } = await apiCall('/api/auth/register', 'POST', { full_name, email, password, confirm_password });
        if (ok) {
            showSuccess('Registration successful! Redirecting...');
            setTimeout(() => { window.location.href = '/dashboard'; }, 1000);
        } else {
            showError(data.error || 'Registration failed.');
        }
    });
}

// Login
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        if (!email || !password) {
            showError('Email and password are required.');
            return;
        }

        const { ok, data } = await apiCall('/api/auth/login', 'POST', { email, password });
        if (ok) {
            showSuccess('Login successful! Redirecting...');
            setTimeout(() => { window.location.href = '/dashboard'; }, 1000);
        } else {
            showError(data.error || 'Invalid email or password.');
        }
    });
}
