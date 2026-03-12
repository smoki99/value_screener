// Main application entry point - initializes everything
// Depends on: utils.js, api.js, table.js, search.js, charts.js

/**
 * Initialize the application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initSearch();
    
    // Fetch initial data
    fetchData();
    
    // Setup refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleRefresh);
    }
});

/**
 * Handle refresh button click - triggers fresh analysis and refetches data
 */
async function handleRefresh() {
    try {
        const success = await triggerAnalysis();
        if (success) {
            alert('Fresh analysis started! Data will update in a few moments...');
            setTimeout(fetchData, 5000);
        }
    } catch (error) {
        console.error('Error triggering analysis:', error);
        fetchData();
    }
}

/**
 * Show stock details modal with professional layout and gauge charts
 */
function showStockDetails(symbol) {
    let stock = getStockBySymbol(symbol);
    
    if (!stock) {
        alert('Stock not found');
        return;
    }
    
    const marketCap = Number(stock.market_cap || 0);
    let marketCapClass = 'market-cap-red';
    if (marketCap > 10e9) { marketCapClass = 'market-cap-green'; }
    else if (marketCap > 2e9) { marketCapClass = 'market-cap-yellow'; }
    
    const modalContent = `
        <div class="modal-header">
            <h2>${stock.symbol} - ${stock.company_name || stock.name}</h2>
            <button onclick="closeModal()" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
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
            
            <div id="chartContainer" class="chart-container">
                <div id="chartLoadingSpinner" class="chart-loading-spinner">
                    <p>Loading chart data...</p>
                </div>
                <div id="chartErrorMessage" class="chart-error-message"></div>
                
                <div class="chart-with-gauges-container">
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
                    
                    <div class="vertical-gauge-panel">
                        <div class="gauge-stack-item">
                            <span class="gauge-stack-label">GP/A</span>
                            <div class="compact-gauge-container">
                                <canvas id="gaugeGPA"></canvas>
                                <div class="gauge-stack-value">${formatNumber(stock.gp_a * 100, 1)}%</div>
                            </div>
                        </div>
                        
                        <div class="gauge-stack-item">
                            <span class="gauge-stack-label">Gross Margin</span>
                            <div class="compact-gauge-container">
                                <canvas id="gaugeGM"></canvas>
                                <div class="gauge-stack-value">${formatNumber(stock.gross_margin * 100, 1)}%</div>
                            </div>
                        </div>
                        
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
            
            <div class="section">
                <h3>Valuation Ratios</h3>
                <div class="valuation-grid">
                    <div class="metric-row"><span class="metric-label">P/E Ratio (Trailing)</span><span class="metric-value">${formatNumber(stock.pe_ratio, 2)}</span></div>
                    <div class="metric-row"><span class="metric-label">Forward P/E</span><span class="metric-value">${formatNumber(stock.forward_pe, 2)}</span></div>
                    <div class="metric-row"><span class="metric-label">P/B Ratio</span><span class="metric-value ${getColorClass(stock.pb_ratio, 'pb_ratio')}">${formatNumber(stock.pb_ratio, 2)}</span></div>
                    <div class="metric-row"><span class="metric-label">P/S Ratio</span><span class="metric-value">${formatNumber(stock.ps_ratio, 2)}</span></div>
                </div>
            </div>
            
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
            
            <div class="section">
                <h3>Balance Sheet</h3>
                <div class="valuation-grid">
                    <div class="metric-row"><span class="metric-label">Total Assets</span><span class="metric-value">${formatLargeNumber(stock.total_assets)}</span></div>
                    <div class="metric-row"><span class="metric-label">Total Debt</span><span class="metric-value">${formatLargeNumber(stock.total_debt)}</span></div>
                    <div class="metric-row"><span class="metric-label">Debt to Equity</span><span class="metric-value">${formatNumber(stock.debt_to_equity, 2)}</span></div>
                    <div class="metric-row"><span class="metric-label">Current Ratio</span><span class="metric-value">${formatNumber(stock.current_ratio, 2)}</span></div>
                </div>
            </div>
            
            <div class="section">
                <h3>Dividend Data</h3>
                <div class="valuation-grid">
                    <div class="metric-row"><span class="metric-label">Dividend Rate</span><span class="metric-value">$${formatNumber(stock.dividend_rate)}</span></div>
                    <div class="metric-row"><span class="metric-label">Dividend Yield</span><span class="metric-value">${formatNumber(stock.dividend_yield * 100, 2)}%</span></div>
                    <div class="metric-row"><span class="metric-label">Payout Ratio</span><span class="metric-value">${formatNumber(stock.payout_ratio * 100, 1)}%</span></div>
                    <div class="metric-row"><span class="metric-label">FCF Coverage</span><span class="metric-value ${getFCFCoverageClass(stock.free_cash_flow, stock.dividend_rate, stock.market_cap, stock.price)}">${formatNumber(getFCFCoverageRatio(stock.free_cash_flow, stock.dividend_rate, stock.market_cap, stock.price), 2)}</span></div>
                </div>
            </div>
            
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
    
    // Fetch and render chart after a short delay
    setTimeout(() => {
        fetchAndRenderChart(stock.symbol);
    }, 100);
    
    // Create gauge charts after another short delay
    setTimeout(() => {
        const gaugeGPA = document.getElementById('gaugeGPA');
        const gaugeGM = document.getElementById('gaugeGM');
        const gaugeROE = document.getElementById('gaugeROE');
        
        if (gaugeGPA) createGaugeChart(gaugeGPA, stock.gp_a * 100, 'GP/A');
        if (gaugeGM) createGaugeChart(gaugeGM, stock.gross_margin * 100, 'Gross Margin');
        if (gaugeROE) createGaugeChart(gaugeROE, stock.roe * 100, 'ROE');
    }, 200);
}

/**
 * Fetch and render candlestick chart with moving averages
 */
async function fetchAndRenderChart(symbol) {
    const loadingSpinner = document.getElementById('chartLoadingSpinner');
    if (loadingSpinner) loadingSpinner.style.display = 'block';
    
    try {
        const result = await fetchChartData(symbol);
        
        if (loadingSpinner) loadingSpinner.style.display = 'none';
        
        renderCandlestickChart(symbol, result.data, result);
        
    } catch (error) {
        console.error('Error fetching chart data:', error);
        
        if (loadingSpinner) loadingSpinner.style.display = 'none';
        
        const errorMessage = document.getElementById('chartErrorMessage');
        if (errorMessage) {
            errorMessage.textContent = `Failed to load chart: ${error.message}`;
            errorMessage.style.display = 'block';
        }
    }
}

/**
 * Render candlestick chart using Lightweight Charts
 */
function renderCandlestickChart(symbol, data, result) {
    const chartContainer = document.getElementById('chartWrapper');
    if (!chartContainer) return;
    
    // Cleanup existing chart
    if (candlestickChart) {
        candlestickChart.remove();
        candlestickChart = null;
    }
    
    try {
        if (typeof LightweightCharts === 'undefined') {
            throw new Error('Lightweight Charts library not loaded');
        }
        
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
        
        const candleData = data.map(d => ({
            time: d.date,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));
        
        const candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });
        
        candleSeries.setData(candleData);
        
        if (candleData.length >= 2) {
            const lastTime = candleData[candleData.length - 1].time;
            const oneYearBackIndex = Math.max(0, candleData.length - 365);
            const firstTime = candleData[oneYearBackIndex].time;
            chart.timeScale().setVisibleRange({
                from: firstTime,
                to: lastTime
            });
        }
        
        // Add SMA 50 line
        const sma50Data = data.filter(d => d.sma_50 !== null).map(d => ({
            time: d.date,
            value: d.sma_50,
        }));
        
        const sma50Series = chart.addSeries(LightweightCharts.LineSeries, {
            color: '#ff9800',
            lineWidth: 2,
            title: 'SMA 50',
        });
        
        sma50Series.setData(sma50Data);
        
        // Add SMA 200 line
        const sma200Data = data.filter(d => d.sma_200 !== null).map(d => ({
            time: d.date,
            value: d.sma_200,
        }));
        
        const sma200Series = chart.addSeries(LightweightCharts.LineSeries, {
            color: '#2196f3',
            lineWidth: 2,
            title: 'SMA 200',
        });
        
        sma200Series.setData(sma200Data);
        
        // Add 52-week high line
        if (result.fifty_two_week_high !== null && result.fifty_two_week_high !== undefined) {
            const fiftyTwoWeekHighSeries = chart.addSeries(LightweightCharts.LineSeries, {
                color: '#3fb950',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: '52W High'
            });
            const highLineData = [
                { time: data[0].date, value: result.fifty_two_week_high },
                { time: data[data.length - 1].date, value: result.fifty_two_week_high }
            ];
            fiftyTwoWeekHighSeries.setData(highLineData);
        }
        
        // Add 52-week low line
        if (result.fifty_two_week_low !== null && result.fifty_two_week_low !== undefined) {
            const fiftyTwoWeekLowSeries = chart.addSeries(LightweightCharts.LineSeries, {
                color: '#f85149',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: '52W Low'
            });
            const lowLineData = [
                { time: data[0].date, value: result.fifty_two_week_low },
                { time: data[data.length - 1].date, value: result.fifty_two_week_low }
            ];
            fiftyTwoWeekLowSeries.setData(lowLineData);
        }
        
        candlestickChart = chart;
        
    } catch (error) {
        console.error('Error rendering chart:', error);
        const errorMessage = document.getElementById('chartErrorMessage');
        if (errorMessage) {
            errorMessage.textContent = `Failed to render chart: ${error.message}`;
            errorMessage.style.display = 'block';
        }
    }
}

/**
 * Close modal and cleanup charts
 */
function closeModal() {
    document.getElementById('stockModal').style.display = 'none';
    
    // Destroy all gauge charts
    for (const key in gaugeCharts) {
        if (gaugeCharts[key]) {
            gaugeCharts[key].destroy();
        }
    }
    gaugeCharts = {};
}
