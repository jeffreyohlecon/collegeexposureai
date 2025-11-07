"""
Diagnostic script to figure out why only 170 ACS observations pass filters
"""

import pandas as pd
import numpy as np

ACS_PATH = '/Users/jeffreyohl/Dropbox/CollegeMajorData/IPUMS/usa_00011.csv'

print("="*70)
print("DIAGNOSING ACS DATA FILTERING ISSUE")
print("="*70)

# Load ACS
print("\nLoading ACS data...")
acs = pd.read_csv(ACS_PATH)

print(f"\n1. INITIAL LOAD:")
print(f"   Total rows: {len(acs):,}")
print(f"   Columns: {list(acs.columns)}")

# Check each filter condition
print(f"\n2. CHECKING EACH FILTER:")

# Age filter
age_filtered = acs[(acs['AGE'] >= 22) & (acs['AGE'] <= 35)]
print(f"   After age 22-35 filter: {len(age_filtered):,} ({len(age_filtered)/len(acs)*100:.1f}%)")

# OCCSOC filter
occsoc_filtered = acs[acs['OCCSOC'].notna()]
print(f"   After OCCSOC notna filter: {len(occsoc_filtered):,} ({len(occsoc_filtered)/len(acs)*100:.1f}%)")

# DEGFIELDD filter
degfieldd_filtered = acs[acs['DEGFIELDD'].notna()]
print(f"   After DEGFIELDD notna filter: {len(degfieldd_filtered):,} ({len(degfieldd_filtered)/len(acs)*100:.1f}%)")

degfieldd_nonzero = acs[(acs['DEGFIELDD'].notna()) & (acs['DEGFIELDD'] != 0)]
print(f"   After DEGFIELDD != 0 filter: {len(degfieldd_nonzero):,} ({len(degfieldd_nonzero)/len(acs)*100:.1f}%)")

# Combined filters
combined = acs[
    (acs['AGE'] >= 22) &
    (acs['AGE'] <= 35) &
    (acs['OCCSOC'].notna()) &
    (acs['DEGFIELDD'].notna()) &
    (acs['DEGFIELDD'] != 0)
]
print(f"\n3. ALL FILTERS COMBINED: {len(combined):,} ({len(combined)/len(acs)*100:.1f}%)")

# Check what values are in key columns
print(f"\n4. VALUE DISTRIBUTIONS:")
print(f"\nAGE:")
print(acs['AGE'].describe())
print(f"\nOCCSOC missing: {acs['OCCSOC'].isna().sum():,} / {len(acs):,}")
print(f"OCCSOC unique values: {acs['OCCSOC'].nunique()}")
print(f"Sample OCCSOC values: {acs['OCCSOC'].dropna().head(10).tolist()}")

print(f"\nDEGFIELDD missing: {acs['DEGFIELDD'].isna().sum():,} / {len(acs):,}")
print(f"DEGFIELDD == 0: {(acs['DEGFIELDD'] == 0).sum():,}")
print(f"DEGFIELDD unique values: {acs['DEGFIELDD'].nunique()}")
print(f"Sample DEGFIELDD values: {acs['DEGFIELDD'].dropna().head(10).tolist()}")

# Check if there's a YEAR column and what years we have
if 'YEAR' in acs.columns:
    print(f"\n5. YEAR DISTRIBUTION:")
    print(acs['YEAR'].value_counts().sort_index())

    # Try filtering by each year
    print(f"\n6. FILTERING BY YEAR:")
    for year in sorted(acs['YEAR'].unique()):
        year_filtered = acs[
            (acs['YEAR'] == year) &
            (acs['AGE'] >= 22) &
            (acs['AGE'] <= 35) &
            (acs['OCCSOC'].notna()) &
            (acs['DEGFIELDD'].notna()) &
            (acs['DEGFIELDD'] != 0)
        ]
        print(f"   Year {year}: {len(year_filtered):,} observations")

print("\n" + "="*70)
print("DIAGNOSIS COMPLETE")
print("="*70)
