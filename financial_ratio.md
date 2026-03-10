# Financial Ratio Specification

Authoritative reference for NASDAQ-100 Cheapest Quality Screener calculations.
Based on Novy-Marx factor investing methodology.

---

## 1. Forward PEG Calculation

### Growth Source Priority (in order)

**Source 1: GE-2Y (Growth Estimates - Blended 2-Year)**
```
From stock.growth_estimates['stockTrend']:
- Get '0y' and '+1y' values
- Blend = ((1 + g_0y) * (1 + g_1y)) ** 0.5 - 1
- Use if blend > 0
```

**Source 2: EE-2Y (Earnings Estimate - Blended 2-Year)**
```
From stock.earnings_estimate['growth']:
- Get '0y' and '+1y' values
- Blend = ((1 + g_0y) * (1 + g_1y)) ** 0.5 - 1
- Use if blend > 0
```

**Source 3: GE-1Y / EE-1Y (Single Year from Estimates)**
```
If blended not available, use '+1y' value directly
- Cap at 60% growth
```

**Source 4: info-eGr (info['earningsGrowth'])**
```
Fallback to stock.info.get('earningsGrowth')
- Apply dampening formula:
  base = min(g1, 0.30)
  excess = max(0, g1 - 0.30) * 0.2
  dampened = base + excess
  final_cap = min(dampened, 0.50)
```

### Growth Capping Rules

| Source Type | Cap | Dampening |
|-------------|-----|----------|
| GE-2Y / EE-2Y | 60% | None |
| GE-1Y / EE-1Y | 60% | None |
| info-eGr | 50% (dampened) | Yes |

### Forward PEG Formula

```
forward_pe = stock.info.get('forwardPE')
growth_pct = growth * 100  # Convert decimal to percentage
peg = forward_pe / growth_pct
```

**Critical:** Growth must be converted from decimal (e.g., 0.25) to percentage (25) before division.

### Validation

- Reject if peg < 0 or peg > 50
- Return None, None, "N/A" if forward_pe <= 0 or growth not available

---

## 2. GAAP PEG Calculation

### Formula

```
trailing_pe = stock.info.get('trailingPE')
net_income = financials.loc['Net Income']
latest = net_income.iloc[0]
ostest = net_income.iloc[-1]
years = len(net_income) - 1

cagr = (latest / oldest) ** (1 / years) - 1
growth_pct = cagr * 100
peg = trailing_pe / growth_pct
```

### Conditions
- Return None if trailing_pe <= 0
- Return None if oldest <= 0 or latest <= 0
- Return None if growth_pct <= 0

---

## 3. Novy-Marx Scoring Model

### Components & Weights

| Factor | Weight | Description |
|--------|--------|-------------|
| GP/A | 40% | Gross Profit / Total Assets |
| P/B | 35% | Price to Book (inverse) |
| Momentum 12M | 25% | 12-month performance |

### Calculation

```
weights = {
    'gpa': (s_gpa, 0.40),
    'pb': (s_pb, 0.35),
    'momentum': (s_momentum, 0.25)
}
active = {k: (score, w) for k, (score, w) in weights.items() if score > 0}
total_weight = sum(w for _, w in active.values())
weighted_sum = sum(score * (w / total_weight) for score, w in active.values())
```

### Penalties
- If P/B star = 1: cap weighted_sum at 3.0
- Missing factors: subtract 0.15 per missing factor
- Minimum score: 0

---

## 4. Multi-Factor Scoring Model

### Components & Weights

| Factor | Weight | Description |
|--------|--------|-------------|
| GP/A | 25% | Gross Profit / Total Assets |
| ROE | 20% | Return on Equity |
| P/B | 20% | Price to Book (inverse) |
| fPEG | 15% | Forward PEG (inverse) |
| Momentum 12M | 20% | 12-month performance |

### Calculation

```
weights = {
    'gpa': (s_gpa, 0.25),
    'roe': (s_roe, 0.20),
    'pb': (s_pb, 0.20),
    'peg': (s_fwd_peg, 0.15),
    'momentum': (s_momentum, 0.20)
}
```

### Penalties
- If P/B star = 1: cap weighted_sum at 3.0
- If fPEG star = 1 AND GP/A <= 3: cap weighted_sum at 3.0
- Missing factors: subtract 0.15 per missing factor
- Minimum score: 0

---

## 5. Star Rating Thresholds

### GP/A (Gross Profit / Assets)
| Stars | Threshold |
|-------|-----------|
| ★ | ≥ 0.10 |
| ★★ | ≥ 0.20 |
| ★★★ | ≥ 0.30 |
| ★★★★ | ≥ 0.40 |

### ROE (Return on Equity)
| Stars | Threshold |
|-------|-----------|
| ★ | ≥ 0.05 |
| ★★ | ≥ 0.10 |
| ★★★ | ≥ 0.20 |
| ★★★★ | ≥ 0.30 |

**Note:** Penalize negative ROE (return 1 star)

### P/B (Price to Book) - Inverse
| Stars | Threshold |
|-------|-----------|
| ★ | ≤ 40.0 |
| ★★ | ≤ 20.0 |
| ★★★ | ≤ 10.0 |
| ★★★★ | ≤ 5.0 |

**Note:** Penalize negative P/B (return 1 star)

### fPEG (Forward PEG) - Inverse
| Stars | Threshold |
|-------|-----------|
| ★ | ≤ 2.5 |
| ★★ | ≤ 2.0 |
| ★★★ | ≤ 1.5 |
| ★★★★ | ≤ 1.0 |

### Momentum 12M
| Stars | Threshold |
|-------|-----------|
| ★ | ≥ 0.00 |
| ★★ | ≥ 0.10 |
| ★★★ | ≥ 0.25 |
| ★★★★ | ≥ 0.50 |

---

## 6. Quality Star Ratings

Based on best(NM, MF) score:

| Quality | Score Range |
|---------|-------------|
| ★★★ | ≥ 4.5 |
| ★★ | ≥ 3.5 |
| ★ | ≥ 2.5 |
| — | < 2.5 |

---

## 7. Asset Growth Calculation (Novy-Marx Control Factor)

### Formula

```
balance_sheet = stock.balance_sheet
assets = balance_sheet.loc['Total Assets']
latest = assets.iloc[0]
previous = assets.iloc[1]
asset_growth = (latest - previous) / previous
```

**Note:** Lower asset growth indicates better future returns (Novy-Marx finding)

---

## 8. Decile Ranking Methodology

### GP/A Decile (Higher is Better)

```
gpa_values = sorted([m['gp_a'] for m in metrics if m['gp_a'] is not None])
rank = sum(1 for v in gpa_values if v <= m['gp_a'])
pctl = rank / len(gpa_values)
decile = min(10, int(pctl * 10) + 1)
```

### P/B Decile (Lower is Better - Inverse)

```
pb_values = sorted([m['pb'] for m in metrics if m['pb'] is not None])
rank = sum(1 for v in pb_values if v >= m['pb'])  # Note: >= for inverse
pctl = rank / len(pb_values)
decile = min(10, int(pctl * 10) + 1)
```

### NM Rank (Combined Decile Score)

```
nm_rank = gp_a_decile + pb_decile  # Range: 2-20, higher is better
```

---

## 9. Color Coding Reference

### GP/A
| Color | Range |
|-------|-------|
| 🟢 Green | ≥ 30% |
| 🟡 Yellow | 15–30% |
| 🔴 Red | < 15% |

### Gross Margin
| Color | Range |
|-------|-------|
| 🟢 Green | ≥ 50% |
| 🟡 Yellow | 30–50% |
| 🔴 Red | < 30% |

### ROE
| Color | Range |
|-------|-------|
| 🟢 Green | ≥ 20% |
| 🟡 Yellow | 10–20% |
| 🔴 Red | < 10% |

### P/B
| Color | Range |
|-------|-------|
| 🟢 Green | ≤ 5.0 |
| 🟡 Yellow | 5–15 |
| 🔴 Red | > 15 |

### PEG
| Color | Range |
|-------|-------|
| 🟢 Green | ≤ 1.0 (GÜNSTIG) |
| 🟡 Yellow | 1.0–1.5 (FAIR) |
| 🔴 Red | > 1.5 (TEUER) |

### Asset Growth
| Color | Range |
|-------|-------|
| 🟢 Green | ≤ 10% |
| 🟡 Yellow | 10–25% |
| 🔴 Red | > 25% |

---

## Appendix: Key Formulas Summary

### Forward PEG (Primary)
```
p = forward_pe / (growth * 100)  # growth as decimal, multiply by 100 for percentage
```

### GAAP PEG (Secondary)
```
cagr = (latest_net_income / oldest_net_income) ** (1 / years) - 1
peg = trailing_pe / (cagr * 100)
```

### Novy-Marx Score
```
nm = weighted_sum(s_gpa*0.40, s_pb*0.35, s_momentum*0.25)
```

### Multi-Factor Score
```
mf = weighted_sum(s_gpa*0.25, s_roe*0.20, s_pb*0.20, s_fpeg*0.15, s_momentum*0.20)
```

### Quality Rating
```
quality = ★★★ if max(nm, mf) >= 4.5 else ★★ if >= 3.5 else ★ if >= 2.5 else —
```
