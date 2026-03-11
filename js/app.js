// API Base URL
const API_BASE = 'http://localhost:5000';

// Global data storage
let buyData = [];
let holdData = [];
let sellData = [];
let lastUpdate = '';

// Sort state
let sortColumn = null;
let sortDirection = 'asc';

// Fetch all data on page load
document.addEventListener('DOMContentLoaded', function() {
    fetchData();
});

// Refresh button handler
document.getElementById('refreshBtn').addEventListener('click', async function() {
    try {
        await fetch(`${API_BASE}/api/analyze`, { method: 'POST' });
        alert('Fresh analysis started! Data will update in a few moments...');
        setTimeout(fetchData, 5000);
    } catch (error) {
        console.error('Error triggering analysis:', error);
        fetchData();
    }
});

// Fetch all stock data from API
async function fetchData() {
    showLoading(true);
    
    try {
        const statsResponse = await fetch(`${API_BASE}/api/stats`);
        if (!statsResponse.ok) throw new Error('Stats fetch failed');
        const statsData = await statsResponse.json();
        
        document.getElementById('buyCount').textContent = statsData.buy_recommendations;
        document.getElementById('holdCount').textContent = statsData.hold_recommendations;
        document.getElementById('sellCount').textContent = statsData.sell_avoidance;
        document.getElementById('totalCount').textContent = statsData.total;
        
        if (statsData.last_update) {
            const date = new Date(statsData.last_update);
            lastUpdate = date.toLocaleString();
            document.getElementById('lastUpdate').textContent = lastUpdate;
        }
        
        const buyResponse = await fetch(`${API_BASE}/api/buy-recommendations`);
        if (buyResponse.ok) {
            const buyJson = await buyResponse.json();
            buyData = buyJson.data || [];
            renderTable('buyTableBody', buyData);
        }
        
        const holdResponse = await fetch(`${API_BASE}/api/hold-recommendations`);
        if (holdResponse.ok) {
            const holdJson = await holdResponse.json();
            holdData = holdJson.data || [];
            renderTable('holdTableBody', holdData);
        }
        
        const sellResponse = await fetch(`${API_BASE}/api/sell-avoidance`);
        if (sellResponse.ok) {
            const sellJson = await sellResponse.json();
            sellData = sellJson.data || [];
            renderTable('sellTableBody', sellData);
        }
        
    } catch (error) {
        console.error('Error fetching data:', error);
        showError('Failed to connect to server. Make sure the server is running on http://localhost:5000');
    } finally {
        showLoading(false);
    }
}

// Render table rows with click handlers
function renderTable(tableId, data) {
    const tbody = document.getElementById(tableId);
    
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No data available</td></tr>';
        return;
    }
    
    let sortedData = [...data];
    if (sortColumn) {
        sortedData.sort((a, b) => compareValues(a[sortColumn], b[sortColumn]));
    }
    
    tbody.innerHTML = sortedData.map(stock => `
        <tr onclick="showStockDetails('${stock.symbol}')" style="cursor: pointer;">
            <td><strong>${stock.symbol || 'N/A'}</strong></td>
            <td>${stock.company_name || stock.name || 'N/A'}</td>
            <td class="stars">${getStarsHTML(stock.star_rating)}</td>
            <td>$${formatNumber(stock.price)}</td>
            <td>${formatNumber(stock.forward_peg, 2)}</td>
            <td>${formatNumber(stock.gp_a * 100, 1)}%</td>
            <td>${formatNumber(stock.roe * 100, 1)}%</td>
            <td>${formatNumber(stock.profit_margin * 100, 1)}%</td>
        </tr>
    `).join('');
}

// Color helper functions based on Novy-Marx paper thresholds
function getColorClass(value, type) {
    if (value === null || value === undefined || isNaN(value)) return '';
    
    const v = Number(value);
    
    switch(type) {
        case 'gp_a': // GP/A: ≥30% green, 15-30% yellow, <15% red
            if (v >= 30) return 'c-green';
            if (v >= 15) return 'c-yellow';
            return 'c-red';
        
        case 'gross_margin': // GM: ≥50% green, 30-50% yellow, <30% red
            if (v >= 50) return 'c-green';
            if (v >= 30) return 'c-yellow';
            return 'c-red';
        
        case 'roe': // ROE: ≥20% green, 10-20% yellow, <10% red
            if (v >= 20) return 'c-green';
            if (v >= 10) return 'c-yellow';
            return 'c-red';
        
        case 'pb_ratio': // P/B: ≤5 green, 5-15 yellow, >15 red (inverted)
            if (v <= 5) return 'c-green';
            if (v <= 15) return 'c-yellow';
            return 'c-red';
        
        case 'peg': // PEG: ≤1.0 green, 1.0-1.5 yellow, >1.5 red
            if (v <= 1.0) return 'peg-green';
            if (v <= 1.5) return 'peg-yellow';
            return 'peg-red';
        
        case 'performance': // Performance: ≥0% green, <0% red
            if (v >= 0) return 'perf-pos';
            return 'perf-neg';
        
        default:
            return '';
    }
}

function getBadgeClass(value, type) {
    const colorClass = getColorClass(value, type);
    if (colorClass === 'c-green' || colorClass === 'peg-green') return 'badge-green';
    if (colorClass === 'c-yellow' || colorClass === 'peg-yellow') return 'badge-yellow';
    if (colorClass === 'c-red' || colorClass === 'peg-red') return 'badge-red';
    return '';
}

function getHighlightClass(value, type) {
    const colorClass = getColorClass(value, type);
    if (colorClass === 'c-green' || colorClass === 'peg-green') return 'highlight-green';
    if (colorClass === 'c-yellow' || colorClass === 'peg-yellow') return 'highlight-yellow';
    if (colorClass === 'c-red' || colorClass === 'peg-red') return 'highlight-red';
    return '';
}

// Show stock details modal with professional color scheme
function showStockDetails(symbol) {
    // Find the stock in all data arrays
    let stock = null;
    if (buyData.length > 0) stock = buyData.find(s => s.symbol === symbol);
    if (!stock && holdData.length > 0) stock = holdData.find(s => s.symbol === symbol);
    if (!stock && sellData.length > 0) stock = sellData.find(s => s.symbol === symbol);
    
    if (!stock) {
        alert('Stock not found');
        return;
    }
    
    // Build modal content with color-coded metrics
    const modalContent = `
        <div class="modal-header">
            <h2>${stock.symbol} - ${stock.company_name || stock.name}</h2>
            <button onclick="closeModal()" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
            <div class="section">
                <h3>Basic Information</h3>
                <p><strong>Sector:</strong> ${stock.sector || 'N/A'}</p>
                <p><strong>Industry:</strong> ${stock.industry || 'N/A'}</p>
                <p><strong>Employees:</strong> ${formatNumber(stock.full_time_employees)}</p>
            </div>
            
            <div class="section">
                <h3>Price & Market Data</h3>
                <div class="metric-row">
                    <span class="metric-label">Current Price</span>
                    <span class="metric-value">$${formatNumber(stock.price)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Previous Close</span>
                    <span class="metric-value">$${formatNumber(stock.previous_close)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Day Range</span>
                    <span class="metric-value">$${formatNumber(stock.day_low)} - $${formatNumber(stock.day_high)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">52-Week Range</span>
                    <span class="metric-value">$${formatNumber(stock.fifty_two_week_low)} - $${formatNumber(stock.fifty_two_week_high)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Market Cap</span>
                    <span class="metric-value">${formatLargeNumber(stock.market_cap)}</span>
                </div>
            </div>
            
            <div class="section">
                <h3>Valuation Ratios</h3>
                <div class="metric-row">
                    <span class="metric-label">P/E Ratio (Trailing)</span>
                    <span class="metric-value">${formatNumber(stock.pe_ratio, 2)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Forward P/E</span>
                    <span class="metric-value">${formatNumber(stock.forward_pe, 2)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">PEG Ratio</span>
                    <span class="metric-value ${getColorClass(stock.peg_ratio, 'peg')}">${formatNumber(stock.peg_ratio, 2)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Forward PEG</span>
                    <span class="metric-value ${getColorClass(stock.forward_peg, 'peg')}">${formatNumber(stock.forward_peg, 2)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">P/B Ratio</span>
                    <span class="metric-value ${getColorClass(stock.pb_ratio, 'pb_ratio')}">${formatNumber(stock.pb_ratio, 2)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">P/S Ratio</span>
                    <span class="metric-value">${formatNumber(stock.ps_ratio, 2)}</span>
                </div>
            </div>
            
            <div class="section">
                <h3>Profitability Metrics (Novy-Marx)</h3>
                <div class="metric-row">
                    <span class="metric-label">GP/A (Gross Profit/Assets)</span>
                    <span class="metric-value ${getColorClass(stock.gp_a * 100, 'gp_a')}">${formatNumber(stock.gp_a * 100, 1)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Gross Margin</span>
                    <span class="metric-value ${getColorClass(stock.gross_margin * 100, 'gross_margin')}">${formatNumber(stock.gross_margin * 100, 1)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Profit Margin</span>
                    <span class="metric-value ${getColorClass(stock.profit_margin * 100, 'gross_margin')}">${formatNumber(stock.profit_margin * 100, 1)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">ROE (Return on Equity)</span>
                    <span class="metric-value ${getColorClass(stock.roe * 100, 'roe')}">${formatNumber(stock.roe * 100, 1)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">ROA (Return on Assets)</span>
                    <span class="metric-value ${getColorClass(stock.roa * 100, 'roe')}">${formatNumber(stock.roa * 100, 1)}%</span>
                </div>
            </div>
            
            <div class="section">
                <h3>Growth Metrics</h3>
                <div class="metric-row">
                    <span class="metric-label">Asset Growth</span>
                    <span class="metric-value ${getColorClass(stock.asset_growth * 100, 'roe')}">${formatNumber(stock.asset_growth * 100, 1)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Revenue Growth (TTM)</span>
                    <span class="metric-value ${getColorClass(stock.revenue_growth_ttm * 100, 'roe')}">${formatNumber(stock.revenue_growth_ttm * 100, 1)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Earnings Growth (Quarterly)</span>
                    <span class="metric-value ${getColorClass(stock.earnings_growth_quarterly * 100, 'roe')}">${formatNumber(stock.earnings_growth_quarterly * 100, 1)}%</span>
                </div>
            </div>
            
            <div class="section">
                <h3>Performance Data</h3>
                <div class="metric-row">
                    <span class="metric-label">6-Month Performance</span>
                    <span class="metric-value ${getColorClass(stock.perf_6m * 100, 'performance')}">${formatNumber(stock.perf_6m * 100, 1)}%</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">12-Month Performance</span>
                    <span class="metric-value ${getColorClass(stock.perf_12m * 100, 'performance')}">${formatNumber(stock.perf_12m * 100, 1)}%</span>
                </div>
            </div>
            
            <div class="section">
                <h3>Dividend Data</h3>
                <p><strong>Dividend Rate:</strong> $${formatNumber(stock.dividend_rate)}</p>
                <p><strong>Dividend Yield:</strong> ${formatNumber(stock.dividend_yield * 100, 2)}%</p>
                <p><strong>Payout Ratio:</strong> ${formatNumber(stock.payout_ratio * 100, 1)}%</p>
            </div>
            
            <div class="section">
                <h3>Balance Sheet Data</h3>
                <p><strong>Total Assets:</strong> ${formatLargeNumber(stock.total_assets)}</p>
                <p><strong>Total Debt:</strong> ${formatLargeNumber(stock.total_debt)}</p>
                <p><strong>Debt to Equity:</strong> ${formatNumber(stock.debt_to_equity, 2)}</p>
                <p><strong>Current Ratio:</strong> ${formatNumber(stock.current_ratio, 2)}</p>
            </div>
            
            <div class="section">
                <h3>Cash Flow Data</h3>
                <p><strong>Operating Cash Flow:</strong> ${formatLargeNumber(stock.operating_cash_flow)}</p>
                <p><strong>Free Cash Flow:</strong> ${formatLargeNumber(stock.free_cash_flow)}</p>
            </div>
            
            <div class="section">
                <h3>Scores & Ratings</h3>
                <div class="metric-row">
                    <span class="metric-label">Star Rating</span>
                    <span class="metric-value stars">${getStarsHTML(stock.star_rating)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Novy Marx Score</span>
                    <span class="metric-value">${formatNumber(stock.nm_score, 2)}</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Multi-Factor Score</span>
                    <span class="metric-value">${formatNumber(stock.mf_score, 2)}</span>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('modalContent').innerHTML = modalContent;
    document.getElementById('stockModal').style.display = 'flex';
}

// Close modal
function closeModal() {
    document.getElementById('stockModal').style.display = 'none';
}

// Get stars HTML
function getStarsHTML(stars) {
    const fullStars = Math.floor(stars);
    const hasHalfStar = stars % 1 >= 0.5;
    
    let html = '';
    for (let i = 0; i < fullStars; i++) {
        html += '★';
    }
    if (hasHalfStar) {
        html += '½';
    }
    return html + ` (${stars})`;
}

// Format number with commas and decimals
function formatNumber(num, decimals = 0) {
    if (num === null || num === undefined || isNaN(num)) return '-';
    return Number(num).toLocaleString('en-US', { 
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals 
    });
}

// Format large numbers (market cap, etc.)
function formatLargeNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '-';
    const n = Number(num);
    if (n >= 1e9) {
        return '$' + (n / 1e9).toFixed(2) + 'B';
    } else if (n >= 1e6) {
        return '$' + (n / 1e6).toFixed(2) + 'M';
    }
    return '$' + formatNumber(n);
}

// Compare values for sorting
function compareValues(a, b) {
    if (a === null || a === undefined) return 1;
    if (b === null || b === undefined) return -1;
    
    const numA = typeof a === 'string' ? parseFloat(a) : a;
    const numB = typeof b === 'string' ? parseFloat(b) : b;
    
    if (isNaN(numA)) return 1;
    if (isNaN(numB)) return -1;
    
    return sortDirection === 'asc' ? numA - numB : numB - numA;
}

// Sort table by column
function sortTable(column) {
    if (sortColumn === column) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortColumn = column;
        sortDirection = 'asc';
    }
    
    renderTable('buyTableBody', buyData);
    renderTable('holdTableBody', holdData);
    renderTable('sellTableBody', sellData);
}

// Show/hide loading spinner
function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'block' : 'none';
    document.getElementById('mainContent').style.opacity = show ? '0.5' : '1';
}

// Show error message
function showError(message) {
    alert(message);
}
