# 4-DIGIT CIP ANALYSIS - SUMMARY

## What Changed

### From 2-Digit to 4-Digit CIP Codes

**Before (2-digit CIP):**
- 49 major families
- CIP 11 = All Computer Science programs
- CIP 52 = All Business programs
- Less granularity

**After (4-digit CIP):**
- **372 specific programs** (vs 49 families)
- **1107** = Computer Science specifically
- **1104** = Information Systems separately
- **5202** = Business Administration
- **5203** = Accounting
- Much more granular analysis!

### Data Files Combined

**Enrollment Data (2019-2025):**
- ✅ `CTEESpring2024-Appendix.xlsx` → 2019-2024 data
- ✅ `CTEESpring2025-DataAppendix.xlsx` → 2025 data
- **Combined**: Full 7-year panel (2019-2025)
- **Format**: 4-digit CIP codes already in both files

**Result:**
- 2,348 observations (372 CIP4 codes × 7 years, with some missingness)
- ~8.5-9 million undergraduates per year

## Key Improvements

### 1. More Precise AI Exposure Mapping

**Example: Computer Science Family (CIP 11)**

At 2-digit level (old):
- All CS programs lumped together
- One AI exposure score for "Computer Science"

At 4-digit level (new):
- **1100**: Computer Science, General
- **1101**: Computer Programming (may have different career outcomes)
- **1104**: Information Systems (more IT management)
- **1107**: Computer Science (traditional CS theory/algorithms)
- **1108**: Computer Software Engineering
- **1110**: Network Administration

Each can have different AI exposure based on typical occupations!

### 2. Better Identification of Treatment Effects

**Example Question:** Did ChatGPT affect enrollment in Computer Science vs Information Systems differently?

- At 2-digit: Can only see aggregate CIP 11 effect
- At 4-digit: Can distinguish:
  - **1107 (CS)**: May attract more students post-ChatGPT
  - **1104 (Info Systems)**: May be less affected
  - Different exposure to AI → Different treatment effects

### 3. Top Enrolled Majors (2025)

| Rank | CIP4 | Program | Enrollment |
|------|------|---------|-----------|
| 1 | 5202 | Business Administration | 649,425 |
| 2 | 2401 | Liberal Arts/General Studies | 599,784 |
| 3 | 5138 | Business Management | 484,912 |
| 4 | 4201 | Psychology, General | 423,294 |
| 5 | 2601 | Biology, General | 370,365 |
| 6 | 1101 | Computer Programming | 224,978 |
| 7 | 1312 | Early Childhood Education | 221,469 |
| 8 | 1107 | Computer Science | 217,579 |
| 9 | 3105 | Health Services | 209,813 |
| 10 | 5208 | Finance | 190,402 |

## FOD to 4-Digit CIP Mapping

**Example Mappings (from crosswalk):**
- FOD 2100 → CIP4 1101 (Computer Programming)
- FOD 2102 → CIP4 1100 (Computer Science, General)
- FOD 2105 → CIP4 1104 (Information Sciences)
- FOD 2107 → CIP4 1105 (Networking & Telecom)

**How it works:**
1. Crosswalk has detailed 6-digit CIP codes (e.g., 11.0701)
2. We extract 4-digit: 
   - First 2 digits = family (11)
   - Next 2 digits = group (07)
   - Combined = 1107
3. Each FOD maps to specific 4-digit program

## Files Created

### Scripts:
1. **`ai_exposure_analysis_4digit.py`** - Main data processing
   - Loads Felten AIOE data
   - Maps FOD → 4-digit CIP
   - Processes ACS (when provided)
   - Calculates program-level AI exposure
   - Merges with enrollment (2019-2025)

2. **`econometric_analysis.py`** - Statistical analysis (same as before)
   - Works with 4-digit CIP data
   - DiD, event study, robustness checks

### Data:
1. **`enrollment_data_4digit_2019_2025.csv`** ✅
   - 2,348 rows (372 CIP4 × 7 years)
   - Combined from both 2024 and 2025 files
   
2. **`enrollment_with_ai_exposure_4digit.csv`** ⚠️
   - Currently uses DUMMY exposure scores
   - Will be real once you provide ACS data
   
3. **`enrollment_trends_4digit.png`** ✅
   - Visualization with dummy data

## What You Need to Do

### CRITICAL: Provide ACS Data

Your ACS file needs:
- `DEGFIELDD` - 4-digit FOD code (e.g., 2102 = Computer Science)
- `OCCSOC` - SOC occupation code
- `PERWT` - Person weight
- `AGE` - Age (filter to 22-35)
- `EDUC` - Education level

Once you have it:
1. Update line 370: `ACS_PATH = 'your_acs_file.csv'`
2. Uncomment lines 377-382
3. Run: `python ai_exposure_analysis_4digit.py`

## Advantages of 4-Digit CIP Analysis

### 1. More Granular Treatment Effects
- Can distinguish between related majors
- E.g., Engineering: Civil (1408) vs Computer (1409) vs Electrical (1410)

### 2. Better Face Validity
- "Computer Science" AI exposure is clearer than "all computing programs"
- Easier to explain and interpret

### 3. Richer Heterogeneity Analysis
- Can examine dose-response within families
- E.g., Within Business: Marketing (5208) vs Accounting (5203) vs Management (5201)

### 4. Policy Relevance
- Universities track enrollment at 4-digit level
- Easier to map findings to actual programs

## Expected Results

### High AI Exposure Programs (predicted):
- 1107: Computer Science
- 5203: Accounting (automated by software)
- 5208: Finance (algorithmic trading, fintech)
- 5201: Business Administration (data analytics)
- 4501: Social Sciences, General (data analysis)

### Low AI Exposure Programs (predicted):
- 5104: Arts (performance, visual arts)
- 3105: Health Services (patient care)
- 1312: Education (teaching, mentoring)
- 3105: Parks & Recreation Management
- 5012: Personal Services

### Medium AI Exposure:
- 2601: Biology (some lab automation, some fieldwork)
- 4201: Psychology (some data analysis, some counseling)
- 1901: Communications (some automated content, some creative)

## Comparison: 2-Digit vs 4-Digit

| Aspect | 2-Digit CIP | 4-Digit CIP |
|--------|-------------|-------------|
| **Granularity** | 49 families | 372 programs |
| **Example** | CIP 11 = All CS | 1107 = CS, 1104 = Info Sys |
| **FOD Mapping** | Approximate | Precise |
| **Treatment ID** | Aggregate | Detailed |
| **Sample Size** | ~100k obs/CIP | ~10k obs/CIP |
| **Interpretation** | General | Specific |
| **Policy Use** | Limited | High |

## Next Steps

### Immediate:
1. ✅ Enrollment data processed (2019-2025)
2. ✅ FOD → 4-digit CIP mapping ready
3. ✅ Scripts created and tested
4. ❌ **Need: ACS PUMS data**

### After Getting ACS:
1. Run `ai_exposure_analysis_4digit.py` → Real exposure scores
2. Validate: Check Computer Science (1107) has high exposure
3. Run `econometric_analysis.py` → DiD results
4. Interpret: Which specific programs affected by AI?

## Research Questions Enabled

With 4-digit CIP, you can answer:

1. **Substitution within families:**
   - Did students shift from traditional CS (1107) to Data Science (1106)?
   
2. **Differential effects by specialization:**
   - Did AI affect Software Engineering (1108) differently than CS (1107)?
   
3. **Cross-family effects:**
   - Did Business Analytics (5209) gain while traditional Business Admin (5202) lost?
   
4. **Job market expectations:**
   - Do students respond to perceived AI threat in specific occupations?
   - E.g., Accounting (5203) vs Finance (5208)

## Caveats

### 1. Smaller Sample Sizes
- Each 4-digit CIP has fewer observations
- Need sufficient ACS sample size (aim for n>50 per CIP)
- Some small programs may need to be excluded

### 2. More Multiple Testing
- 372 programs vs 49 families
- Consider adjusting significance levels
- Or focus on pre-specified programs of interest

### 3. Noisier Estimates
- Within-family variation is smaller
- May need to cluster standard errors differently
- Consider analyzing major programs separately

### 4. Missing Data
- Not all 4-digit CIPs in enrollment appear in ACS
- And vice versa
- ~85-90% match rate expected

## Bottom Line

**4-digit CIP analysis provides:**
- ✅ More precise AI exposure measurement
- ✅ Richer heterogeneity analysis  
- ✅ Better policy relevance
- ✅ Easier interpretation

**Trade-off:**
- ⚠️ Smaller samples per program
- ⚠️ More programs to analyze
- ⚠️ Need careful validation

**Recommendation:** Use 4-digit CIP as primary analysis, with 2-digit as robustness check.
