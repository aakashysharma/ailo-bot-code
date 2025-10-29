# 🔗 AILO URL Construction & Source Attribution Guide

## Issue Identified & Fixed

### Problem
AILO was citing sources like:
```
(Kilde: https://utdanning.no/sammenligning/main)
```

This is technically correct but too generic and doesn't clearly show that the data comes from `api.utdanning.no`.

### Root Cause
1. Many API endpoints don't map 1:1 to website URLs
2. The fallback URL construction was too simplistic
3. No distinction between web URLs and API data sources

### Solution Implemented
Created intelligent URL mapping that:
1. Extracts specific URLs from metadata when available
2. Maps API endpoints to appropriate web sections
3. Includes both web URL and API source reference
4. Clarifies when data is from API vs specific web pages

---

## How URL Construction Works

### Priority Order

1. **Direct URL from Metadata** (Highest Priority)
   ```python
   metadata = {"url": "/yrker/beskrivelse/sykepleier"}
   → https://utdanning.no/yrker/beskrivelse/sykepleier
   ```

2. **Mapped from API Endpoint**
   ```python
   endpoint = "sammenligning/arbeidsmarked/uno/id-y/sykepleier"
   → https://utdanning.no/sammenligning/y/sykepleier
   ```

3. **Generic Section URL**
   ```python
   endpoint = "sammenligning/main"
   → https://utdanning.no/sammenligning
   ```

4. **Fallback**
   ```python
   endpoint = "unknown/path"
   → https://utdanning.no
   ```

---

## API Endpoint → Web URL Mapping

### Salary & Comparison Data
```
API: sammenligning/lonn/arbeidstid-H/.../uno/id-y/sykepleier
Web: https://utdanning.no/sammenligning/y/sykepleier

API: sammenligning/arbeidsmarked/uno/id-y/laerer
Web: https://utdanning.no/sammenligning/y/laerer

API: sammenligning/main
Web: https://utdanning.no/sammenligning
```

### Occupation Information
```
API: yrker/beskrivelse/sykepleier
Web: https://utdanning.no/yrker/beskrivelse/sykepleier

API: onet/yrker/interesse
Web: https://utdanning.no/yrker
```

### Education Information
```
API: utdanning/beskrivelse/sykepleie
Web: https://utdanning.no/utdanning

API: studievelgeren/result/fylke-Oslo
Web: https://utdanning.no/utdanning
```

### Apprenticeships
```
API: finnlarebedrift/naringskodevelger
Web: https://utdanning.no/nb/finn-larebedrift

API: veientilfagbrev/veier/1.3
Web: https://utdanning.no/nb/vei-til-fagbrev
```

### Labor Market
```
API: arbeidsmarkedskart/endring_arbeidsmarked
Web: https://utdanning.no/arbeidsmarked

API: jobbkompasset/yrker
Web: https://utdanning.no/arbeidsmarked
```

### Regional Competence
```
API: regionalkompetanse/arbeidsmarked_i10
Web: https://utdanning.no/regionalkompetanse
```

### Search Results
```
API: search/result
Web: https://utdanning.no/sok
```

---

## Context Preparation Enhancement

### Before
```
**Dokument 1: Informasjon om lønn**
**URL: https://utdanning.no/sammenligning/main**
(Too generic, unclear data source)
```

### After
```
**Dokument 1: Informasjon om lønn**
**URL: https://utdanning.no/sammenligning**
**Datakilde:** api.utdanning.no/sammenligning/lonn/.../sykepleier
(Clear web URL + explicit API source)
```

---

## Response Citation Formats

### Format 1: Specific Web Page
```
En sykepleier tjener i gjennomsnitt 45.000 kr i måneden 
(Kilde: https://utdanning.no/yrker/beskrivelse/sykepleier).
```

### Format 2: Section + API Data
```
Arbeidsmarkedet for sykepleiere er godt 
(Kilde: https://utdanning.no/sammenligning/y/sykepleier, 
data fra api.utdanning.no).
```

### Format 3: API Data Reference
```
Lønnsutviklingen viser en økning på 5% 
(Kilde: data fra api.utdanning.no/sammenligning/lonn).
```

### Format 4: Generic Section
```
Det finnes mange lærlingsplasser i byggebransjen 
(Kilde: https://utdanning.no/nb/finn-larebedrift).
```

---

## Updated System Prompt

The system prompt now includes:
```
**OPPGI ALLTID KILDER**: For HVER påstand eller informasjon du gir, 
må du referere til kilden. Bruk URL-en som er oppgitt i dokumentene: 
`(Kilde: https://utdanning.no/[URL])`. 

Hvis URL-en er generisk eller kommer fra API-data, skriv: 
`(Kilde: data fra api.utdanning.no)` eller 
`(Kilde: https://utdanning.no/[seksjon])`.
```

---

## Example Responses

### Example 1: Career Information
**Question:** "Hva gjør en informatiker?"

**AILO Response:**
```
Informatikere jobber med programmering, systemutvikling og 
dataadministrasjon (Kilde: https://utdanning.no/yrker/
beskrivelse/informatiker).

De kan jobbe i mange bransjer, inkludert IT-selskaper, 
finansinstitusjoner og offentlige etater (Kilde: data fra 
api.utdanning.no/sammenligning).
```

**URL References:**
- ✅ Specific web page for job description
- ✅ API data reference for general information
- ✅ Clear attribution to utdanning.no

### Example 2: Salary Information
**Question:** "Hvor mye tjener en lærer?"

**AILO Response:**
```
En lærer i grunnskolen har en gjennomsnittlig månedslønn på 
48.500 kr (Kilde: https://utdanning.no/sammenligning/y/laerer).

Lønnen varierer med erfaring og utdanningsnivå, og spesial-
lærere tjener noe mer (Kilde: data fra api.utdanning.no/
sammenligning/lonn).
```

**URL References:**
- ✅ Section URL for salary comparison
- ✅ API data reference for detailed stats
- ✅ Both sources clearly attributed

### Example 3: Education Path
**Question:** "Hvordan bli sykepleier?"

**AILO Response:**
```
For å bli sykepleier må du fullføre en 3-årig bachelor-
utdanning i sykepleie (Kilde: https://utdanning.no/
utdanning).

Opptakskravene er generell studiekompetanse med minimum 
karakter 4 i matematikk, norsk og engelsk (Kilde: data fra 
api.utdanning.no/studievelgeren).
```

**URL References:**
- ✅ Generic education section URL
- ✅ API data reference for specific requirements
- ✅ Clear source attribution

---

## Code Implementation

### Function: `_construct_url_from_endpoint()`

```python
def _construct_url_from_endpoint(self, endpoint: str) -> str:
    """
    Construct a web URL from an API endpoint.
    Maps API endpoints to appropriate web URLs.
    """
    # Remove 'param/' prefix
    endpoint = endpoint.replace('param/', '')
    
    # Map API endpoints to web URLs
    if 'sammenligning' in endpoint:
        if '/uno/id-' in endpoint:
            # Extract the ID (e.g., id-y/sykepleier)
            parts = endpoint.split('/uno/id-')
            if len(parts) > 1:
                id_part = parts[1].split('/')[0] + '/' + \
                          parts[1].split('/')[1]
                return f"https://utdanning.no/sammenligning/{id_part}"
        return "https://utdanning.no/sammenligning"
    
    elif 'yrker' in endpoint:
        if '/beskrivelse/' in endpoint:
            return f"https://utdanning.no/{endpoint}"
        return "https://utdanning.no/yrker"
    
    # ... (more mappings)
    
    else:
        # Generic fallback
        clean_endpoint = endpoint.strip('/').replace('//', '/')
        return f"https://utdanning.no/{clean_endpoint}"
```

### Context Preparation

```python
# Extract URL from metadata
for key, value in metadata.items():
    if 'url' in key.lower() and isinstance(value, str):
        if value.startswith('/'):
            url = f"https://utdanning.no{value}"
            break

# Fallback: construct from endpoint
if not url and source:
    url = self._construct_url_from_endpoint(source)

# Always include both web URL and API source
context_parts.append(f"**URL: {url}**")
context_parts.append(f"**Datakilde:** api.utdanning.no/{source}")
```

---

## Testing

### Test URL Construction
```bash
python test_url_construction.py
```

**Sample Output:**
```
Endpoint: sammenligning/lonn/.../uno/id-y/sykepleier
URL:      https://utdanning.no/sammenligning/y/sykepleier

Endpoint: yrker/beskrivelse/laerer
URL:      https://utdanning.no/yrker/beskrivelse/laerer

Endpoint: sammenligning/main
URL:      https://utdanning.no/sammenligning
```

### Test AILO Responses
```bash
python ailo_chatbot.py

Du: Hva gjør en informatiker?
# Check that response includes proper URLs
```

---

## Benefits

### For Users
1. ✅ **Clear Sources**: Know exactly where information comes from
2. ✅ **Verifiable**: Can visit URLs to check information
3. ✅ **Transparent**: See both web page and API data references
4. ✅ **Trustworthy**: Explicit attribution builds trust

### For Developers
1. ✅ **Maintainable**: Clear mapping logic
2. ✅ **Testable**: Easy to verify URL construction
3. ✅ **Extensible**: Simple to add new endpoint mappings
4. ✅ **Debuggable**: Both URLs and endpoints shown

### For utdanning.no
1. ✅ **Proper Attribution**: Clear data source
2. ✅ **Traffic**: Links drive users to website
3. ✅ **API Recognition**: Shows API usage
4. ✅ **Compliance**: Proper data citation

---

## Troubleshooting

### Issue: URLs are too generic

**Check:**
```python
# In _construct_url_from_endpoint()
# Add more specific mapping for the endpoint type
```

**Solution:**
Add specific mapping for the endpoint pattern:
```python
elif 'your_endpoint_type' in endpoint:
    # Extract specific ID or parameter
    return f"https://utdanning.no/specific/path/{id}"
```

### Issue: API source not showing

**Check:**
```python
# In _prepare_context()
context_parts.append(f"**Datakilde:** api.utdanning.no/{source}")
```

**Solution:**
Verify this line exists in the context preparation.

### Issue: URLs not appearing in responses

**Check:**
1. System prompt includes citation instructions
2. Context includes "OPPGI DENNE KILDEN"
3. Temperature is not too high (>0.7)

**Solution:**
```json
{
  "chatbot": {
    "temperature": 0.5,
    "max_tokens": 1500
  }
}
```

---

## Best Practices

### When Adding New Endpoint Mappings

1. **Check existing data:**
   ```bash
   jq '.[] | select(.source_endpoint | contains("new_endpoint")) | 
       {source_endpoint, metadata}' vectorization_dataset.json | head
   ```

2. **Test mapping:**
   ```python
   # Add to test_url_construction.py
   "new_endpoint/path/example",
   ```

3. **Verify in AILO:**
   Ask a question that would use this endpoint type.

### When URLs Don't Exist

1. Use section-level URL: `https://utdanning.no/[section]`
2. Always include API source: `api.utdanning.no/[endpoint]`
3. Make it clear in citation: `(Kilde: data fra api.utdanning.no)`

---

## Configuration

No configuration changes needed. The improvements work with existing settings:

```json
{
  "chatbot": {
    "max_context_docs": 5,
    "temperature": 0.5,
    "max_tokens": 1500,
    "strict_source_mode": true,
    "require_citations": true
  }
}
```

---

## Summary

### What Changed
- ✅ Intelligent URL mapping from API endpoints
- ✅ Both web URL and API source in context
- ✅ Updated system prompt for flexible citation
- ✅ Clear distinction between web pages and API data

### What Improved
- ✅ More meaningful URLs (not just `/sammenligning/main`)
- ✅ Explicit API data attribution
- ✅ Better user experience
- ✅ Easier verification of sources

### What to Expect
- URLs like `https://utdanning.no/sammenligning/y/sykepleier`
- Citations like `(Kilde: data fra api.utdanning.no/sammenligning/lonn)`
- Clear attribution in every response
- Proper credit to utdanning.no and its API

---

**URLs now properly reflect both the web interface and the API data source!** 🔗✨
