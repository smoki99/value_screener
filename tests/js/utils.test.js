// Unit tests for utils.js
// Import functions from js/utils.js using require
const fs = require('fs');
const path = require('path');

// Read and evaluate the utils.js file to get access to its functions
const vm = require('vm');
const utilsContent = fs.readFileSync(path.join(__dirname, '../../js/utils.js'), 'utf8');

// Create a context and run the code in it
const sandbox = {};
vm.runInNewContext(utilsContent, sandbox);

// Now we can access all functions from the sandbox
const { formatNumber, formatLargeNumber, getStarsHTML, getColorClass, getFCFCoverageRatio } = sandbox;

describe('formatNumber', () => {
    test('formats number with commas and decimals', () => {
        expect(formatNumber(1234.567, 2)).toBe('1,234.57');
    });

    test('handles null/undefined values', () => {
        expect(formatNumber(null)).toBe('-');
        expect(formatNumber(undefined)).toBe('-');
        expect(formatNumber(NaN)).toBe('-');
    });
});

describe('formatLargeNumber', () => {
    test('formats billions', () => {
        expect(formatLargeNumber(1234567890)).toBe('$1.23B');
    });

    test('formats millions', () => {
        expect(formatLargeNumber(1234567)).toBe('$1.23M');
    });

    test('handles null/undefined values', () => {
        expect(formatLargeNumber(null)).toBe('-');
        expect(formatLargeNumber(undefined)).toBe('-');
    });
});

describe('getStarsHTML', () => {
    test('returns full stars for whole numbers', () => {
        expect(getStarsHTML(4.0)).toContain('★★★★');
        expect(getStarsHTML(5.0)).toContain('★★★★★');
    });

    test('includes half star indicator when appropriate', () => {
        const result = getStarsHTML(4.5);
        expect(result).toContain('☆');
    });
});

describe('getColorClass', () => {
    test('returns green for high GP/A values', () => {
        expect(getColorClass(35, 'gp_a')).toBe('c-green');
    });

    test('returns yellow for moderate GP/A values', () => {
        expect(getColorClass(20, 'gp_a')).toBe('c-yellow');
    });

    test('returns red for low GP/A values', () => {
        expect(getColorClass(10, 'gp_a')).toBe('c-red');
    });

    test('handles null/undefined values', () => {
        expect(getColorClass(null, 'gp_a')).toBe('');
        expect(getColorClass(undefined, 'gp_a')).toBe('');
    });
});

describe('getFCFCoverageRatio', () => {
    test('calculates ratio correctly', () => {
        const result = getFCFCoverageRatio(1000000, 2.5, 100000000, 50);
        expect(result).toBeGreaterThan(0);
    });

    test('returns null for missing values', () => {
        expect(getFCFCoverageRatio(null, 2.5, 100000000, 50)).toBeNull();
        expect(getFCFCoverageRatio(1000000, null, 100000000, 50)).toBeNull();
    });
});

