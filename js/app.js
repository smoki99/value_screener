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
    // Trigger fresh analysis first
    try {
        await fetch(`${API_BASE}/api/analyze`, { method: 'POST' });
        alert('Fresh analysis started! Data will update in a few moments...');
        setTimeout(fetchData, 5000); // Wait 5 seconds for analysis to complete
    } catch (error) {
        console.error('Error triggering analysis:', error);
        fetchData(); // Just fetch current data
    }
});

// Fetch all stock data from API
async function fetchData() {
    showLoading(true);
    
    try {
        // Fetch stats first
        const statsResponse = await fetch(`${API_BASE}/api/stats`);
        if (!statsResponse.ok) throw new Error('Stats fetch failed');
        const statsData = await statsResponse.json();
        
        // Update statistics cards
        document.getElementById('buyCount').textContent = statsData.buy_recommendations;
        document.getElementById('holdCount').textContent = statsData.hold_recommendations;
        document.getElementById('sellCount').textContent = statsData.sell_avoidance;
        document.getElementById('totalCount').textContent = statsData.total;
        
        // Format last update time
        if (statsData.last_update) {
            const date = new Date(statsData.last_update);
            lastUpdate = date.toLocaleString();
            document.getElementById('lastUpdate').textContent = lastUpdate;
        }
        
        // Fetch buy recommendations
        const buyResponse = await fetch(`${API_BASE}/api/buy-recommendations`);
        if (buyResponse.ok) {
            const buyJson = await buyResponse.json();
            buyData = buyJson.data || [];
            renderTable('buyTableBody', buyData);
        }
        
        // Fetch hold recommendations
        const holdResponse = await fetch(`${API_BASE}/api/hold-recommendations`);
        if (holdResponse.ok) {
            const holdJson = await holdResponse.json();
            holdData = holdJson.data || [];
            renderTable('holdTableBody', holdData);
        }
        
        // Fetch sell avoidance
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

// Render table rows
function renderTable(tableId, data) {
    const tbody = document.getElementById(tableId);
    
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No data available</td></tr>';
        return;
    }
    
    // Sort data if sort column is set
    let sortedData = [...data];
    if (sortColumn) {
        sortedData.sort((a, b) => compareValues(a[sortColumn], b[sortColumn]));
    }
    
    tbody.innerHTML = sortedData.map(stock => `
        <tr>
            <td><strong>${stock.symbol || 'N/A'}</strong></td>
            <td>${stock.company_name || stock.name || 'N/A'}</td>
            <td class="stars">${getStarsHTML(stock.stars)}</td>
            <td>$${formatNumber(stock.price)}</td>
            <td>${formatNumber(stock.forward_peg, 2)}</td>
            <td>${formatNumber(stock.roe * 100, 1)}%</td>
            <td>${formatNumber(stock.profit_margin * 100, 1)}%</td>
        </tr>
    `).join('');
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

// Compare values for sorting
function compareValues(a, b) {
    // Handle null/undefined
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
    // Toggle direction or set new column
    if (sortColumn === column) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortColumn = column;
        sortDirection = 'asc';
    }
    
    // Re-render all tables with sorting
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