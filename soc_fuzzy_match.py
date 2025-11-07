"""
Fuzzy matching for masked/aggregated SOC codes (XX, YY suffixes)
Maps ACS masked codes to Felten AIOE scores using hierarchical prefix matching
"""

import pandas as pd
import numpy as np
import re

def fuzzy_match_soc_codes(acs_with_cip: pd.DataFrame, felten: pd.DataFrame) -> pd.DataFrame:
    """
    Match ACS SOC codes (including masked XX/YY codes) to Felten AIOE scores.

    Strategy:
    1. Try exact match first
    2. For non-matches with XX/YY: match to mean AIOE of prefix
    3. For non-matches that are round numbers (like 251000): match to mean of prefix

    Parameters:
    -----------
    acs_with_cip : ACS data with 'soc_clean' column
    felten : Felten data with 'soc_clean' and 'Language Modeling AIOE' columns

    Returns:
    --------
    acs_with_cip merged with AIOE scores (with fuzzy matching for masked codes)
    """

    print("\n" + "="*70)
    print("FUZZY MATCHING SOC CODES (Handling Masked Codes)")
    print("="*70)

    # Create mapping from soc_clean to AIOE
    felten_dict = dict(zip(felten['soc_clean'], felten['Language Modeling AIOE']))

    # First, try exact match
    acs_with_cip['AIOE'] = acs_with_cip['soc_clean'].map(felten_dict)

    exact_matches = acs_with_cip['AIOE'].notna().sum()
    print(f"\nExact matches: {exact_matches:,} / {len(acs_with_cip):,} ({exact_matches/len(acs_with_cip)*100:.1f}%)")

    # Find non-matches
    non_matches = acs_with_cip[acs_with_cip['AIOE'].isna()].copy()

    if len(non_matches) == 0:
        print("✓ All codes matched!")
        return acs_with_cip

    print(f"\nFuzzy matching {len(non_matches):,} non-matches...")

    # Helper function: check if code is masked (has XX or YY)
    def is_masked(code):
        return bool(re.search(r'[XY]+', str(code).upper()))

    # Helper function: get prefix (remove XX/YY or trailing zeros)
    def get_prefix(code):
        code_str = str(code).upper()
        # Remove XX, YY suffixes
        code_clean = re.sub(r'[XY]+$', '', code_str)
        # If it ends in zeros, try shorter prefix
        if code_clean.endswith('000'):
            return code_clean[:3]
        elif code_clean.endswith('00'):
            return code_clean[:4]
        elif code_clean.endswith('0'):
            return code_clean[:5]
        return code_clean

    # For each non-matching code, find Felten codes with matching prefix
    fuzzy_matches = {}
    fuzzy_match_counts = {}

    unique_non_matches = non_matches['soc_clean'].unique()

    for acs_code in unique_non_matches:
        prefix = get_prefix(acs_code)

        # Find all Felten codes starting with this prefix
        matching_felten = [code for code in felten_dict.keys() if code.startswith(prefix)]

        if matching_felten:
            # Calculate median AIOE of matching codes
            aioe_values = [felten_dict[code] for code in matching_felten]
            median_aioe = np.median(aioe_values)
            fuzzy_matches[acs_code] = median_aioe
            fuzzy_match_counts[acs_code] = len(matching_felten)

            if len(unique_non_matches) <= 50:  # Only print if not too many
                masked_flag = "[MASKED]" if is_masked(acs_code) else "[AGGR]"
                print(f"  {masked_flag} {acs_code:8s} → prefix '{prefix}' → median of {len(matching_felten)} codes: AIOE={median_aioe:.3f}")

    # Apply fuzzy matches
    acs_with_cip.loc[acs_with_cip['AIOE'].isna(), 'AIOE'] = \
        acs_with_cip.loc[acs_with_cip['AIOE'].isna(), 'soc_clean'].map(fuzzy_matches)

    # Final report
    fuzzy_matched = len(non_matches) - acs_with_cip['AIOE'].isna().sum()
    still_missing = acs_with_cip['AIOE'].isna().sum()

    print(f"\n{'='*70}")
    print("MATCHING SUMMARY:")
    print(f"{'='*70}")
    print(f"Exact matches:       {exact_matches:,} ({exact_matches/len(acs_with_cip)*100:.1f}%)")
    print(f"Fuzzy matches:       {fuzzy_matched:,} ({fuzzy_matched/len(acs_with_cip)*100:.1f}%)")
    print(f"Total matched:       {exact_matches + fuzzy_matched:,} ({(exact_matches + fuzzy_matched)/len(acs_with_cip)*100:.1f}%)")
    print(f"Still missing:       {still_missing:,} ({still_missing/len(acs_with_cip)*100:.1f}%)")

    if still_missing > 0:
        print(f"\nTop 10 codes that couldn't be matched:")
        still_missing_codes = acs_with_cip[acs_with_cip['AIOE'].isna()]['soc_clean'].value_counts().head(10)
        for code, count in still_missing_codes.items():
            print(f"  {code:8s}: {count:,} observations")

    return acs_with_cip
