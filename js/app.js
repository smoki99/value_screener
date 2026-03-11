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

// Chart instances for cleanup
let gaugeCharts = {};
let candlestickChart = null;

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
    
    tbody.innerHTML = sortedData.map(stock => {
        // Get Forward PEG color class
        const forwardPegClass = getColorClass(stock.forward_peg, 'peg');
        
        // Compare Forward PEG with Trailing PEG for arrow indicator
        let pegArrow = '';
        if (stock.forward_peg !== null && stock.peg_ratio !== null) {
            if (stock.forward_peg < stock.peg_ratio) {
                pegArrow = '<span class="arrow-up"></span>';
            } else {
                pegArrow = '<span class="arrow-down"></span>';
            }
        }
        
        // Determine price arrow based on 6-month and 12-month performance
        let priceArrow = '';
        const perf6m = stock.perf_6m !== null ? Number(stock.perf_6m) : null;
        const perf12m = stock.perf_12m !== null ? Number(stock.perf_12m) : null;
        
        if (perf6m !== null && perf12m !== null) {
            // Green arrow up: price higher than both 6-month and 12-month ago
            if (perf6m > 0 && perf12m > 0) {
                priceArrow = '<span class="arrow-up"></span>';
            }
            // Red arrow down: price lower than both 6-month and 12-month ago
            else if (perf6m < 0 && perf12m < 0) {
                priceArrow = '<span class="arrow-down"></span>';
            }
            // Yellow sideward arrow: mixed results (one positive, one negative)
            else {
                priceArrow = '<span class="arrow-sideways"></span>';
            }
        }
        
        return `
        <tr onclick="showStockDetails('${stock.symbol}')" style="cursor: pointer;">
            <td><strong>${stock.symbol || 'N/A'}</strong></td>
            <td>${stock.company_name || stock.name || 'N/A'}</td>
            <td class="stars">${getStarsHTML(stock.star_rating)}</td>
            <td class="quality-rating">${stock.quality_rating || '-'}</td>
            <td>$${formatNumber(stock.price)} ${priceArrow}</td>
            <td class="${forwardPegClass}">${formatNumber(stock.forward_peg, 2)} ${pegArrow}</td>
            <td>${formatNumber(stock.gp_a * 100, 1)}%</td>
            <td>${formatNumber(stock.roe * 100, 1)}%</td>
            <td>${formatNumber(stock.profit_margin * 100, 1)}%</td>
        </tr>`;
    }).join('');
}



// Create center text plugin for Chart.js doughnut charts
function createCenterTextPlugin(text, fontSize) {
    return {
        id: 'centerText',
        afterDraw: function(chart) {
            const ctx = chart.ctx;
            const width = chart.width;
            const height = chart.height;
            
            // Save context
            ctx.save();
            
            // Set text properties - use larger font for visibility
            ctx.font = 'bold ' + fontSize + 'px Arial';
            ctx.fillStyle = '#333';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Draw text at center of chart
            ctx.fillText(text, width / 2, height / 2);
            
            // Restore context
            ctx.restore();
        }
    };
}

// Create gauge chart using Chart.js - FIXED to prevent absolute positioning wrappers
function createGaugeChart(canvasElement, value, label) {
    if (!canvasElement) return null;
    
    // Use canvas element's ID as key for cleanup
    const canvasId = canvasElement.id || 'gauge_' + Math.random().toString(36).substr(2, 9);
    
    // Destroy existing chart if any
    if (gaugeCharts[canvasId]) {
        gaugeCharts[canvasId].destroy();
    }
    
    // Determine color based on value thresholds
    let arcColor;
    const v = Number(value);
    
    if (v >= 20) { arcColor = '#3fb950'; } // Green
    else if (v >= 10) { arcColor = '#d29922'; } // Yellow
    else { arcColor = '#f85149'; } // Red
    
    // Format the percentage text for center display
    const percentText = v.toFixed(1) + '%';
    
    // Set explicit canvas dimensions to ensure proper rendering
    canvasElement.width = 200;
    canvasElement.height = 200;
    
    const chart = new Chart(canvasElement, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [v, 100 - v],
                backgroundColor: [
                    arcColor,
                    '#e9ecef'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: false,
            maintainAspectRatio: false, // CRITICAL: Prevent Chart.js from creating absolute positioning wrappers
            aspectRatio: 1,
            cutout: '75%',
            layout: {
                padding: 0,
                autoPadding: false // CRITICAL: Disable auto-padding that causes overflow
            },
            plugins: {
                datalabels: {
                    color: '#000',
                    font: {
                        weight: 'bold',
                        size: 14
                    },
                    formatter: (value) => { return Math.round(value) + '%'; }
                },
                legend: { display: false },
                tooltip: { enabled: false }
            }
        },
        plugins: [
            createCenterTextPlugin(percentText, 24)
        ]
    });
    
    gaugeCharts[canvasId] = chart;
    return chart;
}

// Fetch and render candlestick chart with moving averages
async function fetchAndRenderChart(symbol) {
    const chartContainer = document.getElementById('chartContainer');
    if (!chartContainer) return;
    
    // Show loading spinner
    const loadingSpinner = document.getElementById('chartLoadingSpinner');
    if (loadingSpinner) loadingSpinner.style.display = 'block';
    
    try {
        // Fetch historical data from API
        const response = await fetch(`${API_BASE}/api/stock/${symbol}/history?period=3y`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch chart data: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.error || !result.data || result.data.length === 0) {
            throw new Error(result.message || 'No historical data available');
        }
        
        // Hide loading spinner
        if (loadingSpinner) loadingSpinner.style.display = 'none';
        
        // Render the chart using Lightweight Charts
        renderCandlestickChart(symbol, result.data, result);
        
    } catch (error) {
        console.error('Error fetching chart data:', error);
        
        // Hide loading spinner
        if (loadingSpinner) loadingSpinner.style.display = 'none';
        
        // Show error message
        const errorMessage = document.getElementById('chartErrorMessage');
        if (errorMessage) {
            errorMessage.textContent = `Failed to load chart: ${error.message}`;
            errorMessage.style.display = 'block';
        }
    }
}

// Render candlestick chart using Lightweight Charts
function renderCandlestickChart(symbol, data, result) {
    const chartContainer = document.getElementById('chartWrapper');
    if (!chartContainer) return;
    
    // Destroy existing chart if any
    if (candlestickChart) {
        candlestickChart.remove();
        candlestickChart = null;
    }
    
    try {
        // Check if Lightweight Charts is loaded
        if (typeof LightweightCharts === 'undefined') {
            throw new Error('Lightweight Charts library not loaded');
        }
        
        console.log('Creating chart with Lightweight Charts version:', typeof LightweightCharts);
        
        // Create new Lightweight Charts instance
        const chart = LightweightCharts.createChart(chartContainer, {
            width: chartContainer.clientWidth,
            height: 350,
            layout: {
                background: { type: 'solid', color: '#f8f9fa' },
                textColor: '#666',
            },
            grid: {
                vertLines: { color: 'rgba(217, 217, 217, 0.3)' },
                horzLines: { color: 'rgba(217, 217, 217, 0.3)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
                timeVisible: true,
                secondsVisible: false,
            },
        });
        
        // Prepare candlestick data
        const candleData = data.map(d => ({
            time: d.date,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));
        
        console.log('Candle data sample:', candleData[0]);
        
        // Create candlestick series using addSeries with type
        const candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });
        
        candleSeries.setData(candleData);
        
        // Set visible range to show only the last 1 year (most recent data)
        if (candleData.length >= 2) {
            const lastTime = candleData[candleData.length - 1].time;
            // Find a point approximately 1 year before the end
            // Assuming daily data, ~365 days back from the end
            const oneYearBackIndex = Math.max(0, candleData.length - 365);
            const firstTime = candleData[oneYearBackIndex].time;
            chart.timeScale().setVisibleRange({
                from: firstTime,
                to: lastTime
            });
        }
        
        // Prepare 50-day SMA data
        const sma50Data = data.filter(d => d.sma_50 !== null).map(d => ({
            time: d.date,
            value: d.sma_50,
        }));
        
        // Create 50-day SMA line series (orange)
        const sma50Series = chart.addSeries(LightweightCharts.LineSeries, {
            color: '#ff9800',
            lineWidth: 2,
            title: 'SMA 50',
        });
        
        sma50Series.setData(sma50Data);
        
        // Prepare 200-day SMA data
        const sma200Data = data.filter(d => d.sma_200 !== null).map(d => ({
            time: d.date,
            value: d.sma_200,
        }));
        
        // Create 200-day SMA line series (blue)
        const sma200Series = chart.addSeries(LightweightCharts.LineSeries, {
            color: '#2196f3',
            lineWidth: 2,
            title: 'SMA 200',
        });
        
        sma200Series.setData(sma200Data);
        
        // Add 52-week high horizontal line (green dashed) using a constant line series
        if (result.fifty_two_week_high !== null && result.fifty_two_week_high !== undefined) {
            const fiftyTwoWeekHighSeries = chart.addSeries(LightweightCharts.LineSeries, {
                color: '#3fb950', // Green
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: '52W High'
            });
            // Create a constant line at the high price level using first and last data points
            const highLineData = [
                { time: data[0].date, value: result.fifty_two_week_high },
                { time: data[data.length - 1].date, value: result.fifty_two_week_high }
            ];
            fiftyTwoWeekHighSeries.setData(highLineData);
        }
        
        // Add 52-week low horizontal line (red dashed) using a constant line series
        if (result.fifty_two_week_low !== null && result.fifty_two_week_low !== undefined) {
            const fiftyTwoWeekLowSeries = chart.addSeries(LightweightCharts.LineSeries, {
                color: '#f85149', // Red
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: '52W Low'
            });
            // Create a constant line at the low price level using first and last data points
            const lowLineData = [
                { time: data[0].date, value: result.fifty_two_week_low },
                { time: data[data.length - 1].date, value: result.fifty_two_week_low }
            ];
            fiftyTwoWeekLowSeries.setData(lowLineData);
        }
        
        // Store chart reference for cleanup
        candlestickChart = chart;
        console.log('Chart created successfully');
        
    } catch (error) {
        console.error('Error rendering chart:', error);
        const errorMessage = document.getElementById('chartErrorMessage');
        if (errorMessage) {
            errorMessage.textContent = `Failed to render chart: ${error.message}`;
            errorMessage.style.display = 'block';
        }
    }
}

// Show stock details modal with professional layout and gauge charts
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
    
    // Determine market cap color
    const marketCap = Number(stock.market_cap || 0);
    let marketCapClass = 'market-cap-red';
    if (marketCap > 10e9) { marketCapClass = 'market-cap-green'; } // > $10B green
    else if (marketCap > 2e9) { marketCapClass = 'market-cap-yellow'; } // > $2B yellow
    
    // Build modal content with new professional layout including chart container
    const modalContent = `
        <div class="modal-header">
            <h2>${stock.symbol} - ${stock.company_name || stock.name}</h2>
            <button onclick="closeModal()" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
            <!-- Header Info Section -->
            <div class="header-info">
                <div class="symbol-row">
                    <div class="left-content">
                        <span class="symbol-name">${stock.symbol}</span>
                        <span class="company-name"> - ${stock.company_name || stock.name}</span><span class="stars"> ${getStarsHTML(stock.star_rating)}</span>
                    </div>
                    <div class="price-display">
                        <div class="current-price">Last Close: $${formatNumber(stock.price)}</div>
                    </div>
                </div>

                <div class="basic-info-row">
                    <span class="info-item"><span class="info-label">Sector:</span> ${stock.sector || 'N/A'}</span>
                    <span class="info-item"><span class="info-label">Industry:</span> ${stock.industry || 'N/A'}</span>
                    <span class="info-item"><span class="info-label">Employees:</span> ${formatNumber(stock.full_time_employees)}</span>
                    <span class="info-item"><span class="info-label">Marktkapitalisierung:</span> ${formatLargeNumber(stock.market_cap)}</span>
                    <span class="info-item"><span class="info-label">Stand:</span> ${new Date().toLocaleDateString('de-DE')}</span>
                </div>
            </div>
            
            <!-- Quick Stats Row -->
            <div class="quick-stats-row">
                <div class="stat-item">
                    <div class="stat-label">Forward P/E</div>
                    <div class="stat-value">${stock.forward_pe != null && stock.pe_ratio != null ? (stock.forward_pe < stock.pe_ratio ? '<span class="arrow-up"></span>' : '<span class="arrow-down"></span>') : ''}${formatNumber(stock.forward_pe, 2)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Trailing P/E</div>
                    <div class="stat-value">${formatNumber(stock.pe_ratio, 2)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Forward PEG</div>
                    <div class="stat-value ${getColorClass(stock.forward_peg, 'peg')}">${stock.forward_peg != null && stock.peg_ratio != null ? (stock.forward_peg < stock.peg_ratio ? '<span class="arrow-up"></span>' : '<span class="arrow-down"></span>') : ''}${formatNumber(stock.forward_peg, 2)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Trailing PEG</div>
                    <div class="stat-value ${getColorClass(stock.peg_ratio, 'peg')}">${formatNumber(stock.peg_ratio, 2)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Dividend Yield</div>
                    <div class="stat-value ${getFCFCoverageClass(stock.free_cash_flow, stock.dividend_rate, stock.market_cap, stock.price)}">${formatNumber(stock.dividend_yield * 100, 2)}%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Quality Score (NM)</div>
                    <div class="stat-value">${formatNumber(stock.nm_score, 1)}</div>
                </div>
            </div>
            
            <!-- Chart with Gauges Container - Side by side layout -->
            <div id="chartContainer" class="chart-container">
                <div id="chartLoadingSpinner" class="chart-loading-spinner">
                    <p>Loading chart data...</p>
                </div>
                <div id="chartErrorMessage" class="chart-error-message"></div>
                
                <!-- Main container with chart (left) and gauges panel (right) -->
                <div class="chart-with-gauges-container">
                    <!-- Left side: Candlestick chart -->
                    <div class="main-chart-area">
                        <div id="chartWrapper" class="chart-wrapper"></div>
                        <div class="chart-legend">
                            <div class="legend-item">
                                <span class="legend-line legend-line-50"></span>
                                <span>50-Day SMA</span>
                            </div>
                            <div class="legend-item">
                                <span class="legend-line legend-line-200"></span>
                                <span>200-Day SMA</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Right side: Vertical gauge panel -->
                    <div class="vertical-gauge-panel">
                        <!-- GP/A Gauge (top) -->
                        <div class="gauge-stack-item">
                            <span class="gauge-stack-label">GP/A</span>
                            <div class="compact-gauge-container">
                                <canvas id="gaugeGPA"></canvas>
                                <div class="gauge-stack-value">${formatNumber(stock.gp_a * 100, 1)}%</div>
                            </div>
                        </div>
                        
                        <!-- Gross Margin Gauge (middle) -->
                        <div class="gauge-stack-item">
                            <span class="gauge-stack-label">Gross Margin</span>
                            <div class="compact-gauge-container">
                                <canvas id="gaugeGM"></canvas>
                                <div class="gauge-stack-value">${formatNumber(stock.gross_margin * 100, 1)}%</div>
                            </div>
                        </div>
                        
                        <!-- ROE Gauge (bottom) -->
                        <div class="gauge-stack-item">
                            <span class="gauge-stack-label">ROE</span>
                            <div class="compact-gauge-container">
                                <canvas id="gaugeROE"></canvas>
                                <div class="gauge-stack-value">${formatNumber(stock.roe * 100, 1)}%</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Valuation Section -->
            <div class="section">
                <h3>Valuation Ratios</h3>
                <div class="valuation-grid">
                    <div class="metric-row"><span class="metric-label">P/E Ratio (Trailing)</span><span class="metric-value">${formatNumber(stock.pe_ratio, 2)}</span></div>
                    <div class="metric-row"><span class="metric-label">Forward P/E</span><span class="metric-value">${formatNumber(stock.forward_pe, 2)}</span></div>
                    <div class="metric-row"><span class="metric-label">P/B Ratio</span><span class="metric-value ${getColorClass(stock.pb_ratio, 'pb_ratio')}">${formatNumber(stock.pb_ratio, 2)}</span></div>
                    <div class="metric-row"><span class="metric-label">P/S Ratio</span><span class="metric-value">${formatNumber(stock.ps_ratio, 2)}</span></div>
                </div>
            </div>
            
            <!-- Growth & Performance Section -->
            <div class="section">
                <h3>Growth & Performance</h3>
                <div class="valuation-grid">
                    <div class="metric-row"><span class="metric-label">Asset Growth</span><span class="metric-value ${getColorClass(stock.asset_growth * 100, 'roe')}">${formatNumber(stock.asset_growth * 100, 1)}%</span></div>
                    <div class="metric-row"><span class="metric-label">Revenue Growth (TTM)</span><span class="metric-value ${getColorClass(stock.revenue_growth_ttm * 100, 'roe')}">${formatNumber(stock.revenue_growth_ttm * 100, 1)}%</span></div>
                    <div class="metric-row"><span class="metric-label">Earnings Growth (Q)</span><span class="metric-value ${getColorClass(stock.earnings_growth_quarterly * 100, 'roe')}">${formatNumber(stock.earnings_growth_quarterly * 100, 1)}%</span></div>
                    <div class="metric-row"><span class="metric-label">6M Performance</span><span class="metric-value ${getColorClass(stock.perf_6m * 100, 'performance')}">${formatNumber(stock.perf_6m * 100, 1)}%</span></div>
                    <div class="metric-row"><span class="metric-label">12M Performance</span><span class="metric-value ${getColorClass(stock.perf_12m * 100, 'performance')}">${formatNumber(stock.perf_12m * 100, 1)}%</span></div>
                </div>
            </div>
            
            <!-- Balance Sheet Summary -->
            <div class="section">
                <h3>Balance Sheet</h3>
                <div class="valuation-grid">
                    <div class="metric-row"><span class="metric-label">Total Assets</span><span class="metric-value">${formatLargeNumber(stock.total_assets)}</span></div>
                    <div class="metric-row"><span class="metric-label">Total Debt</span><span class="metric-value">${formatLargeNumber(stock.total_debt)}</span></div>
                    <div class="metric-row"><span class="metric-label">Debt to Equity</span><span class="metric-value">${formatNumber(stock.debt_to_equity, 2)}</span></div>
                    <div class="metric-row"><span class="metric-label">Current Ratio</span><span class="metric-value">${formatNumber(stock.current_ratio, 2)}</span></div>
                </div>
            </div>
            
            <!-- Dividend Data -->
            <div class="section">
                <h3>Dividend Data</h3>
                <div class="valuation-grid">
                    <div class="metric-row"><span class="metric-label">Dividend Rate</span><span class="metric-value">$${formatNumber(stock.dividend_rate)}</span></div>
                    <div class="metric-row"><span class="metric-label">Dividend Yield</span><span class="metric-value">${formatNumber(stock.dividend_yield * 100, 2)}%</span></div>
                    <div class="metric-row"><span class="metric-label">Payout Ratio</span><span class="metric-value">${formatNumber(stock.payout_ratio * 100, 1)}%</span></div>
                    <div class="metric-row"><span class="metric-label">FCF Coverage</span><span class="metric-value ${getFCFCoverageClass(stock.free_cash_flow, stock.dividend_rate, stock.market_cap, stock.price)}">${formatNumber(getFCFCoverageRatio(stock.free_cash_flow, stock.dividend_rate, stock.market_cap, stock.price), 2)}</span></div>
                </div>
            </div>
            
            <!-- Cash Flow -->
            <div class="section">
                <h3>Cash Flow</h3>
                <div class="valuation-grid">
                    <div class="metric-row"><span class="metric-label">Operating Cash Flow</span><span class="metric-value">${formatLargeNumber(stock.operating_cash_flow)}</span></div>
                    <div class="metric-row"><span class="metric-label">Free Cash Flow</span><span class="metric-value">${formatLargeNumber(stock.free_cash_flow)}</span></div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('modalContent').innerHTML = modalContent;
    document.getElementById('stockModal').style.display = 'flex';
    
    // Fetch and render candlestick chart after modal is shown
    setTimeout(() => {
        fetchAndRenderChart(stock.symbol);
    }, 100);
    
    // Create gauge charts after modal is shown - FIXED to pass canvas elements directly
    setTimeout(() => {
        const gaugeGPA = document.getElementById('gaugeGPA');
        const gaugeGM = document.getElementById('gaugeGM');
        const gaugeROE = document.getElementById('gaugeROE');
        
        if (gaugeGPA) createGaugeChart(gaugeGPA, stock.gp_a * 100, 'GP/A');
        if (gaugeGM) createGaugeChart(gaugeGM, stock.gross_margin * 100, 'Gross Margin');
        if (gaugeROE) createGaugeChart(gaugeROE, stock.roe * 100, 'ROE');
    }, 200);
}

// Close modal and cleanup charts
function closeModal() {
    document.getElementById('stockModal').style.display = 'none';
    
    // Cleanup all gauge chart instances
    for (const key in gaugeCharts) {
        if (gaugeCharts[key]) {
            gaugeCharts[key].destroy();
        }
    }
    gaugeCharts = {};
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
    
    // Sort all tables by the selected column
    const sortedBuyData = [...buyData].sort((a, b) => compareValuesForSort(a[column], b[column]));
    const sortedHoldData = [...holdData].sort((a, b) => compareValuesForSort(a[column], b[column]));
    const sortedSellData = [...sellData].sort((a, b) => compareValuesForSort(a[column], b[column]));
    
    renderTable('buyTableBody', sortedBuyData);
    renderTable('holdTableBody', sortedHoldData);
    renderTable('sellTableBody', sortedSellData);
}

// Compare values for sorting (used by sortTable)
function compareValuesForSort(a, b) {
    if (a === null || a === undefined) return 1;
    if (b === null || b === undefined) return -1;
    
    const numA = typeof a === 'string' ? parseFloat(a) : a;
    const numB = typeof b === 'string' ? parseFloat(b) : b;
    
    if (isNaN(numA)) return 1;
    if (isNaN(numB)) return -1;
    
    return sortDirection === 'asc' ? numA - numB : numB - numA;
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
        
        case 'peg': // PEG: <0.4 yellow, 0.4-1.0 green, >1.0 yellow, >1.5 red
            if (v <= 0.4) return 'peg-yellow';
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

// Calculate FCF Coverage Ratio
// Formula: free_cash_flow / (dividend_rate * shares_outstanding)
// where shares_outstanding = market_cap / price
function getFCFCoverageRatio(freeCashFlow, dividendRate, marketCap, price) {
    // Check if all required values are valid
    if (!freeCashFlow || !dividendRate || !marketCap || !price) return null;
    
    const fcf = Number(freeCashFlow);
    const divRate = Number(dividendRate);
    const mktCap = Number(marketCap);
    const prc = Number(price);
    
    // Check for valid numbers
    if (isNaN(fcf) || isNaN(divRate) || isNaN(mktCap) || isNaN(prc)) return null;
    
    // Calculate shares outstanding
    const sharesOutstanding = mktCap / prc;
    
    // Calculate total annual dividend payout
    const totalAnnualDividends = divRate * sharesOutstanding;
    
    // Avoid division by zero
    if (totalAnnualDividends === 0) return null;
    
    // Return FCF coverage ratio
    return fcf / totalAnnualDividends;
}

// Get color class for FCF Coverage Ratio
function getFCFCoverageClass(freeCashFlow, dividendRate, marketCap, price) {
    const ratio = getFCFCoverageRatio(freeCashFlow, dividendRate, marketCap, price);
    
    if (ratio === null || isNaN(ratio)) return '';
    
    // Green if >1 (fully covered), yellow if 0.5-1, red if <0.5
    if (ratio >= 1) return 'c-green';
    if (ratio >= 0.5) return 'c-yellow';
    return 'c-red';
}
