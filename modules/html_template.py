"""
HTML Template für den NASDAQ-100 Cheapest Quality Screener.
Wird von modules/html_report.py importiert.
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NASDAQ-100 Cheapest Quality Screener</title>
<style>
:root {
    --bg: #0d1117;
    --surface: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --text-dim: #8b949e;
    --green: #3fb950;
    --yellow: #d29922;
    --red: #f85149;
    --blue: #58a6ff;
    --purple: #bc8cff;
    --accent: #1f6feb;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
}
.container {
    max-width: 1800px;
    margin: 0 auto;
    padding: 20px;
}
header {
    text-align: center;
    padding: 30px 0 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
}
header h1 {
    font-size: 1.8em;
    background: linear-gradient(135deg, var(--green), var(--blue));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
header .subtitle { color: var(--text-dim); font-size: 0.9em; }
header .timestamp { color: var(--text-dim); font-size: 0.8em; margin-top: 5px; }
.rebalance-note {
    text-align: center;
    padding: 8px 16px;
    margin: 10px auto;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.9em;
    color: var(--yellow);
    max-width: 600px;
}

.legend {
    display: flex;
    flex-wrap: wrap;
    gap: 12px 20px;
    justify-content: center;
    padding: 12px 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 0.82em;
    color: var(--text-dim);
}
.legend span { white-space: nowrap; }
.legend .green { color: var(--green); }
.legend .yellow { color: var(--yellow); }
.legend .red { color: var(--red); }

.tabs {
    display: flex;
    gap: 4px;
    border-bottom: 2px solid var(--border);
    margin-bottom: 0;
    flex-wrap: wrap;
}
.tab {
    padding: 10px 20px;
    cursor: pointer;
    border: 1px solid transparent;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    background: transparent;
    color: var(--text-dim);
    font-size: 0.9em;
    font-weight: 500;
    transition: all 0.2s;
    user-select: none;
}
.tab:hover { color: var(--text); background: var(--surface); }
.tab.active {
    color: var(--text);
    background: var(--surface);
    border-color: var(--border);
    border-bottom: 2px solid var(--surface);
    margin-bottom: -2px;
}
.tab .badge {
    background: var(--accent);
    color: white;
    font-size: 0.75em;
    padding: 1px 6px;
    border-radius: 10px;
    margin-left: 5px;
}
.tab-content { display: none; }
.tab-content.active { display: block; }

.table-wrapper {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 0 8px 8px 8px;
    overflow-x: auto;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82em;
}
th {
    position: sticky;
    top: 0;
    background: #1c2129;
    border-bottom: 2px solid var(--border);
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    color: var(--text-dim);
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
}
th:hover { color: var(--text); }
th .sort-arrow { margin-left: 4px; font-size: 0.8em; }
td {
    padding: 6px 10px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}
tr:hover { background: rgba(88,166,255,0.04); }
tr:last-child td { border-bottom: none; }

.c-green { color: var(--green); }
.c-yellow { color: var(--yellow); }
.c-red { color: var(--red); }
.peg-green { color: var(--green); font-weight: 600; }
.peg-yellow { color: var(--yellow); font-weight: 600; }
.peg-red { color: var(--red); font-weight: 600; }
.perf-pos { color: var(--green); }
.perf-neg { color: var(--red); }
.qual-3 { color: var(--green); font-weight: 700; }
.qual-2 { color: var(--blue); font-weight: 600; }
.qual-1 { color: var(--text-dim); }
.qual-0 { color: var(--text-dim); opacity: 0.5; }
.zone-green { color: var(--green); font-size: 0.9em; }
.zone-yellow { color: var(--yellow); font-size: 0.9em; }
.zone-red { color: var(--red); font-size: 0.9em; }
.name-cell { color: var(--text-dim); font-size: 0.9em; max-width: 180px; overflow: hidden; text-overflow: ellipsis; }
.symbol-cell { font-weight: 700; color: var(--blue); }

.stats {
    display: flex;
    gap: 15px;
    justify-content: center;
    margin: 15px 0;
    flex-wrap: wrap;
}
.stat {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 16px;
    text-align: center;
    min-width: 100px;
}
.stat .value { font-size: 1.4em; font-weight: 700; }
.stat .label { font-size: 0.75em; color: var(--text-dim); }
.stat .value.green { color: var(--green); }
.stat .value.yellow { color: var(--yellow); }
.stat .value.red { color: var(--red); }

.search-box {
    padding: 10px 15px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 0.9em;
    width: 250px;
    margin: 10px 0;
    outline: none;
}
.search-box:focus { border-color: var(--accent); }
.toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin: 10px 0; }
</style>
</head>
<body>
<div class="container">

<header>
    <h1>💎 NASDAQ-100 Cheapest Quality Screener</h1>
    <div class="subtitle">
        Novy-Marx Gross Profitability Premium + Multi-Factor | v10
    </div>
    <div class="timestamp">Stand: {{TIMESTAMP}} | Daten: Yahoo Finance</div>
</header>

<div class="rebalance-note">{{REBALANCE_NOTE}}</div>

<div class="legend">
    <span><strong>NM</strong> = Novy-Marx (GP/A 40% + P/B 35% + Mom 25%)</span>
    <span><strong>MF</strong> = Multi-Factor (GP/A 25% + ROE 20% + P/B 20% + fPEG 15% + Mom 20%)</span>
    <span><strong>NMR</strong> = NM Rank (GP/A Dezil + P/B Dezil, 2–20)</span>
    <span><strong>D.GP/D.PB</strong> = Dezil im Universum (10=best)</span>
    <span><strong>AG</strong> = Asset Growth (niedrig=gut)</span>
    <span>GP/A: <span class="green">■ ≥30%</span> <span class="yellow">■ 15–30%</span> <span class="red">■ &lt;15%</span></span>
    <span>GM: <span class="green">■ ≥50%</span> <span class="yellow">■ 30–50%</span> <span class="red">■ &lt;30%</span></span>
    <span>ROE: <span class="green">■ ≥20%</span> <span class="yellow">■ 10–20%</span> <span class="red">■ &lt;10%</span></span>
    <span>P/B: <span class="green">■ ≤5</span> <span class="yellow">■ 5–15</span> <span class="red">■ &gt;15</span></span>
    <span>PEG: <span class="green">■ ≤1.0</span> <span class="yellow">■ 1.0–1.5</span> <span class="red">■ &gt;1.5</span></span>
    <span>AG: <span class="green">■ ≤10%</span> <span class="yellow">■ 10–25%</span> <span class="red">■ &gt;25%</span></span>
    <span>Dezil: <span class="green">■ 8–10</span> <span class="yellow">■ 4–7</span> <span class="red">■ 1–3</span></span>
</div>

<div class="stats" id="stats"></div>

<div class="tabs" id="tabs">
    <div class="tab active" data-tab="all">Alle Aktien <span class="badge" id="badge-all"></span></div>
    <div class="tab" data-tab="sweet">💎 Sweet Spot <span class="badge" id="badge-sweet"></span></div>
    <div class="tab" data-tab="nmrank">📊 NM Rank <span class="badge" id="badge-nmrank"></span></div>
    <div class="tab" data-tab="traps">⚠️ Value Traps <span class="badge" id="badge-traps"></span></div>
    <div class="tab" data-tab="divergent">🔍 PEG Divergenz <span class="badge" id="badge-divergent"></span></div>
    <div class="tab" data-tab="nopeg">📊 Kein PEG <span class="badge" id="badge-nopeg"></span></div>
</div>

<div class="tab-content active" id="content-all">
    <div class="toolbar">
        <input type="text" class="search-box" id="search-all" placeholder="🔍 Suche Symbol oder Name...">
    </div>
    <div class="table-wrapper"><table id="table-all"></table></div>
</div>
<div class="tab-content" id="content-sweet">
    <div class="toolbar">
        <input type="text" class="search-box" id="search-sweet" placeholder="🔍 Suche...">
    </div>
    <div class="table-wrapper"><table id="table-sweet"></table></div>
</div>
<div class="tab-content" id="content-nmrank">
    <div class="toolbar">
        <input type="text" class="search-box" id="search-nmrank" placeholder="🔍 Suche...">
    </div>
    <div class="table-wrapper"><table id="table-nmrank"></table></div>
</div>
<div class="tab-content" id="content-traps">
    <div class="table-wrapper"><table id="table-traps"></table></div>
</div>
<div class="tab-content" id="content-divergent">
    <div class="table-wrapper"><table id="table-divergent"></table></div>
</div>
<div class="tab-content" id="content-nopeg">
    <div class="toolbar">
        <input type="text" class="search-box" id="search-nopeg" placeholder="🔍 Suche...">
    </div>
    <div class="table-wrapper"><table id="table-nopeg"></table></div>
</div>

</div>

<script>
const allData = {{ALL_DATA}};
const sweetData = {{SWEET_DATA}};
const trapsData = {{TRAPS_DATA}};
const noPegData = {{NO_PEG_DATA}};
const divergentData = {{DIVERGENT_DATA}};
const nmTopData = {{NM_TOP_DATA}};

// =====================================================================
// Formatting helpers
// =====================================================================

function fmtPct(v, digits=1) {
    if (v === null || v === undefined) return 'N/A';
    return (v * 100).toFixed(digits) + '%';
}
function fmtPctSigned(v) {
    if (v === null || v === undefined) return 'N/A';
    let s = (v * 100).toFixed(1);
    return (v >= 0 ? '+' : '') + s + '%';
}
function fmtNum(v, d=2) {
    if (v === null || v === undefined) return 'N/A';
    return Number(v).toFixed(d);
}
function fmtInt(v) {
    if (v === null || v === undefined) return '—';
    return String(v);
}

// =====================================================================
// Color class helpers
// =====================================================================

function pegClass(v) {
    if (v === null || v === undefined) return '';
    if (v <= 1.0) return 'peg-green';
    if (v <= 1.5) return 'peg-yellow';
    return 'peg-red';
}
function gpaClass(v) {
    if (v === null || v === undefined) return '';
    if (v >= 0.30) return 'c-green';
    if (v >= 0.15) return 'c-yellow';
    return 'c-red';
}
function gmClass(v) {
    if (v === null || v === undefined) return '';
    if (v >= 0.50) return 'c-green';
    if (v >= 0.30) return 'c-yellow';
    return 'c-red';
}
function roeClass(v) {
    if (v === null || v === undefined) return '';
    if (v >= 0.20) return 'c-green';
    if (v >= 0.10) return 'c-yellow';
    return 'c-red';
}
function pbClass(v) {
    if (v === null || v === undefined) return '';
    if (v <= 5.0) return 'c-green';
    if (v <= 15.0) return 'c-yellow';
    return 'c-red';
}
function agClass(v) {
    if (v === null || v === undefined) return '';
    if (v <= 0.10) return 'c-green';
    if (v <= 0.25) return 'c-yellow';
    return 'c-red';
}
function decileClass(v) {
    if (v === null || v === undefined) return '';
    if (v >= 8) return 'c-green';
    if (v >= 4) return 'c-yellow';
    return 'c-red';
}
function nmRankClass(v) {
    if (v === null || v === undefined) return '';
    if (v >= 16) return 'c-green';
    if (v >= 10) return 'c-yellow';
    return 'c-red';
}
function perfClass(v) {
    if (v === null || v === undefined) return '';
    return v >= 0 ? 'perf-pos' : 'perf-neg';
}
function zoneText(v) {
    if (v === null || v === undefined) return '';
    if (v <= 1.0) return '<span class="zone-green">🟢 GÜNSTIG</span>';
    if (v <= 1.5) return '<span class="zone-yellow">🟡 FAIR</span>';
    return '<span class="zone-red">🔴 TEUER</span>';
}
function qualClass(q) {
    if (q === '★★★') return 'qual-3';
    if (q === '★★') return 'qual-2';
    if (q === '★') return 'qual-1';
    return 'qual-0';
}
function stars(n) {
    if (n <= 0) return '—';
    return '⭐'.repeat(Math.round(n));
}

// =====================================================================
// Column definitions
// =====================================================================

const mainCols = [
    { key: 'symbol', label: 'Symbol', fmt: v => `<span class="symbol-cell">${v}</span>` },
    { key: 'name', label: 'Name', fmt: v => `<span class="name-cell">${v || ''}</span>` },
    { key: 'gp_a', label: 'GP/A', fmt: v => `<span class="${gpaClass(v)}">${fmtPct(v)}</span>`, sort: 'num' },
    { key: 'gross_margin', label: 'GM', fmt: v => `<span class="${gmClass(v)}">${fmtPct(v)}</span>`, sort: 'num' },
    { key: 'roe', label: 'ROE', fmt: v => `<span class="${roeClass(v)}">${fmtPct(v)}</span>`, sort: 'num' },
    { key: 'pb', label: 'P/B', fmt: v => `<span class="${pbClass(v)}">${fmtNum(v)}</span>`, sort: 'num' },
    { key: 'nm', label: 'NM', fmt: v => v, sort: 'num' },
    { key: 'nm', label: 'NM★', fmt: v => stars(v) },
    { key: 'mf', label: 'MF', fmt: v => v, sort: 'num' },
    { key: 'mf', label: 'MF★', fmt: v => stars(v) },
    { key: 'quality', label: 'Qual', fmt: v => `<span class="${qualClass(v)}">${v}</span>` },
    { key: 'fwd_peg', label: 'fPEG', fmt: v => `<span class="${pegClass(v)}">${fmtNum(v)}</span>`, sort: 'num' },
    { key: 'gaap_peg', label: 'gPEG', fmt: v => `<span class="${pegClass(v)}">${fmtNum(v)}</span>`, sort: 'num' },
    { key: 'growth_used', label: 'Grw%', fmt: v => fmtPct(v, 0), sort: 'num' },
    { key: 'peg_source', label: 'Src', fmt: v => v || '' },
    { key: 'fwd_peg', label: 'Zone', fmt: v => zoneText(v) },
    { key: 'gp_a_decile', label: 'D.GP', fmt: v => `<span class="${decileClass(v)}">${fmtInt(v)}</span>`, sort: 'num' },
    { key: 'pb_decile', label: 'D.PB', fmt: v => `<span class="${decileClass(v)}">${fmtInt(v)}</span>`, sort: 'num' },
    { key: 'nm_rank', label: 'NMR', fmt: v => `<span class="${nmRankClass(v)}">${fmtInt(v)}</span>`, sort: 'num' },
    { key: 'asset_growth', label: 'AG', fmt: v => `<span class="${agClass(v)}">${fmtPctSigned(v)}</span>`, sort: 'num' },
    { key: 'perf_6m', label: '6M', fmt: v => `<span class="${perfClass(v)}">${fmtPctSigned(v)}</span>`, sort: 'num' },
    { key: 'perf_12m', label: '12M', fmt: v => `<span class="${perfClass(v)}">${fmtPctSigned(v)}</span>`, sort: 'num' },
];

const divCols = [
    { key: 'symbol', label: 'Symbol', fmt: v => `<span class="symbol-cell">${v}</span>` },
    { key: 'name', label: 'Name', fmt: v => `<span class="name-cell">${v || ''}</span>` },
    { key: 'fwd_peg', label: 'fPEG', fmt: v => `<span class="${pegClass(v)}">${fmtNum(v)}</span>`, sort: 'num' },
    { key: 'gaap_peg', label: 'gPEG', fmt: v => `<span class="${pegClass(v)}">${fmtNum(v)}</span>`, sort: 'num' },
    { key: 'growth_used', label: 'Grw%', fmt: v => fmtPct(v, 0), sort: 'num' },
    { key: 'ratio', label: 'Ratio', fmt: v => fmtNum(v, 1) + 'x', sort: 'num' },
    { key: 'signal', label: 'Signal', fmt: v => v },
    { key: 'nm', label: 'NM', fmt: v => v, sort: 'num' },
    { key: 'mf', label: 'MF', fmt: v => v, sort: 'num' },
    { key: 'nm_rank', label: 'NMR', fmt: v => `<span class="${nmRankClass(v)}">${fmtInt(v)}</span>`, sort: 'num' },
    { key: 'perf_12m', label: '12M', fmt: v => `<span class="${perfClass(v)}">${fmtPctSigned(v)}</span>`, sort: 'num' },
];

// =====================================================================
// Table renderer with sorting and search
// =====================================================================

function renderTable(tableId, data, cols, searchId) {
    const table = document.getElementById(tableId);
    let currentSort = { col: null, asc: true };
    let filteredData = [...data];

    function draw() {
        let html = '<thead><tr>';
        cols.forEach((c, i) => {
            let arrow = '';
            if (currentSort.col === i) arrow = currentSort.asc ? ' ▲' : ' ▼';
            html += `<th data-col="${i}">${c.label}<span class="sort-arrow">${arrow}</span></th>`;
        });
        html += '</tr></thead><tbody>';

        filteredData.forEach(row => {
            html += '<tr>';
            cols.forEach(c => {
                let val = row[c.key];
                html += `<td>${c.fmt(val)}</td>`;
            });
            html += '</tr>';
        });

        if (filteredData.length === 0) {
            html += `<tr><td colspan="${cols.length}" style="text-align:center; padding:20px; color:var(--text-dim)">Keine Ergebnisse</td></tr>`;
        }

        html += '</tbody>';
        table.innerHTML = html;

        table.querySelectorAll('th').forEach(th => {
            th.addEventListener('click', () => {
                const ci = parseInt(th.dataset.col);
                if (currentSort.col === ci) {
                    currentSort.asc = !currentSort.asc;
                } else {
                    currentSort.col = ci;
                    currentSort.asc = true;
                }
                const key = cols[ci].key;
                filteredData.sort((a, b) => {
                    let va = a[key], vb = b[key];
                    if (va === null || va === undefined) va = currentSort.asc ? Infinity : -Infinity;
                    if (vb === null || vb === undefined) vb = currentSort.asc ? Infinity : -Infinity;
                    if (typeof va === 'string') return currentSort.asc ? va.localeCompare(vb) : vb.localeCompare(va);
                    return currentSort.asc ? va - vb : vb - va;
                });
                draw();
            });
        });
    }

    if (searchId) {
        const searchBox = document.getElementById(searchId);
        if (searchBox) {
            searchBox.addEventListener('input', () => {
                const q = searchBox.value.toLowerCase();
                filteredData = data.filter(r =>
                    (r.symbol && r.symbol.toLowerCase().includes(q)) ||
                    (r.name && r.name.toLowerCase().includes(q))
                );
                draw();
            });
        }
    }

    draw();
}

// =====================================================================
// Tab switching
// =====================================================================

document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('content-' + tab.dataset.tab).classList.add('active');
    });
});

// =====================================================================
// Stats bar
// =====================================================================

const greenCount = allData.filter(r => r.fwd_peg !== null && r.fwd_peg <= 1.0).length;
const yellowCount = allData.filter(r => r.fwd_peg !== null && r.fwd_peg > 1.0 && r.fwd_peg <= 1.5).length;
const redCount = allData.filter(r => r.fwd_peg !== null && r.fwd_peg > 1.5).length;
const highGpaCount = allData.filter(r => r.gp_a !== null && r.gp_a >= 0.30).length;
const highNmrCount = allData.filter(r => r.nm_rank !== null && r.nm_rank >= 16).length;

document.getElementById('stats').innerHTML = `
    <div class="stat"><div class="value">${allData.length}</div><div class="label">Aktien gesamt</div></div>
    <div class="stat"><div class="value green">${greenCount}</div><div class="label">🟢 PEG Günstig</div></div>
    <div class="stat"><div class="value yellow">${yellowCount}</div><div class="label">🟡 PEG Fair</div></div>
    <div class="stat"><div class="value red">${redCount}</div><div class="label">🔴 PEG Teuer</div></div>
    <div class="stat"><div class="value">${sweetData.length}</div><div class="label">💎 Sweet Spot</div></div>
    <div class="stat"><div class="value green">${highGpaCount}</div><div class="label">GP/A ≥30%</div></div>
    <div class="stat"><div class="value green">${highNmrCount}</div><div class="label">NMR ≥16</div></div>
`;

// =====================================================================
// Badges + Render
// =====================================================================

document.getElementById('badge-all').textContent = allData.length;
document.getElementById('badge-sweet').textContent = sweetData.length;
document.getElementById('badge-nmrank').textContent = nmTopData.length;
document.getElementById('badge-traps').textContent = trapsData.length;
document.getElementById('badge-divergent').textContent = divergentData.length;
document.getElementById('badge-nopeg').textContent = noPegData.length;

renderTable('table-all', allData, mainCols, 'search-all');
renderTable('table-sweet', sweetData, mainCols, 'search-sweet');
renderTable('table-nmrank', nmTopData, mainCols, 'search-nmrank');
renderTable('table-traps', trapsData, mainCols);
renderTable('table-divergent', divergentData, divCols);
renderTable('table-nopeg', noPegData, mainCols, 'search-nopeg');
</script>
</body>
</html>"""


def render_html(data: dict) -> str:
    """Rendert das HTML-Template mit den übergebenen Daten.

    Args:
        data: Dictionary mit folgenden Keys:
            - TIMESTAMP: str
            - REBALANCE_NOTE: str
            - ALL_DATA: str (JSON)
            - SWEET_DATA: str (JSON)
            - TRAPS_DATA: str (JSON)
            - NO_PEG_DATA: str (JSON)
            - DIVERGENT_DATA: str (JSON)
            - NM_TOP_DATA: str (JSON)

    Returns:
        Fertig gerendertes HTML als String.
    """
    html = HTML_TEMPLATE
    for key, value in data.items():
        html = html.replace('{{' + key + '}}', str(value))
    return html
