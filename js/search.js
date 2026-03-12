// Search module - handles stock search functionality

// Debounce timer for search input
let searchTimeout;

/**
 * Initialize search event listeners and tab change handlers
 */
function initSearch() {
    const searchInput = document.getElementById('stockSearchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    
    if (searchInput) {
        searchInput.addEventListener('keyup', handleSearchInput);
    }
    
    if (clearBtn) {
        clearBtn.addEventListener('click', clearSearch);
    }
    
    // Add tab change event listeners to clear search when switching tabs
    const navLinks = document.querySelectorAll('#recommendationTabs .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', handleTabChange);
    });
}

/**
 * Handle tab change - clears search and resets all tables
 */
function handleTabChange() {
    // Clear search input
    const searchInput = document.getElementById('stockSearchInput');
    if (searchInput) {
        searchInput.value = '';
    }
    
    // Hide clear button
    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) {
        clearBtn.style.display = 'none';
    }
    
    // Clear search results count
    const resultsCount = document.getElementById('searchResultsCount');
    if (resultsCount) {
        resultsCount.textContent = '';
    }
    
    // Reset all tables to show full data
    renderTable('allTableBody', allData);
    renderTable('buyTableBody', buyData);
    renderTable('holdTableBody', holdData);
    renderTable('sellTableBody', sellData);
}

/**
 * Handle search input with debouncing
 */
function handleSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const searchTerm = this.value.trim().toLowerCase();
        if (searchTerm) {
            performSearch(searchTerm);
        } else {
            // Clear results and show all data when input is empty
            renderTable('allTableBody', allData);
            document.getElementById('searchResultsCount').textContent = '';
        }
    }, 300);
}

/**
 * Clear search input and reset table display
 */
function clearSearch() {
    const searchInput = document.getElementById('stockSearchInput');
    if (searchInput) {
        searchInput.value = '';
    }
    renderTable('allTableBody', allData);
    document.getElementById('searchResultsCount').textContent = '';
}

/**
 * Search stocks by symbol or company name
 */
function performSearch(searchTerm) {
    // Filter allData for matching symbol or company_name
    const results = allData.filter(stock => {
        const symbol = (stock.symbol || '').toLowerCase();
        const companyName = (stock.company_name || stock.name || '').toLowerCase();
        return symbol.includes(searchTerm) || companyName.includes(searchTerm);
    });
    
    // Update search results count
    document.getElementById('searchResultsCount').textContent = `Found ${results.length} result${results.length !== 1 ? 's' : ''}`;
    
    // Render results in a table with sorting applied if active
    const tbody = document.getElementById('allTableBody');
    let sortedResults = [...results];
    if (sortColumn) {
        sortedResults.sort((a, b) => compareValuesForSort(a[sortColumn], b[sortColumn]));
    }
    
    tbody.innerHTML = sortedResults.map(stock => generateRowHTML(stock)).join('');
}

/**
 * Search stocks by symbol or company name (legacy function for compatibility)
 */
function searchStocks(searchTerm) {
    performSearch(searchTerm);
}
