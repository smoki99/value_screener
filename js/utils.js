// Utility functions for the Value Screener

/** @constant {object} Color thresholds based on Novy-Marx paper */
const COLOR_THRESHOLDS = {
    gp_a: { green: 30, yellow: 15 },
    gross_margin: { green: 50, yellow: 30 },
    roe: { green: 20, yellow: 10 },
    pb_ratio: { green: 5, yellow: 15 },
    peg: { yellow_low: 0.4, green: 1.0, yellow_high: 1.5 }
};

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

// Get stars HTML with 1 decimal place - use empty star for half
function getStarsHTML(stars) {
    const fullStars = Math.floor(stars);
    const hasHalfStar = stars % 1 >= 0.5;
    
    let html = '';
    for (let i = 0; i < fullStars; i++) {
        html += '★';
    }
    if (hasHalfStar) {
        html += '☆';
    }
    return html + ` (${stars.toFixed(1)})`;
}

// Color helper functions based on Novy-Marx paper thresholds
function getColorClass(value, type) {
    if (value === null || value === undefined || isNaN(value)) return '';
    
    const v = Number(value);
    const thresholds = COLOR_THRESHOLDS[type];
    
    if (!thresholds) return '';
    
    switch(type) {
        case 'gp_a':
            if (v >= thresholds.green) return 'c-green';
            if (v >= thresholds.yellow) return 'c-yellow';
            return 'c-red';
        
        case 'gross_margin':
            if (v >= thresholds.green) return 'c-green';
            if (v >= thresholds.yellow) return 'c-yellow';
            return 'c-red';
        
        case 'roe':
            if (v >= thresholds.green) return 'c-green';
            if (v >= thresholds.yellow) return 'c-yellow';
            return 'c-red';
        
        case 'pb_ratio':
            if (v <= thresholds.green) return 'c-green';
            if (v <= thresholds.yellow) return 'c-yellow';
            return 'c-red';
        
        case 'peg':
            if (v <= thresholds.yellow_low) return 'peg-yellow';
            if (v <= thresholds.green) return 'peg-green';
            if (v <= thresholds.yellow_high) return 'peg-yellow';
            return 'peg-red';
        
        case 'performance':
            if (v >= 0) return 'perf-pos';
            return 'perf-neg';
        
        default:
            return '';
    }
}

// Calculate FCF Coverage Ratio
function getFCFCoverageRatio(freeCashFlow, dividendRate, marketCap, price) {
    if (!freeCashFlow || !dividendRate || !marketCap || !price) return null;
    
    const fcf = Number(freeCashFlow);
    const divRate = Number(dividendRate);
    const mktCap = Number(marketCap);
    const prc = Number(price);
    
    if (isNaN(fcf) || isNaN(divRate) || isNaN(mktCap) || isNaN(prc)) return null;
    
    const sharesOutstanding = mktCap / prc;
    const totalAnnualDividends = divRate * sharesOutstanding;
    
    if (totalAnnualDividends === 0) return null;
    
    return fcf / totalAnnualDividends;
}

// Get color class for FCF Coverage Ratio
function getFCFCoverageClass(freeCashFlow, dividendRate, marketCap, price) {
    const ratio = getFCFCoverageRatio(freeCashFlow, dividendRate, marketCap, price);
    
    if (ratio === null || isNaN(ratio)) return '';
    
    if (ratio >= 1) return 'c-green';
    if (ratio >= 0.5) return 'c-yellow';
    return 'c-red';
}

// Show/hide loading spinner
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    const content = document.getElementById('mainContent');
    if (spinner) spinner.style.display = show ? 'block' : 'none';
    if (content) content.style.opacity = show ? '0.5' : '1';
}

// Show error message
function showError(message) {
    alert(message);
}
