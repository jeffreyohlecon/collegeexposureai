import json

with open('descriptives.ipynb', 'r') as f:
    nb = json.load(f)

source = ''.join(nb['cells'][0]['source'])
lines = source.split('\n')

# Find main() and its try block
main_start = None
try_start = None
try_end = None

for i, line in enumerate(lines):
    if 'def main():' in line:
        main_start = i
    elif main_start and 'try:' in line and try_start is None:
        try_start = i
    elif try_start and 'except FileNotFoundError' in line:
        try_end = i
        break

print(f"main() at {main_start}, try block {try_start}-{try_end}")
print(f"Lines to replace: {try_start} to {try_end-1}")

# Create new try block with correct order
new_try_block = '''        # Step 1: Load Felten data
        felten = load_felten_data(FELTEN_PATH)
        
        # Step 2: Load FOD to 4-digit CIP crosswalk
        fod_to_cip4 = load_fod_cip4_crosswalk(CROSSWALK_PATH)
        
        # Step 3: Load and combine enrollment data (2019-2025) - MOVED UP!
        enrollment = load_and_combine_enrollment_data(ENROLLMENT_PATH_2024, ENROLLMENT_PATH_2025)
        
        # Step 4: Add empirical enrollment weights to crosswalk
        fod_to_cip4_weighted = add_empirical_weights_to_crosswalk(
            fod_to_cip4, enrollment, base_year=2019
        )
        
        # Step 5-6: Process ACS and calculate exposure scores
        print("\\n" + "="*70)
        print("PROCESSING ACS DATA")
        print("="*70)
        acs = load_and_filter_acs(ACS_PATH)
        acs_with_exposure = process_acs_with_exposure(acs, felten, fod_to_cip4_weighted)
        cip_exposure = calculate_cip4_exposure(acs_with_exposure)
        
        # Save exposure scores
        cip_exposure.to_csv(f'{OUTPUT_DIR}/cip4_ai_exposure_scores.csv', index=False)
        print(f"\\n✓ Saved exposure scores to {OUTPUT_DIR}/cip4_ai_exposure_scores.csv")
        
        # Step 7: Merge enrollment with exposure
        df_final = merge_enrollment_exposure(enrollment, cip_exposure)
        
        # Save final dataset
        df_final.to_csv(f'{OUTPUT_DIR}/enrollment_with_ai_exposure_4digit.csv', index=False)
        print(f"\\n✓ Saved final dataset to {OUTPUT_DIR}/enrollment_with_ai_exposure_4digit.csv")
        
        # Step 8: Create visualizations
        create_descriptive_plots(df_final, f'{OUTPUT_DIR}/enrollment_trends_4digit.png')
        
        # Step 9: Diagnostic reporting - what's missing?
        print("\\n" + "#"*70)
        print("# DIAGNOSTIC REPORT: COVERAGE ANALYSIS")
        print("#"*70)
        
        # (i) ACS FOD codes not in crosswalk
        acs_fods = set(acs['DEGFIELDD'].dropna().unique())
        crosswalk_fods = set(fod_to_cip4['FOD'].unique())
        missing_fods = acs_fods - crosswalk_fods
        
        print(f"\\n(i) ACS FOD codes NOT in crosswalk mapping:")
        print(f"    Total: {len(missing_fods)} FOD codes")
        if len(missing_fods) > 0:
            print(f"    FODs: {sorted(list(missing_fods))[:20]}")
            # How many ACS observations do these represent?
            missing_fod_count = acs[acs['DEGFIELDD'].isin(missing_fods)]['PERWT'].sum()
            total_count = acs['PERWT'].sum()
            print(f"    Represents {missing_fod_count:,.0f} / {total_count:,.0f} ACS observations ({missing_fod_count/total_count*100:.1f}%)")
        
        # (ii) CIP codes with enrollment but no FOD mapping
        enrollment_cips = set(enrollment['CIP4'].unique())
        crosswalk_cips = set(fod_to_cip4['CIP4'].unique())
        unmapped_cips = enrollment_cips - crosswalk_cips
        
        print(f"\\n(ii) CIP4 codes with enrollment but NOT mapped from any FOD:")
        print(f"     Total: {len(unmapped_cips)} CIP4 codes")
        if len(unmapped_cips) > 0:
            # Get enrollment counts for these
            unmapped_enroll = enrollment[enrollment['CIP4'].isin(unmapped_cips)]
            unmapped_2019 = unmapped_enroll[unmapped_enroll['year'] == 2019]['enrollment'].sum()
            total_2019 = enrollment[enrollment['year'] == 2019]['enrollment'].sum()
            print(f"     CIP4s: {sorted(list(unmapped_cips))[:30]}")
            print(f"     2019 enrollment: {unmapped_2019:,.0f} / {total_2019:,.0f} ({unmapped_2019/total_2019*100:.1f}%)")
            print(f"\\n     Top 10 unmapped CIP4s by 2019 enrollment:")
            top_unmapped = unmapped_enroll[unmapped_enroll['year'] == 2019].nlargest(10, 'enrollment')[['CIP4', 'enrollment']]
            for _, row in top_unmapped.iterrows():
                print(f"       CIP4 {row['CIP4']}: {row['enrollment']:,.0f} students")
        
        print("\\n" + "#"*70)
        print("# DATA PREPARATION COMPLETE (4-DIGIT CIP)")
        print("#"*70)
        print("\\nNext steps:")
        print("1. Review cip4_ai_exposure_scores.csv to validate exposure scores")
        print("2. Check enrollment_with_ai_exposure_4digit.csv for data quality")
        print("3. Code missing FOD→CIP4 mappings to improve coverage")
        print("4. Run econometric_analysis.py for DiD and event study")
        print("\\n4-digit CIP analysis provides:")
        print("  - Computer Science (1107) vs Information Systems (1104)")
        print("  - Business Administration (5202) vs Finance (5208) vs Accounting (5203)")  
        print("  - More granular treatment effects and heterogeneity analysis")
        '''

# Replace the try block
del lines[try_start+1:try_end]
lines.insert(try_start+1, new_try_block)

# Save
new_source = '\n'.join(lines)

try:
    compile(new_source, '<test>', 'exec')
    print("\n✓ Code compiles")
    
    nb['cells'][0]['source'] = new_source.splitlines(keepends=True)
    
    with open('descriptives.ipynb', 'w') as f:
        json.dump(nb, f, indent=1)
    
    print("✓ Notebook updated with new main() structure")
except SyntaxError as e:
    print(f"\n✗ Syntax error: {e}")
    import traceback
    traceback.print_exc()

