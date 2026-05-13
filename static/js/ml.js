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
    const statusEl = document.getElementById('ml-status');
    if (!data.uploads || data.uploads.length === 0) {
        statusEl.innerHTML = '<div class="alert alert-info">No datasets uploaded yet. Go to <a href="/upload">Upload Dataset</a> to add one.</div>';
        return;
    }
    statusEl.innerHTML = '';
    data.uploads.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.textContent = `${u.file_name} (${u.total_rows} rows)`;
        select.appendChild(opt);
    });
}

async function loadColumns() {
    const uploadId = document.getElementById('dataset-select').value;
    const statusEl = document.getElementById('ml-status');
    if (!uploadId) { statusEl.innerHTML = ''; return; }
    statusEl.innerHTML = '<div class="loading"><div class="spinner"></div>Loading columns...</div>';
    const { ok, data } = await apiCall(`/api/uploads/${uploadId}`, 'GET');
    const sel = document.getElementById('target-column');
    sel.innerHTML = '<option value="">-- None (Clustering) --</option>';
    statusEl.innerHTML = '';
    if (ok && data.columns) {
        data.columns.forEach(c => {
            sel.innerHTML += `<option value="${c.name}">${c.name} (${c.dtype})</option>`;
        });
    } else {
        statusEl.innerHTML = `<div class="alert alert-error">${data.error || 'Could not load columns for this dataset. The file may have been lost during server restart.'}</div>`;
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

async function trainModel() {
    const uploadId = document.getElementById('dataset-select').value;
    const targetColumn = document.getElementById('target-column').value;
    const taskType = document.getElementById('task-type').value;

    if (!uploadId) {
        alert('Please select a dataset.');
        return;
    }

    const statusEl = document.getElementById('training-status');
    statusEl.innerHTML = '<div class="alert alert-info">Training models... This may take a moment.</div>';

    const resultsEl = document.getElementById('ml-results');
    resultsEl.classList.add('hidden');

    const body = { upload_id: uploadId, target_column: targetColumn };
    if (taskType) body.task_type = taskType;

    const { ok, data } = await apiCall('/api/ml/train', 'POST', body);
    if (!ok) {
        let msg = `<div class="alert alert-error">${data.error || 'Model training failed.'}</div>`;
        if (data.individual_errors && Object.keys(data.individual_errors).length > 0) {
            msg += '<div style="margin-top:12px;"><strong style="font-size:13px;">Individual model errors:</strong></div>';
            Object.entries(data.individual_errors).forEach(([name, err]) => {
                msg += `<div class="summary-card mb-1" style="margin-top:8px;">
                    <div style="font-weight:600;color:var(--accent);margin-bottom:4px;">${name}</div>
                    <div style="font-size:12px;color:var(--danger);font-family:monospace;white-space:pre-wrap;">${err}</div>
                </div>`;
            });
            if (data.results && data.results.all_results) {
                msg += '<div style="margin-top:16px;"><button class="btn btn-secondary btn-sm" onclick="document.getElementById(\'debug-results\').classList.toggle(\'hidden\')">Show Full Response</button></div>';
                msg += '<div id="debug-results" class="hidden" style="margin-top:8px;"><pre style="font-size:11px;background:var(--bg-secondary);padding:12px;border-radius:8px;overflow-x:auto;max-height:300px;">' + JSON.stringify(data.results, null, 2) + '</pre></div>';
            }
        }
        statusEl.innerHTML = msg;
        return;
    }

    const r = data.results;

    // Check for task warning (e.g., classification on continuous target)
    if (r.task_warning) {
        statusEl.innerHTML = `<div class="alert alert-warning">${r.task_warning}</div>`;
        resultsEl.classList.remove('hidden');
        document.getElementById('best-model-info').innerHTML = `<div class="summary-card"><p style="color:var(--text-muted);">Results are not meaningful for this combination. The system encoded ${r.n_features ? '' : ''} continuous values as class labels. Select a categorical target column for proper classification.</p></div>`;
        document.getElementById('model-comparison').innerHTML = '';
        document.getElementById('ml-explanation').innerHTML = '';
        return;
    }

    statusEl.innerHTML = '<div class="alert alert-success">Model training completed successfully!</div>';
    resultsEl.classList.remove('hidden');

    // Store model_result_id for download
    const modelResultId = data.model_result_id;
    const downloadSection = document.getElementById('download-section');
    if (modelResultId) {
        downloadSection.classList.remove('hidden');
        downloadSection.querySelector('button').dataset.resultId = modelResultId;
    } else {
        downloadSection.classList.add('hidden');
    }

    // Best model info
    const bestEl = document.getElementById('best-model-info');
    let bestHtml = `<div class="summary-card">
        <div class="summary-stat"><span class="label">Task Type</span><span class="value"><span class="badge badge-purple">${r.task_type || 'N/A'}</span></span></div>
        <div class="summary-stat"><span class="label">Target Column</span><span class="value">${r.target_column || 'None (Clustering)'}</span></div>
        <div class="summary-stat"><span class="label">Best Model</span><span class="value" style="color:var(--accent);font-size:16px;">${r.best_model || 'N/A'}</span></div>
        <div class="summary-stat"><span class="label">Best Score</span><span class="value" style="font-size:18px;font-weight:700;color:var(--success);">${r.best_score || 0}</span></div>
        <div class="summary-stat"><span class="label">Features Used</span><span class="value">${r.n_features || 0}</span></div>
    </div>`;
    if (r.feature_names && r.feature_names.length > 0) {
        bestHtml += `<div style="margin-top:12px;"><strong style="font-size:12px;color:var(--text-muted);">Features:</strong> ${r.feature_names.join(', ')}</div>`;
    }
    bestEl.innerHTML = bestHtml;

    // Model comparison
    const compEl = document.getElementById('model-comparison');
    let compHtml = '';
    if (r.all_results) {
        Object.entries(r.all_results).forEach(([name, result]) => {
            compHtml += `<div class="model-result-card ${name === r.best_model ? 'model-result-card' : ''}">`;
            compHtml += `<div class="model-name">${name} ${name === r.best_model ? '<span class="badge badge-green">Best</span>' : ''}</div>`;
            if (result.error) {
                compHtml += `<p style="color:var(--danger);">${result.error}</p>`;
            } else if (result.metrics) {
                compHtml += '<div class="metric-list">';
                Object.entries(result.metrics).forEach(([k, v]) => {
                    let valCls = 'accent';
                    if (k === 'accuracy' || k === 'r2_score' || k === 'f1_score') valCls = v > 0.8 ? 'success' : v > 0.6 ? 'warning' : 'danger';
                    if (k === 'mae' || k === 'mse' || k === 'rmse') valCls = 'danger';
                    compHtml += `<div class="metric-item"><div class="metric-value" style="color:var(--${valCls});">${v}</div><div class="metric-label">${k}</div></div>`;
                });
                compHtml += '</div>';
            }
            if (result.confusion_matrix) {
                compHtml += `<div style="margin-top:8px;"><strong style="font-size:12px;color:var(--text-muted);">Confusion Matrix:</strong> `;
                result.confusion_matrix.forEach(row => {
                    compHtml += `[${row.join(', ')}] `;
                });
                compHtml += '</div>';
            }
            if (result.cluster_summary) {
                compHtml += `<div style="margin-top:8px;"><strong style="font-size:12px;color:var(--text-muted);">Cluster Centers:</strong><pre style="font-size:11px;overflow-x:auto;">${JSON.stringify(result.cluster_summary, null, 2)}</pre></div>`;
            }
            compHtml += '</div>';
        });
    }
    compEl.innerHTML = compHtml;

    // LLM explanation
    const expEl = document.getElementById('ml-explanation');
    if (data.llm_explanation) {
        expEl.innerHTML = `<div class="query-answer">${data.llm_explanation}</div>`;
    } else {
        expEl.innerHTML = '<p style="color:var(--text-muted);">LLM explanation not available.</p>';
    }
}

function downloadModel() {
    const btn = document.querySelector('#download-section button');
    const resultId = btn ? btn.dataset.resultId : null;
    if (!resultId) { alert('No model available for download.'); return; }
    window.location.href = `/api/ml/download/${resultId}`;
}

document.getElementById('dataset-select').addEventListener('change', loadColumns);
document.addEventListener('DOMContentLoaded', () => { loadDatasets(); loadUserInfo(); });
