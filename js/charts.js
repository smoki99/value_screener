// Charts module - handles gauge and candlestick charts

// Chart instances for cleanup
let gaugeCharts = {};
let candlestickChart = null;

/**
 * Create center text plugin for Chart.js doughnut charts
 */
function createCenterTextPlugin(text, fontSize) {
    return {
        id: 'centerText',
        afterDraw: function(chart) {
            const ctx = chart.ctx;
            const width = chart.width;
            const height = chart.height;
            
            ctx.save();
            ctx.font = 'bold ' + fontSize + 'px Arial';
            ctx.fillStyle = '#333';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(text, width / 2, height / 2);
            ctx.restore();
        }
    };
}

/**
 * Create gauge chart using Chart.js
 */
function createGaugeChart(canvasElement, value, label) {
    if (!canvasElement) return null;
    
    const canvasId = canvasElement.id || 'gauge_' + Math.random().toString(36).substr(2, 9);
    
    if (gaugeCharts[canvasId]) {
        gaugeCharts[canvasId].destroy();
    }
    
    let arcColor;
    const v = Number(value);
    // For negative values: show red arc proportional to magnitude, display actual value
    const gaugeValue = Math.abs(v);
    
    if (v >= 20) { arcColor = '#3fb950'; }
    else if (v >= 10) { arcColor = '#d29922'; }
    else { arcColor = '#f85149'; }
    
    const percentText = v.toFixed(1) + '%';
    
    canvasElement.width = 200;
    canvasElement.height = 200;
    
    const chart = new Chart(canvasElement, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [gaugeValue, 100 - gaugeValue],
                backgroundColor: [
                    arcColor,
                    '#e9ecef'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: false,
            maintainAspectRatio: false,
            aspectRatio: 1,
            cutout: '75%',
            layout: {
                padding: 0,
                autoPadding: false
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
        
        // Prepare candlestick data
        const candleData = data.map(d => ({
            time: d.date,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));
        
        // Add candlestick series
        const candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });
        
        candleSeries.setData(candleData);
        
        // Set visible range to last year
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
 * Cleanup all charts
 */
function cleanupCharts() {
    for (const key in gaugeCharts) {
        if (gaugeCharts[key]) {
            gaugeCharts[key].destroy();
        }
    }
    gaugeCharts = {};
    
    if (candlestickChart) {
        candlestickChart.remove();
        candlestickChart = null;
    }
}
