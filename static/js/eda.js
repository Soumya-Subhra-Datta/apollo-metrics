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
    if (!ok) { if (data.error && data.error.includes('Authentication')) { window.location.href = '/login'; return; } return; }
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

function setEl(id, content) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = content;
}

async function runEDA() {
    const uploadId = document.getElementById('dataset-select').value;
    if (!uploadId) { alert('Please select a dataset.'); return; }

    const resultsEl = document.getElementById('eda-results');
    resultsEl.classList.remove('hidden');
    resultsEl.innerHTML = '<div class="loading"><div class="spinner"></div><p>Running automated EDA...</p></div>';

    let response;
    try {
        const res = await fetch(`/api/eda/${uploadId}`);
        response = await res.json();
        if (!res.ok) { resultsEl.innerHTML = `<div class="alert alert-error">${response.error || 'EDA failed.'}</div>`; return; }
    } catch (e) {
        resultsEl.innerHTML = `<div class="alert alert-error">Network error: ${e.message}</div>`;
        return;
    }

    const data = response;
    const eda = data.eda || {};
    const overview = eda.overview || {};

    resultsEl.innerHTML = '<div class="loading"><div class="spinner"></div><p>Rendering results...</p></div>';

    setTimeout(() => {
        try {
            renderEDA(data, eda, overview);
        } catch (e) {
            resultsEl.innerHTML = `<div class="alert alert-error">Render error: ${e.message}. Check console for details.</div>`;
            console.error('EDA render error:', e);
        }
    }, 50);
}

function renderEDA(data, eda, overview) {
    const resultsEl = document.getElementById('eda-results');

    let cleaningHtml = '';
    if (data.cleaning_summary) {
        const cs = data.cleaning_summary;
        cleaningHtml = `<div class="stats-grid" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));margin-bottom:20px;">
            <div class="summary-card"><h4>Cleaning Summary</h4>
                <div class="summary-stat"><span class="label">Original Rows</span><span class="value">${cs.original_rows || 0}</span></div>
                <div class="summary-stat"><span class="label">Cleaned Rows</span><span class="value">${cs.cleaned_rows || 0}</span></div>
                <div class="summary-stat"><span class="label">Duplicates Removed</span><span class="value">${cs.duplicates_removed || 0}</span></div>
            </div>`;
        if (data.missing_report) {
            cleaningHtml += `<div class="summary-card"><h4>Missing Values</h4>
                <div class="summary-stat"><span class="label">Before</span><span class="value">${data.missing_report.total_missing_before || 0}</span></div>
                <div class="summary-stat"><span class="label">After</span><span class="value">${data.missing_report.total_missing_after || 0}</span></div>
            </div>`;
        }
        cleaningHtml += '</div>';
    }

    let overviewHtml = '<div class="stats-grid">';
    overviewHtml += `<div class="stat-card"><div class="stat-icon uploads"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg></div><div class="stat-number">${overview.total_rows || 0}</div><div class="stat-label">Total Rows</div></div>`;
    overviewHtml += `<div class="stat-card"><div class="stat-icon queries"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div><div class="stat-number">${overview.total_columns || 0}</div><div class="stat-label">Total Columns</div></div>`;
    overviewHtml += `<div class="stat-card"><div class="stat-icon models"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><div class="stat-number">${overview.missing_values || 0}</div><div class="stat-label">Missing Values</div></div>`;
    overviewHtml += `<div class="stat-card"><div class="stat-icon reports"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg></div><div class="stat-number">${overview.duplicate_rows || 0}</div><div class="stat-label">Duplicate Rows</div></div>`;
    if (overview.numerical_columns !== undefined) overviewHtml += `<div class="stat-card"><div class="stat-icon queries" style="background:rgba(16,185,129,0.12);color:var(--success);"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg></div><div class="stat-number">${overview.numerical_columns}</div><div class="stat-label">Numerical</div></div>`;
    if (overview.categorical_columns !== undefined) overviewHtml += `<div class="stat-card"><div class="stat-icon models" style="background:rgba(245,158,11,0.12);color:var(--warning);"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h16"/></svg></div><div class="stat-number">${overview.categorical_columns}</div><div class="stat-label">Categorical</div></div>`;
    overviewHtml += '</div>';

    let numHtml = '';
    try {
        const numData = eda.numerical_stats || {};
        const keys = Object.keys(numData);
        if (keys.length > 0) {
            const fields = ['mean', 'median', 'std', 'min', 'max', 'q1', 'q3'];
            numHtml = '<div class="table-container"><table><thead><tr><th>Column</th>';
            fields.forEach(f => { numHtml += `<th>${f}</th>`; });
            numHtml += '</tr></thead><tbody>';
            keys.forEach(col => {
                numHtml += `<tr><td style="font-weight:600;">${col}</td>`;
                fields.forEach(f => { numHtml += `<td>${numData[col][f] !== undefined ? numData[col][f] : ''}</td>`; });
                numHtml += '</tr>';
            });
            numHtml += '</tbody></table></div>';
        } else {
            numHtml = '<p style="color:var(--text-muted);padding:12px;">No numerical columns found.</p>';
        }
    } catch (e) { numHtml = `<p style="color:var(--danger);">Error rendering numerical stats.</p>`; }

    let catHtml = '';
    try {
        const catData = eda.categorical_stats || {};
        const keys = Object.keys(catData);
        if (keys.length > 0) {
            keys.forEach(col => {
                const s = catData[col];
                catHtml += `<div class="summary-card mb-1"><h4>${col}</h4>`;
                catHtml += `<div class="summary-stat"><span class="label">Unique Values</span><span class="value">${s.unique_values}</span></div>`;
                catHtml += `<div class="summary-stat"><span class="label">Missing</span><span class="value">${s.missing}</span></div>`;
                if (s.top_values) {
                    catHtml += '<div style="margin-top:6px;font-size:12px;color:var(--text-muted);font-weight:600;">Top Values:</div>';
                    Object.entries(s.top_values).slice(0, 5).forEach(([k, v]) => {
                        catHtml += `<div class="summary-stat" style="font-size:12px;"><span class="label">${k}</span><span class="value">${v}</span></div>`;
                    });
                }
                catHtml += '</div>';
            });
        } else {
            catHtml = '<p style="color:var(--text-muted);padding:12px;">No categorical columns found.</p>';
        }
    } catch (e) { catHtml = `<p style="color:var(--danger);">Error rendering categorical stats.</p>`; }

    let insightHtml = '';
    try {
        const insights = eda.insights || [];
        if (insights.length > 0) {
            insightHtml = insights.map(i => `<div class="insight-card">${i}</div>`).join('');
        } else {
            insightHtml = '<p style="color:var(--text-muted);padding:12px;">No insights generated.</p>';
        }
    } catch (e) { insightHtml = `<p style="color:var(--danger);">Error rendering insights.</p>`; }

    let corrHtml = '';
    try {
        const cd = eda.correlation_matrix || {};
        if (cd.data && cd.data.length > 0) {
            const cols = cd.columns || [];
            corrHtml = '<div class="table-container"><table><thead><tr><th></th>';
            cols.forEach(c => { corrHtml += `<th style="font-size:11px;padding:4px 8px;">${c}</th>`; });
            corrHtml += '</tr></thead><tbody>';
            cd.data.forEach((row, i) => {
                corrHtml += `<tr><td style="font-weight:600;font-size:11px;padding:4px 8px;">${cols[i]}</td>`;
                row.forEach(val => {
                    const c = Math.abs(val) > 0.7 ? 'var(--success)' : Math.abs(val) > 0.4 ? 'var(--warning)' : 'var(--text-muted)';
                    corrHtml += `<td style="color:${c};font-weight:${Math.abs(val) > 0.5 ? 600 : 400};padding:4px 8px;font-size:12px;">${val}</td>`;
                });
                corrHtml += '</tr>';
            });
            corrHtml += '</tbody></table></div>';
        } else {
            corrHtml = '<p style="color:var(--text-muted);padding:12px;">Not enough numerical columns for correlation matrix.</p>';
        }
    } catch (e) { corrHtml = `<p style="color:var(--danger);">Error rendering correlation matrix.</p>`; }

    let previewHtml = '';
    try {
        if (eda.preview && eda.preview.length > 0) {
            const cols = Object.keys(eda.preview[0]);
            previewHtml = '<div class="table-container"><table><thead><tr>';
            cols.forEach(c => { previewHtml += `<th>${c}</th>`; });
            previewHtml += '</tr></thead><tbody>';
            eda.preview.forEach(row => {
                previewHtml += '<tr>';
                cols.forEach(c => { previewHtml += `<td>${row[c] !== null && row[c] !== undefined ? row[c] : ''}</td>`; });
                previewHtml += '</tr>';
            });
            previewHtml += '</tbody></table></div>';
        }
    } catch (e) { previewHtml = `<p style="color:var(--danger);">Error rendering preview.</p>`; }

    resultsEl.innerHTML = cleaningHtml + overviewHtml +
        `<div class="grid-2 mt-2">
            <div class="card"><div class="card-header"><h3>Numerical Statistics</h3></div>${numHtml}</div>
            <div class="card"><div class="card-header"><h3>Categorical Statistics</h3></div>${catHtml}</div>
        </div>
        <div class="card mt-2"><div class="card-header"><h3>EDA Insights</h3></div>${insightHtml}</div>
        <div class="card mt-2"><div class="card-header"><h3>Correlation Matrix</h3></div>${corrHtml}</div>
        <div class="card mt-2"><div class="card-header"><h3>Dataset Preview</h3></div>${previewHtml}</div>`;
}

document.addEventListener('DOMContentLoaded', () => { loadDatasets(); loadUserInfo(); });
