# College Exposure AI

@~/.claude/CLAUDE.md

---

## Project-Specific Notes

See the development journey documentation below for context on the data pipeline.

---

## Development Journey - November 6, 2025

### The Problem

User had a Jupyter notebook `descriptives.ipynb` that was supposed to:
1. Load AI occupation exposure (AIOE) scores from Felten et al.
2. Load ACS PUMS data with Field of Degree (FOD) codes
3. Map FOD → CIP4 (4-digit CIP codes)
4. Calculate AI exposure by CIP4
5. Merge with enrollment data (2019-2025)
6. Create visualizations

### Key Technical Decisions

#### Why DataFrame Not Dict for Crosswalk
- **Original**: Dict[FOD → CIP4] (one-to-one) ❌
- **Problem**: Lost 70% of mappings (188/191 FODs map to multiple CIP4s)
- **Solution**: DataFrame [FOD, CIP4, empirical_weight] ✓

#### Why Empirical Weights Not Equal Splits
- **Equal splits (1/N)**: Treats rare and common majors equally ❌
- **Empirical weights**: Based on actual 2019 enrollment ✓
- **Bayesian**: P(CIP4|FOD) estimated from observed data

#### Why Drop NAs Not Impute Mean
- Mean imputation biases toward average, reduces variance ❌
- Dropping NAs keeps estimates unbiased ✓

### Manual Mapping System

Add mappings at top of notebook in `MANUAL_MAPPINGS`:
```python
MANUAL_MAPPINGS = [
    {
        'FOD': 6107,
        'CIP4': '5138',
        'CIP4_title': 'Registered Nursing',
        'notes': 'Added 2025-11-06 - large major not in crosswalk'
    },
    # ... more mappings ...
]
```

### Data Summary
- **ACS**: 4.77M observations → 1.41M filtered (age 22-35, valid FOD & occupation)
- **Crosswalk**: 191 FODs → 614 FOD×CIP4 mappings → 398 unique CIP4 codes
- **Enrollment**: 2019-2025, 390 CIP4 codes, ~8.5-8.9M undergraduates/year
- **Expected coverage**: ~285 CIP4 codes (73%), ~90%+ of students

### Latest Updates (November 19, 2025)

- Fixed CIP4_title missing column error
- Fixed hardcoded wage column references (`mean_wage_2019` → `mean_wage_{base_year_label}`)
- Replaced wage tercile time-series plot with scatter plot (only have one year of wage data)
