# Financial Ratio Implementation Plan

This document outlines the verification, correction, and testing plan for all financial ratios.
Based on `financial_ratio.md` specification from `original.py`.

---

## 1. Forward PEG Calculation

### Current Implementation (`modules/metrics.py`)
```python
def calculate_forward_peg(info: dict, growth_rate: float | None = None) -> float | None:
    try:
        forward_pe = info.get('forwardPE')
        growth = growth_rate if growth_rate is not None else info.get('earningsGrowth')
        if forward_pe and growth and growth > 0:
            return float(forward_pe) / (float(growth) * 100)
    except (KeyError, TypeError):
        pass
    return None
```

### Check 1: Correctly Implemented?
**YES** ✓ - The formula `forward_pe / (growth * 100)` correctly converts decimal growth to percentage.

### Check 2: Corrections Needed
**NO CORRECTIONS NEEDED** - Implementation matches specification.

### Check 3: Unit Test Plan
```python
def test_calculate_forward_peg():
    # Test with valid data (growth as decimal)
    info = {'forwardPE': 15.0}
    result = calculate_forward_peg(info, growth_rate=0.25)  # 25% growth
    assert result == 0.60, f"Expected 0.60, got {result}"  # 15 / 25 = 0.60
    
    # Test with invalid data (no forward PE)
    info = {}
    result = calculate_forward_peg(info, growth_rate=0.25)
    assert result is None
    
    # Test with zero growth
    info = {'forwardPE': 15.0}
    result = calculate_forward_peg(info, growth_rate=0.0)
    assert result is None
```

---

## 2. GAAP PEG Calculation

### Current Implementation (`modules/metrics.py`)
```python
def calculate_gaap_peg(info: dict) -> float | None:
    try:
        pe = info.get('trailingPE')
        growth = info.get('earningsGrowth')
        if pe and growth and growth > 0:
            return float(pe) / float(growth)
    except (KeyError, TypeError):
        pass
    return None
```

### Check 1: Correctly Implemented?
**NO** ✗ - Missing the `* 100` conversion. Should be `pe / (growth * 100)`.

### Check 2: Corrections Needed
```python
def calculate_gaap_peg(info: dict) -> float | None:
    try:
        pe = info.get('trailingPE')
        growth = info.get('earningsGrowth')
        if pe and growth and growth > 0:
            return float(pe) / (float(growth) * 100)  # Added * 100
    except (KeyError, TypeError):
        pass
    return None
```

### Check 3: Unit Test Plan
```python
def test_calculate_gaap_peg():
    # Test with valid data
    info = {'trailingPE': 20.0, 'earningsGrowth': 0.40}  # 40% growth
    result = calculate_gaap_peg(info)
    assert result == 0.50, f"Expected 0.50, got {result}"  # 20 / 40 = 0.50
```

---

## 3. Growth Source Priority (GE-2Y → EE-2Y → GE-1Y/EE-1Y → info-eGr)

### Current Implementation (`modules/fetcher.py`)
```python
def fetch_growth_estimates(stock):
    result = {
        'growth_5y': None,
        'growth_2y': None,
        'growth_1y': None,
        'source': 'N/A',
    }
```

### Check 1: Correctly Implemented?
**PARTIALLY** - Need to verify the full implementation matches specification.

### Check 2: Corrections Needed
Need to implement:
- GE-2Y blended calculation from `stock.growth_estimates['stockTrend']`
- EE-2Y blended calculation from `stock.earnings_estimate['growth']`
- Dampening formula for info-based estimates

### Check 3: Unit Test Plan
```python
def test_fetch_growth_estimates():
    # Mock stock with growth_estimates data
    mock_stock = type('MockStock', (), {
        'growth_estimates': pd.DataFrame({
            'stockTrend': {'0y': 0.20, '+1y': 0.30}
        }, index=['0y', '+1y'])
    })()
    
    result = fetch_growth_estimates(mock_stock)
    # Blend = ((1 + 0.20) * (1 + 0.30)) ** 0.5 - 1 = 0.249
    assert abs(result['growth_2y'] - 0.249) < 0.01
```

---

## 4. Novy-Marx Scoring Model

### Current Implementation (`modules/scoring.py`)
```python
def score_novy_marx(info, financials, balance_sheet, perf_6m, perf_12m, growth_estimates):
    try:
        gm = info.get('grossMargins')
        if not gm or gm <= 0.20:
            return 0
        gpa = info.get('profitMargins')
        if not gpa or gpa <= 0.05:
            return 0
        roe = info.get('returnOnEquity')
        if not roe or roe < 0.10:
            return 0
```

### Check 1: Correctly Implemented?
**NO** ✗ - Current implementation uses simplified thresholds, not the weighted scoring model from specification.

### Check 2: Corrections Needed
```python
def score_novy_marx(s_gpa: int, s_pb: int, s_momentum: int) -> float:
    """Calculate Novy-Marx score using star ratings."""
    weights = {
        'gpa': (s_gpa, 0.40),
        'pb': (s_pb, 0.35),
        'momentum': (s_momentum, 0.25)
    }
    active = {k: (score, w) for k, (score, w) in weights.items() if score > 0}
    if len(active) < 2:
        return 0
    total_weight = sum(w for _, w in active.values())
    weighted_sum = sum(score * (w / total_weight) for score, w in active.values())
    
    # Penalties
    if s_pb == 1:
        weighted_sum = min(weighted_sum, 3.0)
    missing = 3 - len(active)
    weighted_sum -= missing * 0.15
    return round(max(weighted_sum, 0), 1)
```

### Check 3: Unit Test Plan
```python
def test_score_novy_marx():
    # All stars at max (4 each)
    result = score_novy_marx(4, 4, 4)
    assert result == 4.0, f"Expected 4.0, got {result}"
    
    # Mixed scores
    result = score_novy_marx(3, 2, 4)
    expected = round((3 * 0.40 + 2 * 0.35 + 4 * 0.25), 1)  # 2.9
    assert result == expected
```

---

## 5. Multi-Factor Scoring Model

### Current Implementation (`modules/scoring.py`)
```python
def score_multi_factor(info, financials, balance_sheet, perf_6m, perf_12m, growth_estimates):
    try:
        gaap_peg, forward_peg = get_peg_values(info, financials)
        peg_score = 0
        if gaap_peg and gaap_peg <= 1.5:
            peg_score = 20 - int(gaap_peg * 10)
```

### Check 1: Correctly Implemented?
**NO** ✗ - Current implementation uses simplified scoring, not the weighted model.

### Check 2: Corrections Needed
```python
def score_multi_factor(s_gpa: int, s_roe: int, s_pb: int, s_fpeg: int, s_momentum: int) -> float:
    """Calculate multi-factor score using star ratings."""
    weights = {
        'gpa': (s_gpa, 0.25),
        'roe': (s_roe, 0.20),
        'pb': (s_pb, 0.20),
        'peg': (s_fpeg, 0.15),
        'momentum': (s_momentum, 0.20)
    }
    active = {k: (score, w) for k, (score, w) in weights.items() if score > 0}
    if len(active) < 2:
        return 0
    total_weight = sum(w for _, w in active.values())
    weighted_sum = sum(score * (w / total_weight) for score, w in active.values())
    
    # Penalties
    if s_pb == 1:
        weighted_sum = min(weighted_sum, 3.0)
    if s_fpeg == 1 and s_gpa <= 3:
        weighted_sum = min(weighted_sum, 3.0)
    missing = 5 - len(active)
    weighted_sum -= missing * 0.15
    return round(max(weighted_sum, 0), 1)
```

### Check 3: Unit Test Plan
```python
def test_score_multi_factor():
    # All stars at max (4 each)
    result = score_multi_factor(4, 4, 4, 4, 4)
    assert result == 4.0
```

---

## 6. Star Rating Thresholds

### Current Implementation (`modules/scoring.py`)
```python
def get_star_rating(peg: float | None) -> int:
    if peg is None:
        return 0
    if peg <= 0.75:
        return 5
```

### Check 1: Correctly Implemented?
**PARTIALLY** - Only implements PEG rating, not all metrics.

### Check 2: Corrections Needed
```python
def get_star_rating(value: float | None, thresholds: list[float], reverse: bool = False,
                    penalize_negative: bool = False) -> int:
    """Get star rating based on value and thresholds."""
    if value is None or pd.isna(value):
        return 0
    if penalize_negative and value < 0:
        return 1
    stars = 1
    for t in thresholds:
        if not reverse:
            if value >= t:
                stars += 1
        else:
            if value <= t:
                stars += 1
    return min(stars, 5)
```

### Check 3: Unit Test Plan
```python
def test_get_star_rating():
    # GP/A thresholds [0.1, 0.2, 0.3, 0.4]
    result = get_star_rating(0.35, [0.1, 0.2, 0.3, 0.4])
    assert result == 4
    
    # P/B thresholds (reverse) [40.0, 20.0, 10.0, 5.0]
    result = get_star_rating(8.0, [40.0, 20.0, 10.0, 5.0], reverse=True)
    assert result == 3
```

---

## 7. Quality Star Ratings

### Current Implementation (None found)

### Check 1: Correctly Implemented?
**NO** ✗ - Not implemented.

### Check 2: Corrections Needed
```python
def get_quality_rating(nm_score: float, mf_score: float) -> str:
    """Get quality rating based on best(NM, MF) score."""
    best = max(nm_score, mf_score)
    if best >= 4.5:
        return "★★★"
    elif best >= 3.5:
        return "★★"
    elif best >= 2.5:
        return "★"
    else:
        return "—"
```

### Check 3: Unit Test Plan
```python
def test_get_quality_rating():
    assert get_quality_rating(4.5, 3.0) == "★★★"
    assert get_quality_rating(3.5, 2.0) == "★★"
    assert get_quality_rating(2.5, 1.0) == "★"
    assert get_quality_rating(2.0, 1.5) == "—"
```

---

## 8. Asset Growth Calculation

### Current Implementation (`modules/fetcher.py`)
```python
def calculate_asset_growth(balance_sheet):
    try:
        if balance_sheet is None or balance_sheet.empty:
            return None
        assets = balance_sheet.loc['Total Assets']
        if len(assets) >= 2:
            latest = assets.iloc[0]
            previous = assets.iloc[1]
            if previous > 0:
                return (latest - previous) / previous
    except (KeyError, IndexError):
        pass
    return None
```

### Check 1: Correctly Implemented?
**YES** ✓ - Matches specification exactly.

### Check 2: Corrections Needed
**NO CORRECTIONS NEEDED**

### Check 3: Unit Test Plan
```python
def test_calculate_asset_growth():
    balance_sheet = pd.DataFrame({
        'Total Assets': [100.0, 95.0]
    }, index=['Total Assets'])
    result = calculate_asset_growth(balance_sheet)
    assert abs(result - 0.0526) < 0.01  # (100-95)/95
```

---

## Summary of Required Changes

| Module | Function | Status | Action |
|--------|----------|--------|--------|
| metrics.py | calculate_gaap_peg | ✗ Wrong | Add `* 100` to formula |
| scoring.py | score_novy_marx | ✗ Simplified | Replace with weighted model |
| scoring.py | score_multi_factor | ✗ Simplified | Replace with weighted model |
| scoring.py | get_star_rating | ⚠ Partial | Add generic version with thresholds |
| scoring.py | get_quality_rating | ✗ Missing | Implement new function |

---

## Test File: `tests/test_financial_ratios.py`

```python
"""
Unit tests for financial ratio calculations.
"""
import pandas as pd
from modules.metrics import calculate_gaap_peg, calculate_forward_peg
from modules.scoring import (
    score_novy_marx,
    score_multi_factor,
    get_star_rating,
    get_quality_rating
)
from modules.fetcher import calculate_asset_growth

def test_calculate_forward_peg():
    """Test Forward PEG calculation."""
    info = {'forwardPE': 15.0}
    result = calculate_forward_peg(info, growth_rate=0.25)
    assert result == 0.60

def test_calculate_gaap_peg():
    """Test GAAP PEG calculation."""
    info = {'trailingPE': 20.0, 'earningsGrowth': 0.40}
    result = calculate_gaap_peg(info)
    assert result == 0.50

def test_score_novy_marx():
    """Test Novy-Marx scoring."""
    result = score_novy_marx(4, 4, 4)
    assert result == 4.0

def test_score_multi_factor():
    """Test multi-factor scoring."""
    result = score_multi_factor(4, 4, 4, 4, 4)
    assert result == 4.0

def test_get_star_rating():
    """Test star rating thresholds."""
    result = get_star_rating(0.35, [0.1, 0.2, 0.3, 0.4])
    assert result == 4

def test_get_quality_rating():
    """Test quality rating."""
    assert get_quality_rating(4.5, 3.0) == "★★★"

def test_calculate_asset_growth():
    """Test asset growth calculation."""
    balance_sheet = pd.DataFrame({
        'Total Assets': [100.0, 95.0]
    }, index=['Total Assets'])
    result = calculate_asset_growth(balance_sheet)
    assert abs(result - 0.0526) < 0.01
```
</parameter> </function> }</tool_call>