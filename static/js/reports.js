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

function logout() { apiCall('/api/auth/logout', 'GET').then(() => { window.location.href = '/login'; }); }
async function loadDatasets() {
    const { ok, data } = await apiCall('/api/uploads', 'GET');
    if (!ok) { if (data.error && data.error.includes('Authentication')) { window.location.href = '/login'; } return; }
    const select = document.getElementById('dataset-select');
    if (data.uploads) {
        data.uploads.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = `${u.file_name} (${u.total_rows} rows)`;
            select.appendChild(opt);
        });
    }
}

async function loadUserInfo() {
    const { ok, data } = await apiCall('/api/auth/me', 'GET');
    if (ok && data.user) {
        document.getElementById('sidebar-avatar').textContent = (data.user.full_name || 'U')[0].toUpperCase();
        document.getElementById('sidebar-name').textContent = data.user.full_name;
        document.getElementById('sidebar-email').textContent = data.user.email;
    }
}

async function generateReport() {
    const uploadId = document.getElementById('dataset-select').value;
    if (!uploadId) { alert('Please select a dataset.'); return; }

    const statusEl = document.getElementById('report-status');
    statusEl.innerHTML = '<div class="alert alert-info">Generating report... This may take a moment.</div>';

    const { ok, data } = await apiCall('/api/reports/generate', 'POST', { upload_id: uploadId });
    if (!ok) {
        statusEl.innerHTML = `<div class="alert alert-error">${data.error || 'Report generation failed.'}</div>`;
        return;
    }

    statusEl.innerHTML = `<div class="alert alert-success">Report generated successfully! <a href="/reports" style="color:var(--accent);font-weight:600;">View in reports list</a></div>`;
    loadReports();
}

async function loadReports() {
    const el = document.getElementById('reports-list');
    el.innerHTML = '<div class="loading"><div class="spinner"></div>Loading...</div>';

    const { ok, data } = await apiCall('/api/reports', 'GET');
    if (!ok) {
        el.innerHTML = `<p style="color:var(--text-muted);padding:20px;">${data.error || 'Failed to load reports.'}</p>`;
        return;
    }

    if (!data.reports || data.reports.length === 0) {
        el.innerHTML = '<p style="color:var(--text-muted);padding:20px;text-align:center;">No reports generated yet.</p>';
        return;
    }

    let html = '<table><thead><tr><th>Report Name</th><th>Dataset</th><th>Created</th><th>Action</th></tr></thead><tbody>';
    data.reports.forEach(r => {
        html += `<tr>
            <td>${r.report_name || r.report_name}</td>
            <td>${r.file_name || 'N/A'}</td>
            <td>${r.created_at || ''}</td>
            <td><a href="/api/reports/download/${r.id}" class="btn btn-secondary btn-sm">Download</a></td>
        </tr>`;
    });
    html += '</tbody></table>';
    el.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', () => { loadDatasets(); loadUserInfo(); loadReports(); });
