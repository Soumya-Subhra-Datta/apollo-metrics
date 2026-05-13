async function apiCall(url, method, body) {
    try {
        const options = { method, headers: { 'Content-Type': 'application/json' } };
        if (body) options.body = JSON.stringify(body);
        const res = await fetch(url, options);
        const data = await res.json();
        return { ok: res.ok, data };
    } catch (err) {
        return { ok: false, data: { error: 'Network error.' } };
    }
}

function logout() {
    apiCall('/api/auth/logout', 'GET').then(() => {
        window.location.href = '/login';
    });
}

async function loadDashboard() {
    const { ok, data } = await apiCall('/api/dashboard/summary', 'GET');
    if (!ok) {
        if (data.error && data.error.includes('Authentication')) {
            window.location.href = '/login';
            return;
        }
        return;
    }

    document.getElementById('sidebar-avatar').textContent = (data.user.full_name || 'U')[0].toUpperCase();
    document.getElementById('sidebar-name').textContent = data.user.full_name;
    document.getElementById('sidebar-email').textContent = data.user.email;
    document.getElementById('user-name').textContent = data.user.full_name;

    document.getElementById('stat-uploads').textContent = data.stats.total_uploads;
    document.getElementById('stat-queries').textContent = data.stats.total_queries;
    document.getElementById('stat-models').textContent = data.stats.total_models;
    document.getElementById('stat-reports').textContent = data.stats.total_reports;

    const uploadsEl = document.getElementById('recent-uploads');
    if (data.recent_uploads && data.recent_uploads.length > 0) {
        let html = '<div class="table-container"><table><thead><tr><th>File</th><th>Rows</th><th>Cols</th><th>Date</th></tr></thead><tbody>';
        data.recent_uploads.forEach(u => {
            html += `<tr><td>${u.file_name}</td><td>${u.total_rows}</td><td>${u.total_columns}</td><td>${u.uploaded_at || ''}</td></tr>`;
        });
        html += '</tbody></table></div>';
        uploadsEl.innerHTML = html;
    } else {
        uploadsEl.innerHTML = '<p style="color:var(--text-muted);padding:20px;text-align:center;">No datasets uploaded yet. <a href="/upload" style="color:var(--accent);">Upload one now</a>.</p>';
    }

    const queriesEl = document.getElementById('recent-queries');
    if (data.recent_queries && data.recent_queries.length > 0) {
        let html = '<div class="table-container"><table><thead><tr><th>Question</th><th>Dataset</th><th>Date</th></tr></thead><tbody>';
        data.recent_queries.forEach(q => {
            html += `<tr><td class="truncate" style="max-width:200px;">${q.question}</td><td>${q.file_name}</td><td>${q.created_at || ''}</td></tr>`;
        });
        html += '</tbody></table></div>';
        queriesEl.innerHTML = html;
    } else {
        queriesEl.innerHTML = '<p style="color:var(--text-muted);padding:20px;text-align:center;">No AI queries yet. <a href="/query" style="color:var(--accent);">Ask a question</a>.</p>';
    }
}

document.addEventListener('DOMContentLoaded', loadDashboard);
