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
async function loadUploads() {
    const { ok, data } = await apiCall('/api/uploads', 'GET');
    if (!ok) {
        if (data.error && data.error.includes('Authentication')) { window.location.href = '/login'; return; }
        document.getElementById('upload-history').innerHTML = `<p style="color:var(--text-muted);padding:20px;">${data.error}</p>`;
        return;
    }
    const el = document.getElementById('upload-history');
    if (!data.uploads || data.uploads.length === 0) {
        el.innerHTML = '<p style="color:var(--text-muted);padding:20px;text-align:center;">No uploads yet.</p>';
        return;
    }
    let html = '<table><thead><tr><th>File Name</th><th>Rows</th><th>Columns</th><th>Uploaded</th><th>Action</th></tr></thead><tbody>';
    data.uploads.forEach(u => {
        html += `<tr><td>${u.file_name}</td><td>${u.total_rows}</td><td>${u.total_columns}</td><td>${u.uploaded_at || ''}</td>`;
        html += `<td><button class="btn btn-danger btn-sm" onclick="deleteUpload(${u.id}, '${u.file_name}')">Delete</button></td></tr>`;
    });
    html += '</tbody></table>';
    el.innerHTML = html;
}

async function deleteUpload(uploadId, fileName) {
    if (!confirm(`Delete "${fileName}" and all related data (analysis, queries, models, reports)? This cannot be undone.`)) return;
    const { ok, data } = await apiCall(`/api/uploads/${uploadId}`, 'DELETE');
    if (ok) {
        alert(`"${fileName}" deleted successfully.`);
        loadUploads();
    } else {
        alert(data.error || 'Failed to delete dataset.');
    }
}

// Sidebar user info
async function loadUserInfo() {
    const { ok, data } = await apiCall('/api/auth/me', 'GET');
    if (ok && data.user) {
        document.getElementById('sidebar-avatar').textContent = (data.user.full_name || 'U')[0].toUpperCase();
        document.getElementById('sidebar-name').textContent = data.user.full_name;
        document.getElementById('sidebar-email').textContent = data.user.email;
    }
}

document.getElementById('file-input').addEventListener('change', async function(e) {
    const file = this.files[0];
    if (!file) return;
    const name = file.name.toLowerCase();
    if (!name.endsWith('.csv') && !name.endsWith('.xls') && !name.endsWith('.xlsx')) {
        document.getElementById('upload-status').innerHTML = '<div class="alert alert-error">Only CSV and Excel (.xls, .xlsx) files are allowed.</div>';
        return;
    }
    if (file.size > 50 * 1024 * 1024) {
        document.getElementById('upload-status').innerHTML = '<div class="alert alert-error">File size exceeds 50 MB limit.</div>';
        return;
    }

    const statusEl = document.getElementById('upload-status');
    statusEl.innerHTML = '<div class="alert alert-info">Uploading and processing...</div>';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (res.ok) {
            statusEl.innerHTML = '<div class="alert alert-success">File uploaded and analyzed successfully!</div>';
            document.getElementById('upload-result').classList.remove('hidden');

            const infoEl = document.getElementById('dataset-info');
            infoEl.innerHTML = `
                <div class="summary-card mb-2">
                    <div class="summary-stat"><span class="label">File Name</span><span class="value">${data.file_name}</span></div>
                    <div class="summary-stat"><span class="label">Total Rows</span><span class="value">${data.total_rows}</span></div>
                    <div class="summary-stat"><span class="label">Total Columns</span><span class="value">${data.total_columns}</span></div>
                </div>
            `;

            if (data.columns && data.columns.length > 0) {
                let colHtml = '<h4 style="margin-bottom:8px;">Columns</h4><table><thead><tr><th>Name</th><th>Type</th><th>Missing</th><th>Unique</th></tr></thead><tbody>';
                data.columns.forEach(c => {
                    colHtml += `<tr><td>${c.name}</td><td>${c.dtype}</td><td>${c.missing}</td><td>${c.unique}</td></tr>`;
                });
                colHtml += '</tbody></table>';
                infoEl.innerHTML += colHtml;
            }

            const previewEl = document.getElementById('preview-table');
            if (data.preview && data.preview.length > 0) {
                const cols = Object.keys(data.preview[0]);
                let tableHtml = '<h4 style="margin-bottom:8px;">Preview (First 10 Rows)</h4><table><thead><tr>';
                cols.forEach(c => { tableHtml += `<th>${c}</th>`; });
                tableHtml += '</tr></thead><tbody>';
                data.preview.forEach(row => {
                    tableHtml += '<tr>';
                    cols.forEach(c => { tableHtml += `<td>${row[c] !== null && row[c] !== undefined ? row[c] : ''}</td>`; });
                    tableHtml += '</tr>';
                });
                tableHtml += '</tbody></table>';
                previewEl.innerHTML = tableHtml;
            }

            loadUploads();
        } else {
            statusEl.innerHTML = `<div class="alert alert-error">${data.error || 'Upload failed.'}</div>`;
        }
    } catch (err) {
        statusEl.innerHTML = '<div class="alert alert-error">Upload failed due to a network error.</div>';
    }

    this.value = '';
});

const uploadZone = document.getElementById('upload-zone');
uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('dragover'); });
uploadZone.addEventListener('dragleave', () => { uploadZone.classList.remove('dragover'); });
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        document.getElementById('file-input').files = files;
        document.getElementById('file-input').dispatchEvent(new Event('change'));
    }
});

document.addEventListener('DOMContentLoaded', () => { loadUploads(); loadUserInfo(); });
