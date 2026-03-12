// Utility functions for the Value Screener

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
    
    switch(type) {
        case 'gp_a':
            if (v >= 30) return 'c-green';
            if (v >= 15) return 'c-yellow';
            return 'c-red';
        
        case 'gross_margin':
            if (v >= 50) return 'c-green';
            if (v >= 30) return 'c-yellow';
            return 'c-red';
        
        case 'roe':
            if (v >= 20) return 'c-green';
            if (v >= 10) return 'c-yellow';
            return 'c-red';
        
        case 'pb_ratio':
            if (v <= 5) return 'c-green';
            if (v <= 15) return 'c-yellow';
            return 'c-red';
        
        case 'peg':
            if (v <= 0.4) return 'peg-yellow';
            if (v <= 1.0) return 'peg-green';
            if (v <= 1.5) return 'peg-yellow';
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
