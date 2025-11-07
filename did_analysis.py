# =============================================================================
# STEP 11: DIFFERENCE-IN-DIFFERENCES ANALYSIS
# =============================================================================

import pandas as pd
import numpy as np

def run_did_analysis(df: pd.DataFrame, output_dir: str) -> pd.DataFrame:
    """
    Run Difference-in-Differences analysis comparing high vs low AI exposure terciles.

    Specification:
    - Treatment: High AI exposure tercile (vs Low tercile baseline)
    - Post-period: 2025 (vs 2019-2024 pre-period)
    - Outcome: log(enrollment)
    - Weights: Enrollment (larger majors weighted more heavily)
    - Controls: Wage quartiles, year fixed effects

    This ensures "people" (enrollment) is the unit of observation, not just majors.
    Small heterogeneous majors with 14 people don't dominate the results.
    """
    print("\n" + "="*70)
    print("DIFFERENCE-IN-DIFFERENCES ANALYSIS")
    print("="*70)

    # Filter to Low and High terciles only (exclude Medium)
    df_did = df[df['ai_exposure_tercile'].isin(['Low', 'High'])].copy()

    # Filter to observations with valid wage data (for wage-controlled specification)
    df_did_wage = df_did[df_did['wage_quartile'].notna()].copy()

    print(f"\nSample for DiD analysis:")
    print(f"  Total observations: {len(df_did):,}")
    print(f"  Observations with wage data: {len(df_did_wage):,}")
    print(f"  Unique CIP4 codes: {df_did['CIP4'].nunique()}")
    print(f"  Years: {sorted(df_did['year'].unique())}")

    # Create treatment indicator (High = 1, Low = 0)
    df_did['treat'] = (df_did['ai_exposure_tercile'] == 'High').astype(int)
    df_did_wage['treat'] = (df_did_wage['ai_exposure_tercile'] == 'High').astype(int)

    # Create post-period indicator (2025 = 1, 2019-2024 = 0)
    df_did['post'] = (df_did['year'] == 2025).astype(int)
    df_did_wage['post'] = (df_did_wage['year'] == 2025).astype(int)

    # Create DiD interaction term
    df_did['treat_x_post'] = df_did['treat'] * df_did['post']
    df_did_wage['treat_x_post'] = df_did_wage['treat'] * df_did_wage['post']

    # Summary stats by group
    print("\n" + "="*70)
    print("PRE/POST ENROLLMENT BY TREATMENT GROUP (Weighted by Enrollment)")
    print("="*70)

    for tercile in ['Low', 'High']:
        for period in ['Pre (2019-2024)', 'Post (2025)']:
            if period == 'Pre (2019-2024)':
                data = df_did[(df_did['ai_exposure_tercile'] == tercile) & (df_did['year'] < 2025)]
            else:
                data = df_did[(df_did['ai_exposure_tercile'] == tercile) & (df_did['year'] == 2025)]

            total_enrollment = data['enrollment'].sum()
            n_majors = data['CIP4'].nunique()
            avg_enrollment = total_enrollment / n_majors if n_majors > 0 else 0

            print(f"\n{tercile} Exposure - {period}:")
            print(f"  Total enrollment: {total_enrollment:,.0f}")
            print(f"  Number of majors: {n_majors}")
            print(f"  Avg enrollment per major: {avg_enrollment:,.0f}")

    # Calculate enrollment-weighted means
    print("\n" + "="*70)
    print("ENROLLMENT-WEIGHTED MEAN LOG ENROLLMENT")
    print("="*70)

    for tercile in ['Low', 'High']:
        for period, period_name in [(df_did['year'] < 2025, 'Pre'), (df_did['year'] == 2025, 'Post')]:
            data = df_did[(df_did['ai_exposure_tercile'] == tercile) & period]

            if len(data) > 0:
                # Weighted mean log enrollment
                weighted_mean = np.average(data['log_enrollment'], weights=data['enrollment'])
                print(f"{tercile} - {period_name}: {weighted_mean:.4f}")

    # Try to use statsmodels for WLS regression
    try:
        import statsmodels.api as sm
        from statsmodels.formula.api import wls

        print("\n" + "="*70)
        print("DiD REGRESSION RESULTS (Weighted Least Squares)")
        print("="*70)

        # Specification 1: Basic DiD (no wage controls)
        print("\n[1] BASIC DiD: log(enrollment) ~ treat × post + year FE")
        print("    Weights: enrollment (larger majors weighted more heavily)")
        print("-" * 70)

        # Create year dummies
        df_did_reg = df_did.copy()
        for year in df_did_reg['year'].unique():
            if year != 2019:  # Omit 2019 as base year
                df_did_reg[f'year_{year}'] = (df_did_reg['year'] == year).astype(int)

        # Build formula
        year_dummies = ' + '.join([f'year_{y}' for y in sorted(df_did_reg['year'].unique()) if y != 2019])
        formula_basic = f'log_enrollment ~ treat + post + treat_x_post + {year_dummies}'

        # Run WLS regression
        model_basic = wls(formula_basic, data=df_did_reg, weights=df_did_reg['enrollment']).fit()

        print(model_basic.summary())

        # Extract DiD coefficient
        did_coef = model_basic.params['treat_x_post']
        did_se = model_basic.bse['treat_x_post']
        did_pval = model_basic.pvalues['treat_x_post']

        print("\n" + "="*70)
        print(f"DiD ESTIMATE (High vs Low Exposure):")
        print(f"  Coefficient: {did_coef:.4f}")
        print(f"  Std Error: {did_se:.4f}")
        print(f"  P-value: {did_pval:.4f}")
        print(f"  Interpretation: High AI exposure majors had {did_coef*100:.2f}% ")
        print(f"                  differential enrollment growth in 2025 vs 2019-2024")
        print("="*70)

        # Specification 2: DiD with wage controls
        print("\n\n[2] WAGE-CONTROLLED DiD: log(enrollment) ~ treat × post + wage quartiles + year FE")
        print("    Weights: enrollment")
        print("    Sample: Only majors with wage data")
        print("-" * 70)

        # Create wage quartile dummies
        df_wage_reg = df_did_wage.copy()
        for year in df_wage_reg['year'].unique():
            if year != 2019:
                df_wage_reg[f'year_{year}'] = (df_wage_reg['year'] == year).astype(int)

        for quartile in ['Q2', 'Q3', 'Q4']:  # Omit Q1 as base
            df_wage_reg[f'wage_{quartile}'] = (df_wage_reg['wage_quartile'] == quartile).astype(int)

        # Build formula with wage controls
        wage_dummies = ' + '.join([f'wage_{q}' for q in ['Q2', 'Q3', 'Q4']])
        year_dummies_wage = ' + '.join([f'year_{y}' for y in sorted(df_wage_reg['year'].unique()) if y != 2019])
        formula_wage = f'log_enrollment ~ treat + post + treat_x_post + {wage_dummies} + {year_dummies_wage}'

        # Run WLS regression with wage controls
        model_wage = wls(formula_wage, data=df_wage_reg, weights=df_wage_reg['enrollment']).fit()

        print(model_wage.summary())

        # Extract DiD coefficient
        did_coef_wage = model_wage.params['treat_x_post']
        did_se_wage = model_wage.bse['treat_x_post']
        did_pval_wage = model_wage.pvalues['treat_x_post']

        print("\n" + "="*70)
        print(f"WAGE-CONTROLLED DiD ESTIMATE (High vs Low Exposure):")
        print(f"  Coefficient: {did_coef_wage:.4f}")
        print(f"  Std Error: {did_se_wage:.4f}")
        print(f"  P-value: {did_pval_wage:.4f}")
        print(f"  Interpretation: Conditional on 2019 wages, high AI exposure majors")
        print(f"                  had {did_coef_wage*100:.2f}% differential enrollment growth")
        print("="*70)

        # Save results
        results = pd.DataFrame({
            'specification': ['Basic DiD', 'Wage-Controlled DiD'],
            'coefficient': [did_coef, did_coef_wage],
            'std_error': [did_se, did_se_wage],
            'p_value': [did_pval, did_pval_wage],
            'n_obs': [len(df_did_reg), len(df_wage_reg)],
            'n_majors': [df_did_reg['CIP4'].nunique(), df_wage_reg['CIP4'].nunique()]
        })

        results.to_csv(f'{output_dir}/did_results.csv', index=False)
        print(f"\n✓ Saved DiD results to {output_dir}/did_results.csv")

        return results

    except ImportError:
        print("\n⚠ statsmodels not available - running manual DiD calculation")

        # Manual DiD calculation (enrollment-weighted means)
        print("\n" + "="*70)
        print("MANUAL DiD CALCULATION (Enrollment-Weighted)")
        print("="*70)

        # Calculate means
        high_pre = df_did[(df_did['treat'] == 1) & (df_did['post'] == 0)]
        high_post = df_did[(df_did['treat'] == 1) & (df_did['post'] == 1)]
        low_pre = df_did[(df_did['treat'] == 0) & (df_did['post'] == 0)]
        low_post = df_did[(df_did['treat'] == 0) & (df_did['post'] == 1)]

        # Weighted means
        high_pre_mean = np.average(high_pre['log_enrollment'], weights=high_pre['enrollment'])
        high_post_mean = np.average(high_post['log_enrollment'], weights=high_post['enrollment'])
        low_pre_mean = np.average(low_pre['log_enrollment'], weights=low_pre['enrollment'])
        low_post_mean = np.average(low_post['log_enrollment'], weights=low_post['enrollment'])

        # DiD estimate
        high_diff = high_post_mean - high_pre_mean
        low_diff = low_post_mean - low_pre_mean
        did_estimate = high_diff - low_diff

        print(f"\nHigh Exposure:")
        print(f"  Pre (2019-2024):  {high_pre_mean:.4f}")
        print(f"  Post (2025):      {high_post_mean:.4f}")
        print(f"  Difference:       {high_diff:.4f}")

        print(f"\nLow Exposure:")
        print(f"  Pre (2019-2024):  {low_pre_mean:.4f}")
        print(f"  Post (2025):      {low_post_mean:.4f}")
        print(f"  Difference:       {low_diff:.4f}")

        print(f"\nDiD Estimate: {did_estimate:.4f}")
        print(f"Interpretation: High AI exposure majors had {did_estimate*100:.2f}%")
        print(f"                differential enrollment growth in 2025 vs 2019-2024")

        results = pd.DataFrame({
            'specification': ['Manual DiD'],
            'coefficient': [did_estimate],
            'high_pre': [high_pre_mean],
            'high_post': [high_post_mean],
            'low_pre': [low_pre_mean],
            'low_post': [low_post_mean]
        })

        results.to_csv(f'{output_dir}/did_results.csv', index=False)
        print(f"\n✓ Saved DiD results to {output_dir}/did_results.csv")

        return results
