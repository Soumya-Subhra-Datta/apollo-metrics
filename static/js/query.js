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

async function askQuestion() {
    const uploadId = document.getElementById('dataset-select').value;
    const question = document.getElementById('question-input').value.trim();

    if (!uploadId) { alert('Please select a dataset.'); return; }
    if (!question) { alert('Please enter a question.'); return; }

    const statusEl = document.getElementById('query-status');
    const resultEl = document.getElementById('query-result');
    statusEl.innerHTML = '<div class="alert alert-info">Asking AI...</div>';
    resultEl.classList.add('hidden');

    const { ok, data } = await apiCall('/api/query', 'POST', { upload_id: uploadId, question });
    if (!ok) {
        statusEl.innerHTML = `<div class="alert alert-error">${data.error || 'Query failed.'}</div>`;
        return;
    }

    statusEl.innerHTML = '';
    resultEl.classList.remove('hidden');
    document.getElementById('query-answer').textContent = data.answer;
    document.getElementById('question-input').value = '';
    loadQueryHistory();
}

async function clearHistory() {
    const uploadId = document.getElementById('dataset-select').value;
    if (!uploadId) { alert('Please select a dataset.'); return; }
    if (!confirm('Clear all query history for this dataset?')) return;
    const { ok, data } = await apiCall(`/api/query/history/${uploadId}`, 'DELETE');
    if (ok) { loadQueryHistory(); alert('Query history cleared.'); }
    else { alert(data.error || 'Failed to clear history.'); }
}

async function clearAllHistory() {
    if (!confirm('Clear ALL query history across all datasets?')) return;
    const { ok, data } = await apiCall('/api/query/history', 'DELETE');
    if (ok) { loadQueryHistory(); alert('All query history cleared.'); }
    else { alert(data.error || 'Failed to clear history.'); }
}

async function loadQueryHistory() {
    const uploadId = document.getElementById('dataset-select').value;
    if (!uploadId) {
        document.getElementById('query-history').innerHTML = '<p style="color:var(--text-muted);padding:20px;text-align:center;">Select a dataset to view query history.</p>';
        return;
    }

    const el = document.getElementById('query-history');
    el.innerHTML = '<div class="loading"><div class="spinner"></div>Loading...</div>';

    const { ok, data } = await apiCall(`/api/query/history/${uploadId}`, 'GET');
    if (!ok) {
        el.innerHTML = `<p style="color:var(--text-muted);padding:20px;">${data.error || 'Failed to load history.'}</p>`;
        return;
    }

    if (!data.queries || data.queries.length === 0) {
        el.innerHTML = '<p style="color:var(--text-muted);padding:20px;text-align:center;">No questions asked yet for this dataset.</p>';
        return;
    }

    let html = '';
    data.queries.forEach(q => {
        html += `<div class="summary-card mb-1">
            <div style="margin-bottom:8px;"><strong style="color:var(--accent);">Q:</strong> ${q.question}</div>
            <div><strong style="color:var(--success);">A:</strong><p class="query-answer" style="margin-top:4px;font-size:13px;">${q.answer ? (q.answer.length > 300 ? q.answer.substring(0, 300) + '...' : q.answer) : 'No answer'}</p></div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:6px;">${q.created_at || ''}</div>
        </div>`;
    });
    el.innerHTML = html;
}

document.getElementById('dataset-select').addEventListener('change', loadQueryHistory);
document.addEventListener('DOMContentLoaded', () => { loadDatasets(); loadUserInfo(); loadQueryHistory(); });
