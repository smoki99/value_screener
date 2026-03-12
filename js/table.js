// Table module - handles rendering and sorting

/** @constant {string} Sort state */
let sortColumn = null;
let sortDirection = 'asc';

/**
 * Render table rows with click handlers
 * @param {string} tableId - The ID of the tbody element to populate
 * @param {Array} data - Array of stock objects to render
 */
function renderTable(tableId, data) {
    const tbody = document.getElementById(tableId);
    
    if (!tbody || data.length === 0) {
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">No data available</td></tr>';
        }
        return;
    }
    
    let sortedData = [...data];
    if (sortColumn) {
        sortedData.sort((a, b) => compareValuesForSort(a[sortColumn], b[sortColumn]));
    }
    
    tbody.innerHTML = sortedData.map(stock => generateRowHTML(stock)).join('');
}

/**
 * Get price arrow HTML based on 6M and 12M performance
 * @param {number|null} perf6m - 6-month performance value
 * @param {number|null} perf12m - 12-month performance value
 * @returns {string} Arrow HTML string
 */
function getPriceArrow(perf6m, perf12m) {
    if (perf6m === null || perf12m === null) return '';
    
    const p6 = Number(perf6m);
    const p12 = Number(perf12m);
    
    if (p6 > 0 && p12 > 0) return '<span class="arrow-up"></span>';
    if (p6 < 0 && p12 < 0) return '<span class="arrow-down"></span>';
    return '<span class="arrow-sideways"></span>';
}

/**
 * Generate HTML for a single table row
 * @param {object} stock - Stock object to render
 * @returns {string} Row HTML string
 */
function generateRowHTML(stock) {
    const forwardPegClass = getColorClass(stock.forward_peg, 'peg');
    let pegArrow = '';
    if (stock.forward_peg !== null && stock.peg_ratio !== null) {
        pegArrow = stock.forward_peg < stock.peg_ratio ? '<span class="arrow-up"></span>' : '<span class="arrow-down"></span>';
    }
    
    const priceArrow = getPriceArrow(stock.perf_6m, stock.perf_12m);
    
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
}

/**
 * Sort table by column
 */
function sortTable(column) {
    if (sortColumn === column) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortColumn = column;
        sortDirection = 'asc';
    }
    
    const sortedAllData = [...allData].sort((a, b) => compareValuesForSort(a[column], b[column]));
    const sortedBuyData = [...buyData].sort((a, b) => compareValuesForSort(a[column], b[column]));
    const sortedHoldData = [...holdData].sort((a, b) => compareValuesForSort(a[column], b[column]));
    const sortedSellData = [...sellData].sort((a, b) => compareValuesForSort(a[column], b[column]));
    
    renderTable('allTableBody', sortedAllData);
    renderTable('buyTableBody', sortedBuyData);
    renderTable('holdTableBody', sortedHoldData);
    renderTable('sellTableBody', sortedSellData);
}

/**
 * Compare values for sorting
 */
function compareValuesForSort(a, b) {
    if (a === null || a === undefined) return 1;
    if (b === null || b === undefined) return -1;
    
    const numA = typeof a === 'string' ? parseFloat(a) : a;
    const numB = typeof b === 'string' ? parseFloat(b) : b;
    
    if (isNaN(numA)) return 1;
    if (isNaN(numB)) return -1;
    
    return sortDirection === 'asc' ? numA - numB : numB - numA;
}
