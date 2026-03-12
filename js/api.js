
/** @constant {Array} Global data storage for all stocks   */
let allData = [];
let buyData = [];
let holdData = [];
let sellData = [];

/**
 * Fetch all stock data from the API
 * Retrieves stats, all stocks, and categorized recommendations (buy/hold/sell)
 * @returns {Promise<void>}
 */
async function fetchData() {
    showLoading(true);
    
    try {
        // Fetch stats first
        const statsResponse = await fetch('/api/stats');
        if (!statsResponse.ok) throw new Error('Stats fetch failed');
        const statsData = await statsResponse.json();
        
        updateStatsDisplay(statsData);
        
        // Fetch all stocks data
        const allResponse = await fetch('/api/stocks');
        if (allResponse.ok) {
            const allJson = await allResponse.json();
            allData = allJson.data || [];
        }
        
        // Fetch buy recommendations
        const buyResponse = await fetch('/api/buy-recommendations');
        if (buyResponse.ok) {
            const buyJson = await buyResponse.json();
            buyData = buyJson.data || [];
        }
        
        // Fetch hold recommendations
        const holdResponse = await fetch('/api/hold-recommendations');
        if (holdResponse.ok) {
            const holdJson = await holdResponse.json();
            holdData = holdJson.data || [];
        }
        
        // Fetch sell avoidance
        const sellResponse = await fetch('/api/sell-avoidance');
        if (sellResponse.ok) {
            const sellJson = await sellResponse.json();
            sellData = sellJson.data || [];
        }
        
        // Render all tables with fetched data
        renderTable('allTableBody', allData);
        renderTable('buyTableBody', buyData);
        renderTable('holdTableBody', holdData);
        renderTable('sellTableBody', sellData);
        
    } catch (error) {
        console.error('Error fetching data:', error);
        showError('Failed to connect to server. Make sure the server is running.');
    } finally {
        showLoading(false);
    }
}

/**
 * Update stats display with fetched data
 */
function updateStatsDisplay(statsData) {
    const buyCount = document.getElementById('buyCount');
    const holdCount = document.getElementById('holdCount');
    const sellCount = document.getElementById('sellCount');
    const totalCount = document.getElementById('totalCount');
    const lastUpdate = document.getElementById('lastUpdate');
    
    if (buyCount) buyCount.textContent = statsData.buy_recommendations;
    if (holdCount) holdCount.textContent = statsData.hold_recommendations;
    if (sellCount) sellCount.textContent = statsData.sell_avoidance;
    if (totalCount) totalCount.textContent = statsData.total;
    
    if (statsData.last_update && lastUpdate) {
        const date = new Date(statsData.last_update);
        lastUpdate.textContent = date.toLocaleString();
    }
}

/**
 * Fetch historical chart data for a stock
 */
async function fetchChartData(symbol, period = '3y') {
    try {
        const response = await fetch(`/api/stock/${symbol}/history?period=${period}`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch chart data: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.error || !result.data || result.data.length === 0) {
            throw new Error(result.message || 'No historical data available');
        }
        
        return result;
    } catch (error) {
        console.error('Error fetching chart data:', error);
        throw error;
    }
}

/**
 * Trigger a fresh analysis from the server
 */
async function triggerAnalysis() {
    try {
        await fetch('/api/analyze', { method: 'POST' });
        return true;
    } catch (error) {
        console.error('Error triggering analysis:', error);
        return false;
    }
}

/**
 * Get stock data by symbol from any dataset
 */
function getStockBySymbol(symbol) {
    if (!symbol) return null;
    
    let stock = allData.find(s => s.symbol === symbol);
    if (stock) return stock;
    
    stock = buyData.find(s => s.symbol === symbol);
    if (stock) return stock;
    
    stock = holdData.find(s => s.symbol === symbol);
    if (stock) return stock;
    
    return sellData.find(s => s.symbol === symbol);
}
