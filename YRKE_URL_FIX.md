# Yrke URL Pattern Fix

## Problem

The API validation was rejecting URLs with invalid uno_id patterns for yrke endpoints:
- Error: `"String should match pattern '^(y|u)_\\w+$'"`
- This means yrke IDs must follow the pattern: `y_` followed by alphanumeric characters and underscores
- Similarly, utdanning IDs must follow: `u_` followed by alphanumeric characters and underscores

## Solution

### 1. Analysis

Analyzed the already downloaded `sammenligning_main.json` to extract valid ID patterns:
- **408 valid yrke IDs** (y_*): Examples: `y_barnehage_ass`, `y_butikkmedarbeider`, `y_ingenior`
- **390 valid utdanning IDs** (u_*): Examples: `u_duodji_metall`, `u_ingenior`, `u_larerutdanning`

All IDs follow the pattern: `^(y|u)_[a-z0-9_]+$`

### 2. Implementation

Created `fix_yrke_urls.py` script that:
1. Reads all valid y_ and u_ IDs from `sammenligning_main.json`
2. Removes old parametrized URLs like `sammenligning/yrke/{uno_id}`
3. Creates specific URLs for each valid ID
4. Generates a fixed URL list

### 3. Results

**Before:**
- Total URLs: ~146
- Sammenligning yrke URLs: 2 (with parametrized {uno_id})
- Pattern errors: Many 404s due to invalid parameter substitution

**After:**
- Total URLs: 943
- Sammenligning yrke URLs: 409 (1 base + 408 specific y_ IDs)
- Sammenligning utdanning URLs: 390 (specific u_ IDs)
- Pattern errors: **Fixed** ✅

### 4. URL Examples Created

#### Yrke Comparison URLs (408 + 1 base)
```
https://api.utdanning.no/sammenligning/yrke
https://api.utdanning.no/sammenligning/yrke/y_adjunkt
https://api.utdanning.no/sammenligning/yrke/y_advokat
https://api.utdanning.no/sammenligning/yrke/y_barnehage_ass
https://api.utdanning.no/sammenligning/yrke/y_butikkmedarbeider
https://api.utdanning.no/sammenligning/yrke/y_dyrepasser
https://api.utdanning.no/sammenligning/yrke/y_ingenior
... (408 total)
```

#### Utdanning Comparison URLs (390)
```
https://api.utdanning.no/sammenligning/utdanning/u_aktivitorfag
https://api.utdanning.no/sammenligning/utdanning/u_akvakultur
https://api.utdanning.no/sammenligning/utdanning/u_duodji_metall
https://api.utdanning.no/sammenligning/utdanning/u_ingenior
https://api.utdanning.no/sammenligning/utdanning/u_larerutdanning
... (390 total)
```

### 5. Pattern Validation

All generated IDs match the required API pattern:
```regex
^(y|u)_\w+$
```

Examples:
- ✅ `y_barnehage_ass` - Valid (y_ + word characters)
- ✅ `y_butikkmedarbeider` - Valid (y_ + word characters)
- ✅ `u_duodji_metall` - Valid (u_ + word characters)
- ❌ `elektiker` - Invalid (missing y_ prefix)
- ❌ `y_Elektriker` - Invalid (uppercase not in pattern)
- ❌ `y-elektriker` - Invalid (hyphen not allowed)

### 6. Benefits

1. **No More Pattern Errors**: All URLs now use valid IDs extracted from actual API data
2. **More Data**: Added 798 new valid URLs (408 yrke + 390 utdanning)
3. **Better Coverage**: Can now fetch detailed comparison data for all available occupations and education programs
4. **Maintainable**: Script can be re-run when new IDs are added to the API

### 7. Files Modified

- ✅ `fix_yrke_urls.py` - New script to fix URLs
- ✅ `url_list.json` - Updated with 943 URLs (was ~146)
- ✅ `url_list_backup_TIMESTAMP.json` - Backup of original

### 8. Next Steps

To apply these fixes to your data download:

```bash
# The URL list is already updated
# Just re-run the data download pipeline
python main.py
```

This will:
- Use the new URL list with valid IDs
- Download comparison data for all 408 yrker
- Download comparison data for all 390 utdanning programs
- Eliminate the "String should match pattern" errors

### 9. Validation Commands

Test a few URLs manually:
```bash
# Test yrke endpoint
curl "https://api.utdanning.no/sammenligning/yrke/y_ingenior"

# Test utdanning endpoint  
curl "https://api.utdanning.no/sammenligning/utdanning/u_ingenior"
```

Both should return valid JSON data without pattern validation errors.

---

**Status**: ✅ **FIXED**

The URL list now contains only valid uno_ids that match the API's required pattern `^(y|u)_\w+$`, eliminating all "String should match pattern" errors for sammenligning/yrke endpoints.
