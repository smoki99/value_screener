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

// Show stock details modal
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
    
    // Build modal content
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
                <p><strong>Current Price:</strong> $${formatNumber(stock.price)}</p>
                <p><strong>Previous Close:</strong> $${formatNumber(stock.previous_close)}</p>
                <p><strong>Day Range:</strong> $${formatNumber(stock.day_low)} - $${formatNumber(stock.day_high)}</p>
                <p><strong>52-Week Range:</strong> $${formatNumber(stock.fifty_two_week_low)} - $${formatNumber(stock.fifty_two_week_high)}</p>
                <p><strong>Market Cap:</strong> ${formatLargeNumber(stock.market_cap)}</p>
            </div>
            
            <div class="section">
                <h3>Valuation Ratios</h3>
                <p><strong>P/E Ratio (Trailing):</strong> ${formatNumber(stock.pe_ratio, 2)}</p>
                <p><strong>Forward P/E:</strong> ${formatNumber(stock.forward_pe, 2)}</p>
                <p><strong>PEG Ratio:</strong> ${formatNumber(stock.peg_ratio, 2)}</p>
                <p><strong>Forward PEG:</strong> ${formatNumber(stock.forward_peg, 2)}</p>
                <p><strong>P/B Ratio:</strong> ${formatNumber(stock.pb_ratio, 2)}</p>
                <p><strong>P/S Ratio:</strong> ${formatNumber(stock.ps_ratio, 2)}</p>
            </div>
            
            <div class="section">
                <h3>Profitability Metrics</h3>
                <p><strong>GP/A (Gross Profit/Assets):</strong> ${formatNumber(stock.gp_a * 100, 1)}%</p>
                <p><strong>Gross Margin:</strong> ${formatNumber(stock.gross_margin * 100, 1)}%</p>
                <p><strong>Profit Margin:</strong> ${formatNumber(stock.profit_margin * 100, 1)}%</p>
                <p><strong>ROE (Return on Equity):</strong> ${formatNumber(stock.roe * 100, 1)}%</p>
                <p><strong>ROA (Return on Assets):</strong> ${formatNumber(stock.roa * 100, 1)}%</p>
            </div>
            
            <div class="section">
                <h3>Growth Metrics</h3>
                <p><strong>Asset Growth:</strong> ${formatNumber(stock.asset_growth * 100, 1)}%</p>
                <p><strong>Revenue Growth (TTM):</strong> ${formatNumber(stock.revenue_growth_ttm * 100, 1)}%</p>
                <p><strong>Earnings Growth (Quarterly):</strong> ${formatNumber(stock.earnings_growth_quarterly * 100, 1)}%</p>
            </div>
            
            <div class="section">
                <h3>Performance Data</h3>
                <p><strong>6-Month Performance:</strong> ${formatNumber(stock.perf_6m * 100, 1)}%</p>
                <p><strong>12-Month Performance:</strong> ${formatNumber(stock.perf_12m * 100, 1)}%</p>
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
                <p><strong>Star Rating:</strong> ${getStarsHTML(stock.star_rating)}</p>
                <p><strong>Novy Marx Score:</strong> ${formatNumber(stock.nm_score, 2)}</p>
                <p><strong>Multi-Factor Score:</strong> ${formatNumber(stock.mf_score, 2)}</p>
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
