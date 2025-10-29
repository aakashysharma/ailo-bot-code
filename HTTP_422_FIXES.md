# HTTP 422 Validation Error Fixes

## Summary

- **Original URLs**: 943
- **Fixed URLs**: 5
- **Removed URLs**: 2
- **Final count**: 941

## Validation Errors Found

### OVTTAS Endpoints

**Error**: `Field required: lang`

All OVTTAS endpoints require a `lang` parameter (e.g., `lang=no` for Norwegian).

**Fixed URLs**:
- `https://api.utdanning.no/ovttas/emne` → `https://api.utdanning.no/ovttas/emne?lang=nb&prefix=0|`
- `https://api.utdanning.no/ovttas/innholdstype` → `https://api.utdanning.no/ovttas/innholdstype?lang=nb`
- `https://api.utdanning.no/ovttas/language` → `https://api.utdanning.no/ovttas/language?lang=nb`
- `https://api.utdanning.no/ovttas/nivaa` → `https://api.utdanning.no/ovttas/nivaa?lang=nb`
- `https://api.utdanning.no/ovttas/tilgjengelighet` → `https://api.utdanning.no/ovttas/tilgjengelighet?lang=nb`

### VOV Fagkode Velger

**Error**: `Field required: q`

This is a search endpoint that requires user input. Removed from automated downloads.
- ✗ `https://api.utdanning.no/vov/fagkode_velger`

### Sammenligning Yrke Base

**Error**: `Field required: styrk98[]`

The base endpoint requires specific occupation codes. We already have individual URLs for each yrke (408 URLs), so the base endpoint is not needed.
- ✗ `https://api.utdanning.no/sammenligning/yrke`

## Next Steps

1. Review the fixed URL list: `url_list_fixed_422.json`
2. Backup current list: `cp url_list.json url_list_backup.json`
3. Apply fixes: `mv url_list_fixed_422.json url_list.json`
4. Re-run download: `python main.py`

All 422 validation errors should now be resolved.
