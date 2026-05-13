let myChart = null;
let isHeatmap = false;

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

async function loadColumns() {
    const uploadId = document.getElementById('dataset-select').value;
    if (!uploadId) return;
    const { ok, data } = await apiCall(`/api/uploads/${uploadId}`, 'GET');
    if (ok && data.columns) {
        const xSel = document.getElementById('x-column');
        const ySel = document.getElementById('y-column');
        xSel.innerHTML = '<option value="">-- Select --</option>';
        ySel.innerHTML = '<option value="">-- None --</option>';
        data.columns.forEach(c => {
            xSel.innerHTML += `<option value="${c.name}">${c.name} (${c.dtype})</option>`;
            ySel.innerHTML += `<option value="${c.name}">${c.name} (${c.dtype})</option>`;
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

function showDownloadButton() {
    document.getElementById('download-chart-section').classList.remove('hidden');
}

function hideDownloadButton() {
    document.getElementById('download-chart-section').classList.add('hidden');
}

function downloadChart() {
    const canvas = document.getElementById('chart-canvas');
    if (!canvas) { alert('No chart to download.'); return; }
    const ctx = canvas.getContext('2d');
    const originalFill = ctx.fillStyle;
    ctx.save();
    ctx.globalCompositeOperation = 'destination-over';
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.restore();
    const link = document.createElement('a');
    link.download = `apollo_chart_${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
}

const chartColors = ['#6c63ff', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899', '#8b5cf6', '#14b8a6', '#f97316', '#6366f1'];

function getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
        grid: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
        text: isDark ? '#9ca3b8' : '#555770'
    };
}

async function generateChart() {
    const uploadId = document.getElementById('dataset-select').value;
    const chartType = document.getElementById('chart-type').value;
    const xColumn = document.getElementById('x-column').value;
    const yColumn = document.getElementById('y-column').value;

    if (!uploadId || !chartType || !xColumn) {
        alert('Please select dataset, chart type, and X-axis column.');
        return;
    }

    hideDownloadButton();
    isHeatmap = false;

    const resultDiv = document.getElementById('chart-result');
    resultDiv.classList.remove('hidden');
    resultDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating chart...</p></div>';

    const { ok, data } = await apiCall('/api/charts/generate', 'POST', {
        upload_id: uploadId, chart_type: chartType, x_column: xColumn, y_column: yColumn
    });
    if (!ok) {
        resultDiv.innerHTML = `<div class="alert alert-error">${data.error || 'Chart generation failed.'}</div>`;
        return;
    }

    if (chartType === 'heatmap') {
        isHeatmap = true;
        resultDiv.innerHTML = '<div class="card"><div class="chart-container"><canvas id="chart-canvas"></canvas></div><div id="download-chart-section" class="hidden" style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border);text-align:center;"><button class="btn btn-primary btn-sm" onclick="downloadChart()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>Download Chart (PNG)</button></div></div>';
        renderHeatmapTable(data.chart_data);
        return;
    }

    resultDiv.innerHTML = '<div class="card"><div class="chart-container"><canvas id="chart-canvas"></canvas></div><div id="download-chart-section" class="hidden" style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border);text-align:center;"><button class="btn btn-primary btn-sm" onclick="downloadChart()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>Download Chart (PNG)</button></div></div>';
    const ctx = document.getElementById('chart-canvas').getContext('2d');
    if (myChart) { myChart.destroy(); myChart = null; }

    const colors = getChartColors();
    const cd = data.chart_data;

    if (chartType === 'scatter') {
        myChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: cd.datasets[0].label,
                    data: cd.datasets[0].data,
                    backgroundColor: chartColors[0],
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: xColumn, color: colors.text }, grid: { color: colors.grid } },
                    y: { title: { display: true, text: yColumn, color: colors.text }, grid: { color: colors.grid } }
                },
                plugins: { legend: { labels: { color: colors.text } } }
            }
        });
        showDownloadButton();
        return;
    }

    if (chartType === 'box') {
        const ds = cd.datasets[0].data[0];
        myChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: cd.labels,
                datasets: [{
                    label: cd.datasets[0].label,
                    data: [ds.median],
                    backgroundColor: chartColors[0]
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            afterBody: function() {
                                return `Min: ${ds.min}\nQ1: ${ds.q1}\nMedian: ${ds.median}\nQ3: ${ds.q3}\nMax: ${ds.max}\nOutliers: ${ds.outliers.length}`;
                            }
                        }
                    },
                    legend: { labels: { color: colors.text } }
                },
                scales: {
                    y: { grid: { color: colors.grid }, ticks: { color: colors.text } },
                    x: { grid: { color: colors.grid }, ticks: { color: colors.text } }
                }
            }
        });
        showDownloadButton();
        return;
    }

    const chartConfig = {
        type: chartType === 'histogram' ? 'bar' : chartType,
        data: {
            labels: cd.labels,
            datasets: cd.datasets.map((ds, i) => ({
                label: ds.label,
                data: ds.data,
                backgroundColor: chartType === 'pie' ? chartColors.slice(0, ds.data.length) : chartColors[i % chartColors.length],
                borderColor: chartColors[i % chartColors.length],
                borderWidth: 1
            }))
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { labels: { color: colors.text } } }
        }
    };

    if (chartType !== 'pie' && chartType !== 'histogram') {
        chartConfig.options.scales = {
            y: { beginAtZero: true, grid: { color: colors.grid }, ticks: { color: colors.text } },
            x: { grid: { color: colors.grid }, ticks: { color: colors.text } }
        };
    }

    myChart = new Chart(ctx, chartConfig);
    showDownloadButton();
}

function renderHeatmapTable(cd) {
    if (!cd.labels || !cd.data) {
        document.getElementById('chart-result').innerHTML = '<p style="color:var(--text-muted);padding:20px;">Not enough data for heatmap.</p>';
        return;
    }

    const canvas = document.getElementById('chart-canvas');
    const labels = cd.labels;
    const data = cd.data;
    const cellSize = 60;
    const padding = 10;
    const headerSize = 30;
    const width = labels.length * cellSize + headerSize;
    const height = labels.length * cellSize + headerSize;

    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);

    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#1a1a2e';

    for (let i = 0; i < labels.length; i++) {
        ctx.save();
        ctx.translate(headerSize / 2, headerSize + i * cellSize + cellSize / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(labels[i], 0, 0);
        ctx.restore();

        ctx.fillText(labels[i], headerSize + i * cellSize + cellSize / 2, headerSize / 2);
    }

    for (let i = 0; i < data.length; i++) {
        for (let j = 0; j < data[i].length; j++) {
            const val = data[i][j];
            const abs = Math.abs(val);
            const r = val >= 0 ? 16 : 239;
            const g = val >= 0 ? 185 : 68;
            const b = val >= 0 ? 129 : 68;
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${abs})`;
            ctx.fillRect(headerSize + j * cellSize, headerSize + i * cellSize, cellSize, cellSize);
            ctx.strokeStyle = '#e2e4ec';
            ctx.lineWidth = 0.5;
            ctx.strokeRect(headerSize + j * cellSize, headerSize + i * cellSize, cellSize, cellSize);
            ctx.fillStyle = abs > 0.5 ? '#ffffff' : '#1a1a2e';
            ctx.font = 'bold 12px sans-serif';
            ctx.fillText(val.toFixed(2), headerSize + j * cellSize + cellSize / 2, headerSize + i * cellSize + cellSize / 2);
        }
    }

    showDownloadButton();
}

document.getElementById('dataset-select').addEventListener('change', loadColumns);
document.addEventListener('DOMContentLoaded', () => { loadDatasets(); loadUserInfo(); });
