# 📚 AILO Source Citation & Data Integrity Guide

## Overview

AILO has been configured to **ONLY use data from utdanning.no** and **ALWAYS cite sources** for every piece of information provided. This ensures accuracy, transparency, and trustworthiness.

## Key Features

### 1. ✅ Strict Data-Only Mode

AILO will **NEVER** use:
- General knowledge from the LLM's training data
- External information not from utdanning.no
- Speculation or assumptions

AILO will **ONLY** use:
- Data downloaded from api.utdanning.no
- Information processed and stored in `utdanning_data/`
- Facts that can be traced back to a specific URL

### 2. 📖 Mandatory Source Citations

**Every response includes:**
- Source URL in format: `(Kilde: https://utdanning.no/[path])`
- Clear attribution for each fact or statistic
- References to the original endpoint

**Example Response:**
```
Yrket som sykepleier har en gjennomsnittlig månedslønn på ca. 45.000 kr 
(Kilde: https://utdanning.no/yrker/beskrivelse/sykepleier). 

Arbeidsmarkedet for sykepleiere er godt, med lav ledighet og høy etterspørsel 
(Kilde: https://utdanning.no/sammenligning/arbeidsmarked/uno/id-y/sykepleier).
```

### 3. 🚫 Honest Limitations

When information is not available, AILO will:
- Clearly state "Jeg har ikke denne informasjonen i databasen min"
- Suggest rephrasing the question
- Recommend visiting utdanning.no directly
- **NOT** make up or guess information

## Configuration

### In `ailo_config.json`:

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

**Settings Explained:**
- `temperature: 0.5` - Lower temperature = more factual, less creative responses
- `max_tokens: 1500` - Increased to allow room for source citations
- `strict_source_mode: true` - Only use data from knowledge base
- `require_citations: true` - Always include source URLs

## How It Works

### 1. Context Preparation

For every user query, AILO:
1. Searches the knowledge base for relevant documents
2. Extracts URLs from document metadata
3. Constructs full URLs: `https://utdanning.no/[path]`
4. Includes explicit instructions to cite sources

### 2. Response Generation

The LLM receives:
- System prompt emphasizing source citation
- Relevant documents with URLs
- Strict reminder: "You MUST cite sources for everything"
- User's question

### 3. Response Validation

After generation:
- Check if sources are mentioned (basic validation)
- Add reminder if citations seem missing
- Log all responses for quality assurance

## System Prompt Highlights

```
**KRITISK VIKTIG - Kildeangivelse:**
1. BRUK KUN DATA FRA UTDANNING.NO
2. OPPGI ALLTID KILDER med URL
3. VÆR ÆRLIG OM BEGRENSNINGER
4. IKKE GJETNING
```

## Testing Source Citations

### Good Responses ✅

```
User: "Hva er lønnen for en lærer?"
AILO: "En lærer i Norge har en gjennomsnittlig månedslønn på 48.500 kr 
       (Kilde: https://utdanning.no/yrker/beskrivelse/laerer-grunnskole)"
```

### Honest Responses ✅

```
User: "Hva synes du om dette yrket?"
AILO: "Beklager, jeg finner ikke spesifikk informasjon om dette i databasen 
       min fra utdanning.no. Mitt kunnskapsgrunnlag er begrenset til data 
       fra utdanning.no API."
```

### Bad Responses ❌

```
User: "Hva er lønnen for en lærer?"
AILO: "Lærere tjener vanligvis ganske godt, og jobben er sikker."
       (NO SOURCE CITED - This should not happen!)
```

## Data Flow

```
utdanning.no API
    ↓
api_downloader.py (downloads JSON)
    ↓
data_parser.py (extracts text + metadata)
    ↓
text_extractor.py (prepares for LLM)
    ↓
vectorization_dataset.json (knowledge base)
    ↓
AILO Chatbot (searches + cites)
    ↓
User receives answer WITH SOURCES
```

## Troubleshooting

### Problem: AILO gives generic answers without sources

**Solution:**
1. Check that knowledge base is loaded:
   ```bash
   ls -lh utdanning_data/processed/text_for_llm/vectorization_dataset.json
   ```
2. Verify config settings:
   ```bash
   cat ailo_config.json | grep -A 5 chatbot
   ```
3. Restart AILO:
   ```bash
   python ailo_chatbot.py
   ```

### Problem: Sources are missing from responses

**Solution:**
1. Lower the temperature (more factual):
   - Change `temperature` to `0.3` in config
2. Increase context documents:
   - Change `max_context_docs` to `8` or `10`
3. Check LLM model:
   - Some models follow instructions better than others
   - Consider using a different model in LM Studio

### Problem: "No information found" too often

**Solution:**
1. Increase `max_context_docs` to search more documents
2. Update data (might be incomplete):
   ```bash
   python main.py
   ```
3. Check search query - try different keywords

## Verification Commands

### Check Knowledge Base Size
```bash
jq 'length' utdanning_data/processed/text_for_llm/vectorization_dataset.json
```

### Check Data Statistics
```bash
cat utdanning_data/processed/text_for_llm/dataset_analysis.json
```

### View Sample Document with URL
```bash
jq '.[0] | {title, source_endpoint, metadata: .metadata | with_entries(select(.key | contains("url")))}' \
  utdanning_data/processed/text_for_llm/vectorization_dataset.json
```

### Test Source Extraction
```python
import json

with open('utdanning_data/processed/text_for_llm/vectorization_dataset.json', 'r') as f:
    data = json.load(f)

# Count documents with URLs
with_urls = sum(1 for doc in data if any('url' in str(k).lower() for k in doc.get('metadata', {}).keys()))
print(f"Documents with URLs: {with_urls}/{len(data)}")
```

## Best Practices

### For Users:
1. **Be specific** in your questions
2. **Use keywords** from Norwegian education (yrke, utdanning, lønn, etc.)
3. **Verify sources** by clicking the URLs AILO provides
4. **Report issues** if sources are missing or incorrect

### For Administrators:
1. **Update data regularly** (nightly via scheduler)
2. **Monitor response quality** - check saved conversations
3. **Adjust config** based on user feedback
4. **Keep knowledge base current** - re-run data pipeline weekly

## Configuration Tuning

### For Maximum Accuracy:
```json
{
  "chatbot": {
    "max_context_docs": 10,
    "temperature": 0.3,
    "max_tokens": 2000
  }
}
```

### For Faster Responses:
```json
{
  "chatbot": {
    "max_context_docs": 3,
    "temperature": 0.5,
    "max_tokens": 1000
  }
}
```

### For Balanced Performance:
```json
{
  "chatbot": {
    "max_context_docs": 5,
    "temperature": 0.5,
    "max_tokens": 1500
  }
}
```

## Quality Metrics

### Good Quality Indicators:
- ✅ Every answer has at least one `(Kilde: ...)` citation
- ✅ URLs are valid and clickable
- ✅ Information matches what's on utdanning.no
- ✅ Honest about limitations when data is missing

### Red Flags:
- ❌ Generic advice without sources
- ❌ Made-up statistics or facts
- ❌ Contradicts information on utdanning.no
- ❌ Never says "I don't have this information"

## Example Conversations

### Example 1: Successful Query with Sources

```
Du: Hvordan bli sykepleier?

AILO: For å bli sykepleier i Norge må du fullføre en bachelorgrad i 
sykepleie, som tar 3 år (Kilde: https://utdanning.no/utdanning/...sykepleie).

Opptakskravet er generell studiekompetanse, og det er krav om karakter 
i realfag (Kilde: https://utdanning.no/utdanning/...opptak).

Etter endt utdanning har sykepleiere gode jobbmuligheter, med en 
arbeidsledighet på under 2% (Kilde: https://utdanning.no/sammenligning/
arbeidsledighet/uno/id-u/sykepleie).
```

### Example 2: Honest Response When Data Missing

```
Du: Hva er fremtidsutsiktene for astronauter i Norge?

AILO: Beklager, jeg finner ikke spesifikk informasjon om astronauter i 
databasen min fra utdanning.no. Mitt kunnskapsgrunnlag er begrenset til 
data fra utdanning.no API.

Du kan prøve å:
• Omformulere spørsmålet ditt
• Bruke mer spesifikke nøkkelord
• Besøke https://utdanning.no direkte for mer informasjon

Kan jeg hjelpe deg med noe annet innen norsk utdanning og karriere?
```

## Related Files

- `ailo_chatbot.py` - Main chatbot implementation
- `ailo_config.json` - Configuration file
- `data_parser.py` - Extracts metadata and URLs
- `text_extractor.py` - Prepares data for LLM

## Updates

**Version 1.1 (2025-10-29):**
- ✅ Added mandatory source citation
- ✅ Strict data-only mode
- ✅ URL extraction from metadata
- ✅ Lower temperature for factual responses
- ✅ Increased token limit for citations
- ✅ Response validation

---

**Remember:** AILO's strength is in accurate, source-backed information from utdanning.no. Every answer should trace back to a verifiable source! 📚✨
