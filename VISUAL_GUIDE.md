# 🎨 AILO Source Citation - Visual Guide

## Before vs After

### ❌ BEFORE (v1.0)

```
┌─────────────────────────────────────────────┐
│  User: Hva er lønnen for en lærer?         │
└─────────────────────────────────────────────┘
                  ↓
         ┌────────────────┐
         │  AILO v1.0     │
         │  (No source    │
         │   checking)    │
         └────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  AILO: En lærer tjener rundt 45.000-50.000 │
│  kr i måneden. Dette varierer med erfaring  │
│  og utdanning.                              │
│                                             │
│  ⚠️  NO SOURCE CITED!                       │
│  ⚠️  User can't verify this                 │
└─────────────────────────────────────────────┘
```

### ✅ AFTER (v1.1)

```
┌─────────────────────────────────────────────┐
│  User: Hva er lønnen for en lærer?         │
└─────────────────────────────────────────────┘
                  ↓
         ┌────────────────┐
         │  AILO v1.1     │
         │  ✓ Source check│
         │  ✓ Data-only   │
         └────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  AILO: En lærer i grunnskolen har en        │
│  gjennomsnittlig månedslønn på 48.500 kr    │
│  (Kilde: https://utdanning.no/yrker/        │
│  beskrivelse/laerer-grunnskole).            │
│                                             │
│  Dette varierer med erfaring og             │
│  utdanningsnivå (Kilde: https://            │
│  utdanning.no/sammenligning/lonn/uno/       │
│  id-y/laerer).                              │
│                                             │
│  ✅ SOURCES CITED!                          │
│  ✅ User can verify by clicking URLs        │
└─────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────┐
│           utdanning.no API                      │
│  (Education data for Norway)                    │
└────────────────┬────────────────────────────────┘
                 │
                 ↓ api_downloader.py
                 │
┌────────────────┴────────────────────────────────┐
│         utdanning_data/raw/                     │
│  (JSON files with API responses)                │
└────────────────┬────────────────────────────────┘
                 │
                 ↓ data_parser.py + text_extractor.py
                 │
┌────────────────┴────────────────────────────────┐
│    utdanning_data/processed/text_for_llm/       │
│  vectorization_dataset.json                     │
│  • Contains text content                        │
│  • Contains metadata with URLs                  │
│  • Contains source endpoints                    │
└────────────────┬────────────────────────────────┘
                 │
                 ↓ AILO loads into memory
                 │
┌────────────────┴────────────────────────────────┐
│         AILO Knowledge Base                     │
│  • 33,873 documents                             │
│  • Indexed by keywords                          │
│  • URLs extracted and ready                     │
└────────────────┬────────────────────────────────┘
                 │
                 ↓ User asks question
                 │
┌────────────────┴────────────────────────────────┐
│       Search & Context Preparation              │
│  1. Search knowledge base by keywords           │
│  2. Find top 5 relevant documents               │
│  3. Extract URLs from metadata                  │
│  4. Prepare context with sources                │
└────────────────┬────────────────────────────────┘
                 │
                 ↓ Send to LM Studio
                 │
┌────────────────┴────────────────────────────────┐
│            LM Studio (Local LLM)                │
│  • Receives system prompt                       │
│  • Receives context with URLs                   │
│  • Receives strict instructions                 │
│  • Generates response with citations            │
└────────────────┬────────────────────────────────┘
                 │
                 ↓ Response validation
                 │
┌────────────────┴────────────────────────────────┐
│         AILO Response to User                   │
│  ✓ Based ONLY on utdanning.no data              │
│  ✓ Includes source URLs                         │
│  ✓ Honest if data missing                       │
└─────────────────────────────────────────────────┘
```

---

## System Prompt Flow

```
┌─────────────────────────────────────────────┐
│  1. System Prompt (AILO's Personality)      │
│     "You are AILO, career counselor..."     │
│     "CRITICAL: CITE ALL SOURCES"            │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────┴───────────────────────────┐
│  2. Context with Sources                    │
│     "Document 1: Career Info"               │
│     "URL: https://utdanning.no/..."         │
│     "YOU MUST CITE THIS SOURCE"             │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────┴───────────────────────────┐
│  3. Strict Reminder                         │
│     "REMINDER: You MUST cite sources"       │
│     "Do NOT use external knowledge"         │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────┴───────────────────────────┐
│  4. Conversation History (last 10 messages) │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
┌─────────────────┴───────────────────────────┐
│  5. User Question                           │
│     "Hva er lønnen for en lærer?"           │
└─────────────────┬───────────────────────────┘
                  │
                  ↓
          ┌───────────────┐
          │   LM Studio   │
          │   Processes   │
          └───────┬───────┘
                  │
                  ↓
┌─────────────────┴───────────────────────────┐
│  Response with Citations                    │
│  "...48.500 kr (Kilde: https://...)"        │
└─────────────────────────────────────────────┘
```

---

## Configuration Impact

```
┌────────────────────────────────────────────┐
│         Temperature: 0.5                   │
├────────────────────────────────────────────┤
│  Lower = More factual                      │
│  Higher = More creative                    │
│                                            │
│  0.3 ████░░░░░░ Very factual              │
│  0.5 ██████░░░░ Balanced (recommended)    │
│  0.7 ████████░░ More creative             │
│  1.0 ██████████ Very creative             │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│      Max Context Docs: 5                   │
├────────────────────────────────────────────┤
│  More docs = More context, slower          │
│  Fewer docs = Less context, faster         │
│                                            │
│   3 docs: ███░░░░░░░ Fast, less context   │
│   5 docs: ██████░░░░ Balanced             │
│  10 docs: ██████████ Slow, max context    │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│         Max Tokens: 1500                   │
├────────────────────────────────────────────┤
│  Controls response length                  │
│                                            │
│   500: Short answers, may cut off sources │
│  1000: Medium answers                      │
│  1500: Longer answers with full citations │
│  2000: Very detailed with many sources    │
└────────────────────────────────────────────┘
```

---

## Response Validation Flow

```
                User Question
                      ↓
            ┌─────────────────┐
            │ Knowledge Base  │
            │ Search          │
            └────────┬────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    Documents Found          No Documents
         │                       │
         ↓                       ↓
┌────────────────┐      ┌────────────────┐
│ Prepare Context│      │ Return Honest  │
│ with URLs      │      │ "No Info" Msg  │
└───────┬────────┘      └────────────────┘
        │
        ↓
┌────────────────┐
│ Send to LLM    │
└───────┬────────┘
        │
        ↓
┌────────────────┐
│ Get Response   │
└───────┬────────┘
        │
        ↓
┌────────────────┐
│ Check for      │
│ "kilde:" or    │
│ URL in response│
└───────┬────────┘
        │
  ┌─────┴─────┐
  │           │
Found      Not Found
  │           │
  ↓           ↓
✅ Good    ⚠️  Add
Return      Reminder
            & Return
```

---

## Example: Search & Citation Process

```
USER ASKS: "Hva er lønnen for en sykepleier?"
           ↓
┌──────────────────────────────────────────┐
│ Step 1: Extract Keywords                 │
│         ["lønn", "sykepleier"]           │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ Step 2: Search Knowledge Base            │
│                                          │
│  Doc 1: "Sykepleier, lønn..." ⭐⭐⭐⭐⭐  │
│  Doc 2: "Helsefag, lønn..."   ⭐⭐⭐⭐   │
│  Doc 3: "Arbeidsmarked..."    ⭐⭐⭐    │
│  Doc 4: "Utdanning sykepl..." ⭐⭐⭐    │
│  Doc 5: "Helse og omsorg..."  ⭐⭐      │
│                                          │
│  Select top 5                            │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ Step 3: Extract URLs from Metadata       │
│                                          │
│  Doc 1: /yrker/beskrivelse/sykepleier    │
│  Doc 2: /sammenligning/lonn/...          │
│  Doc 3: /sammenligning/arbeidsmarked/... │
│  Doc 4: /utdanning/beskrivelse/...       │
│  Doc 5: /yrker/helse-omsorg/...          │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ Step 4: Build Context                    │
│                                          │
│  "**Document 1**"                        │
│  "URL: https://utdanning.no/yrker/..."   │
│  "YOU MUST CITE THIS SOURCE"             │
│  [content of document 1]                 │
│                                          │
│  "**Document 2**"                        │
│  "URL: https://utdanning.no/sammenli..." │
│  "YOU MUST CITE THIS SOURCE"             │
│  [content of document 2]                 │
│  ...                                     │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ Step 5: Send to LLM                      │
│                                          │
│  System: [personality + strict rules]    │
│  Context: [docs with URLs]               │
│  Reminder: [MUST cite sources]           │
│  User: "Hva er lønnen for sykepleier?"   │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ Step 6: LLM Generates Response           │
│                                          │
│  "En sykepleier i Norge har en           │
│  gjennomsnittlig månedslønn på ca.       │
│  45.000 kr (Kilde: https://utdanning.no  │
│  /yrker/beskrivelse/sykepleier)."        │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ Step 7: Validate & Return                │
│                                          │
│  ✓ Contains "kilde:"                     │
│  ✓ Contains URL                          │
│  ✓ Relevant to question                  │
│  → Return to user                        │
└──────────────────────────────────────────┘
```

---

## Quality Indicators

### ✅ GOOD Response

```
┌────────────────────────────────────────┐
│ User: Hva er lønnen for en lærer?     │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ AILO Response:                         │
│                                        │
│ En lærer i grunnskolen har en          │
│ gjennomsnittlig månedslønn på          │
│ 48.500 kr (Kilde: https://             │
│ utdanning.no/yrker/beskrivelse/        │
│ laerer-grunnskole).                    │
│                                        │
│ ✅ Specific number                     │
│ ✅ Source URL provided                 │
│ ✅ Clickable link                      │
│ ✅ Based on actual data                │
└────────────────────────────────────────┘
```

### ❌ BAD Response (Should not happen)

```
┌────────────────────────────────────────┐
│ User: Hva er lønnen for en lærer?     │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ AILO Response:                         │
│                                        │
│ Lærere i Norge tjener ganske godt.     │
│ Det varierer med erfaring.             │
│                                        │
│ ❌ No specific numbers                 │
│ ❌ No source cited                     │
│ ❌ Generic statement                   │
│ ❌ Can't verify                        │
└────────────────────────────────────────┘
```

### ✅ HONEST Response (When data missing)

```
┌────────────────────────────────────────┐
│ User: Hva er lønnen for astronauter?  │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ AILO Response:                         │
│                                        │
│ Beklager, jeg finner ikke spesifikk   │
│ informasjon om astronauter i           │
│ databasen min fra utdanning.no.        │
│                                        │
│ ✅ Admits limitation                   │
│ ✅ Doesn't make up info                │
│ ✅ Suggests alternatives               │
│ ✅ Maintains trust                     │
└────────────────────────────────────────┘
```

---

## Testing Checklist

```
┌─────────────────────────────────────────┐
│  🧪 AILO Source Citation Tests          │
├─────────────────────────────────────────┤
│                                         │
│  [ ] Run python test_source_citations.py│
│                                         │
│  [ ] Ask about known topic (e.g. lærer) │
│      → Should include sources           │
│                                         │
│  [ ] Ask about unknown topic            │
│      → Should admit no data             │
│                                         │
│  [ ] Check URLs are clickable           │
│      → Should start with https://       │
│                                         │
│  [ ] Verify data matches utdanning.no   │
│      → Click URL and compare            │
│                                         │
│  [ ] Test multiple questions            │
│      → Every answer should cite sources │
│                                         │
│  [ ] Check config settings              │
│      → temperature ≤ 0.5                │
│      → max_tokens ≥ 1500                │
│                                         │
└─────────────────────────────────────────┘
```

---

## File Structure Overview

```
ailo-bot-code/
│
├── 🤖 CORE FILES
│   ├── ailo_chatbot.py          ← Main chatbot (UPDATED!)
│   ├── ailo_scheduler.py         ← Auto updates
│   ├── ailo_config.json          ← Config (UPDATED!)
│   └── main.py                   ← Data pipeline
│
├── 📚 NEW DOCUMENTATION
│   ├── SOURCE_CITATION_GUIDE.md  ← Complete guide (NEW!)
│   ├── UPDATE_NOTES_v1.1.md      ← Change summary (NEW!)
│   ├── CHANGES_SUMMARY.md        ← Quick summary (NEW!)
│   └── VISUAL_GUIDE.md           ← This file (NEW!)
│
├── 🧪 TESTING
│   └── test_source_citations.py  ← Test script (NEW!)
│
├── 📖 EXISTING DOCS (Updated)
│   ├── QUICKREF.md               ← Updated
│   ├── AILO_GUIDE.md
│   └── README.md
│
└── 📁 DATA
    └── utdanning_data/
        └── processed/
            └── text_for_llm/
                └── vectorization_dataset.json
```

---

**Remember:** Every answer needs a source! 📚✨
