# =============================================================================
# STEP 11: DIFFERENCE-IN-DIFFERENCES ANALYSIS
# =============================================================================

import pandas as pd
import numpy as np

def run_did_analysis(df: pd.DataFrame, output_dir: str, base_year: int = 2019) -> pd.DataFrame:
    """
    Run Difference-in-Differences analysis comparing high vs low AI exposure terciles.

    Specification:
    - Treatment: High AI exposure tercile (vs Low tercile baseline)
    - Post-period: 2025 (vs base_year-2024 pre-period)
    - Outcome: log(enrollment)
    - Weights: Enrollment (larger majors weighted more heavily)
    - Controls: Wage quartiles, year fixed effects

    This ensures "people" (enrollment) is the unit of observation, not just majors.
    Small heterogeneous majors with 14 people don't dominate the results.

    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with enrollment, exposure, and wage data
    output_dir : str
        Directory to save results
    base_year : int
        Base year for wage data (default 2019)
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

        # Specification 1: Basic DiD (no wage controls, no year FE)
        print("\n[1] BASIC DiD: log(enrollment) ~ treat × post")
        print("    Weights: enrollment (larger majors weighted more heavily)")
        print("-" * 70)

        # Build formula (no year FE)
        df_did_reg = df_did.copy()
        formula_basic = f'log_enrollment ~ treat + post + treat_x_post'

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
        print("\n\n[2] WAGE-CONTROLLED DiD: log(enrollment) ~ treat × post + wage quartiles")
        print("    Weights: enrollment")
        print("    Sample: Only majors with wage data")
        print("-" * 70)

        # Create wage quartile dummies
        df_wage_reg = df_did_wage.copy()
        for quartile in ['Q2', 'Q3', 'Q4']:  # Omit Q1 as base
            df_wage_reg[f'wage_{quartile}'] = (df_wage_reg['wage_quartile'] == quartile).astype(int)

        # Build formula with wage controls (no year FE)
        wage_dummies = ' + '.join([f'wage_{q}' for q in ['Q2', 'Q3', 'Q4']])
        formula_wage = f'log_enrollment ~ treat + post + treat_x_post + {wage_dummies}'

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
        print(f"  Interpretation: Conditional on {base_year} wages, high AI exposure majors")
        print(f"                  had {did_coef_wage*100:.2f}% differential enrollment growth")
        print("="*70)

        # Save regression tables as LaTeX (publication-ready)
        print("\n" + "="*70)
        print("SAVING PUBLICATION-READY LATEX TABLES")
        print("="*70)

        # Save individual model summaries as LaTeX
        with open(f'{output_dir}/did_table1_basic.tex', 'w') as f:
            f.write(model_basic.summary().as_latex())
        print(f"✓ Saved basic DiD table to {output_dir}/did_table1_basic.tex")

        with open(f'{output_dir}/did_table2_wage_controls.tex', 'w') as f:
            f.write(model_wage.summary().as_latex())
        print(f"✓ Saved wage-controlled DiD table to {output_dir}/did_table2_wage_controls.tex")

        # Specification 3: DiD on Year-over-Year Growth Rates
        print("\n\n[3] GROWTH RATE DiD: YoY enrollment growth ~ treat × post + log(wage)")
        print("    Weights: enrollment")
        print("    Outcome: Year-over-year % growth rate")
        print(f"    Control: Log {base_year} wage level")
        print("-" * 70)

        # Calculate YoY growth rates
        df_growth = df_did_wage.sort_values(['CIP4', 'year']).copy()  # Use wage sample
        df_growth['enrollment_lag'] = df_growth.groupby('CIP4')['enrollment'].shift(1)
        df_growth['growth_rate'] = ((df_growth['enrollment'] - df_growth['enrollment_lag']) /
                                     df_growth['enrollment_lag'] * 100)

        # Drop base_year (no prior year to calculate growth)
        df_growth = df_growth[df_growth['year'] > base_year].copy()

        # Redefine post (now 2025 vs 2020-2024)
        df_growth['post'] = (df_growth['year'] == 2025).astype(int)
        df_growth['treat_x_post'] = df_growth['treat'] * df_growth['post']

        # Build formula with log wage control (no year FE)
        formula_growth = f'growth_rate ~ treat + post + treat_x_post + log_mean_wage_{base_year}'

        # Run WLS on growth rates (weight by enrollment)
        model_growth = wls(formula_growth, data=df_growth, weights=df_growth['enrollment']).fit()

        print(model_growth.summary())

        # Extract DiD coefficient
        did_coef_growth = model_growth.params['treat_x_post']
        did_se_growth = model_growth.bse['treat_x_post']
        did_pval_growth = model_growth.pvalues['treat_x_post']

        print("\n" + "="*70)
        print(f"GROWTH RATE DiD ESTIMATE (High vs Low Exposure):")
        print(f"  Coefficient: {did_coef_growth:.4f} percentage points")
        print(f"  Std Error: {did_se_growth:.4f}")
        print(f"  P-value: {did_pval_growth:.4f}")
        print(f"  Interpretation: High AI exposure majors had {did_coef_growth:.2f} percentage point")
        print(f"                  higher YoY growth in 2025 vs 2020-2024")
        print("="*70)

        # Save growth rate model as LaTeX
        with open(f'{output_dir}/did_table3_growth_rate.tex', 'w') as f:
            f.write(model_growth.summary().as_latex())
        print(f"\n✓ Saved growth rate DiD table to {output_dir}/did_table3_growth_rate.tex")

        # Create a combined summary table (all three specs side-by-side)
        try:
            from statsmodels.iolib.summary2 import summary_col

            results_combined = summary_col(
                [model_basic, model_wage, model_growth],
                model_names=['(1)\nBasic DiD', '(2)\nWage Controls', '(3)\nGrowth Rate'],
                stars=True,
                float_format='%.4f',
                info_dict={
                    'N': lambda x: f"{int(x.nobs):,}",
                    'R-squared': lambda x: f"{x.rsquared:.3f}",
                    'Weighted': ['Yes', 'Yes', 'Yes']
                }
            )

            with open(f'{output_dir}/did_table_combined.tex', 'w') as f:
                f.write(results_combined.as_latex())
            print(f"✓ Saved combined DiD table to {output_dir}/did_table_combined.tex")

        except Exception as e:
            print(f"⚠ Could not create combined table: {e}")

        # Also create a simple summary CSV for reference
        results_summary = pd.DataFrame({
            'specification': ['Basic DiD', 'Wage-Controlled DiD', 'Growth Rate DiD'],
            'coefficient': [did_coef, did_coef_wage, did_coef_growth],
            'std_error': [did_se, did_se_wage, did_se_growth],
            'p_value': [did_pval, did_pval_wage, did_pval_growth],
            'n_obs': [len(df_did_reg), len(df_wage_reg), len(df_growth)],
            'n_majors': [df_did_reg['CIP4'].nunique(), df_wage_reg['CIP4'].nunique(), df_growth['CIP4'].nunique()]
        })

        results_summary.to_csv(f'{output_dir}/did_results_summary.csv', index=False)
        print(f"✓ Saved summary CSV to {output_dir}/did_results_summary.csv")

        print("\n" + "="*70)
        print("LATEX TABLE FILES CREATED:")
        print("="*70)
        print(f"  1. {output_dir}/did_table1_basic.tex")
        print(f"  2. {output_dir}/did_table2_wage_controls.tex")
        print(f"  3. {output_dir}/did_table3_growth_rate.tex")
        print(f"  4. {output_dir}/did_table_combined.tex (all specs)")
        print(f"\n  Reference CSV: {output_dir}/did_results_summary.csv")
        print("="*70)

        return results_summary

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

        results.to_csv(f'{output_dir}/did_results_manual.csv', index=False)
        print(f"\n✓ Saved DiD results to {output_dir}/did_results_manual.csv")

        # Create a simple LaTeX table for manual DiD
        latex_table = r'''\begin{table}[htbp]
\centering
\caption{Difference-in-Differences Estimation: AI Exposure and Enrollment Growth}
\label{tab:did_manual}
\begin{tabular}{lcc}
\hline\hline
& High AI Exposure & Low AI Exposure \\
\hline
Pre-period (2019--2024) & %.4f & %.4f \\
Post-period (2025) & %.4f & %.4f \\
Difference (Post - Pre) & %.4f & %.4f \\
\hline
DiD Estimate & \multicolumn{2}{c}{%.4f} \\
 & \multicolumn{2}{c}{(%.2f\%%)} \\
\hline\hline
\multicolumn{3}{l}{\footnotesize Outcome: Log enrollment (weighted by enrollment)} \\
\multicolumn{3}{l}{\footnotesize DiD = (High Post - High Pre) - (Low Post - Low Pre)} \\
\end{tabular}
\end{table}
''' % (high_pre_mean, low_pre_mean, high_post_mean, low_post_mean,
       high_diff, low_diff, did_estimate, did_estimate * 100)

        with open(f'{output_dir}/did_table_manual.tex', 'w') as f:
            f.write(latex_table)
        print(f"✓ Saved LaTeX table to {output_dir}/did_table_manual.tex")

        return results
