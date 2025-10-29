# AILO Chatbot Logging System

**AILO** = AI-powered Learning Oracle

## Overview

The AILO chatbot now includes comprehensive logging throughout all parts of the program. This allows you to track every step of the conversation, from loading the knowledge base to generating responses.

## Log Files

### Location
All log files are automatically saved to the `logs/` directory in your project folder.

### File Naming
- Format: `ailo_chat_YYYYMMDD_HHMMSS.log`
- Example: `ailo_chat_20251029_143052.log`
- A new log file is created each time you start the AILO chatbot

### Log Levels

The logging system uses different levels to categorize information:

1. **DEBUG** - Detailed diagnostic information (file only)
   - Document scoring details
   - URL construction steps
   - API payload information
   - Internal processing steps

2. **INFO** - General informational messages (console + file)
   - Knowledge base loading status
   - Search results summary
   - User interactions
   - API calls and responses
   - Source citation counts

3. **WARNING** - Warning messages (console + file)
   - Missing data or files
   - No relevant documents found
   - Missing source citations

4. **ERROR** - Error messages (console + file)
   - Connection failures
   - API errors
   - File loading errors
   - Exceptions with stack traces

## What Gets Logged

### 1. Initialization
```
AILO Chatbot Logging System Initialized
Data directory: utdanning_data
Knowledge base loaded with 33,873 documents
```

### 2. Knowledge Base Loading
- File paths checked
- Number of documents loaded
- Indexing by category
- Document counts per category

### 3. Search Process
```
KNOWLEDGE BASE SEARCH
Query: Hva er lønnen for sykepleiere?
Extracted key terms: {'sykepleiere', 'lønnen'}
Question type identified: salary
Found 15 documents with score > 0
Returning top 5 results:
  1. Score: 45.00 - sammenligning_lonn - Sammenligning Lonn
  2. Score: 32.50 - yrker_sykepleier - Yrker Sykepleier
  ...
```

### 4. Context Preparation
- Documents being processed
- URL extraction and construction
- Context size in characters
- Which URLs are being included

### 5. LLM API Calls
```
NEW CHAT REQUEST
User message: Hva er lønnen for sykepleiere?
Calling LM Studio API at http://localhost:1234...
API Payload: model=gemma-3n-E4B-it-MLX-bf16, temperature=0.5, max_tokens=1500
API Response Status: 200
✓ Successfully received response from LLM
Response length: 850 characters
Source citations found in response: 2
```

### 6. Chat Responses
- Full user messages
- Response generation status
- Source citation validation
- Conversation history size

### 7. User Commands
- Clear conversation history
- Save conversation
- Exit requests

## How to Use the Logs

### Viewing Real-Time Logs

The console shows INFO level and above messages in real-time as you use AILO:
```bash
python ailo_chatbot.py
```

### Analyzing Detailed Logs

For detailed debugging, open the log file in the `logs/` directory:
```bash
# View the latest log file
ls -lt logs/ | head -5
cat logs/ailo_chat_20251029_143052.log
```

### Searching Logs

Use grep to find specific information:

```bash
# Find all search queries
grep "Query:" logs/ailo_chat_*.log

# Find all API errors
grep "ERROR" logs/ailo_chat_*.log

# Find scoring details
grep "scored" logs/ailo_chat_*.log

# Find source citations
grep "Source citations" logs/ailo_chat_*.log
```

### Understanding the "Thinking Process"

The logs capture AILO's decision-making process:

1. **Question Analysis**
   - Look for "Question type identified"
   - Shows how AILO categorized your question

2. **Document Search**
   - Look for "Extracted key terms"
   - Shows which keywords AILO focused on

3. **Document Scoring**
   - Look for "scored" in DEBUG level
   - Shows why certain documents were selected
   - Example: `Doc 'sammenligning_lonn' scored 45.00: title_match(lønn): +10, text_match(sykepleier): +5...`

4. **Context Building**
   - Look for "Processing doc"
   - Shows which URLs were constructed
   - Shows how context was assembled

5. **LLM Response**
   - Look for "API Response Status"
   - Shows the full interaction with the LLM
   - Includes validation of source citations

## Troubleshooting with Logs

### Problem: AILO gives irrelevant answers
**Check:**
- Search for "Question type identified" - Is it correct?
- Search for "Returning top" - Are the right documents being selected?
- Look at document scores - Are the scores reasonable?

### Problem: Missing source citations
**Check:**
- Search for "Source citations found in response"
- If count is 0, check "Context prepared" to verify sources were provided
- Look for "⚠ Response is missing source citations"

### Problem: API connection issues
**Check:**
- Search for "ERROR" and "connection"
- Look for "Testing LM Studio connection"
- Check response status codes

### Problem: Slow responses
**Check:**
- Look at timestamps between "NEW CHAT REQUEST" and "Successfully received response"
- Check "Searching through X documents" to see knowledge base size
- Look for any ERROR or WARNING messages

## Log Retention

- Log files are never automatically deleted
- You can manually delete old logs to save space
- Each log file is independent and self-contained

## Example Log Session

```
2025-10-29 14:30:52 - AILO - INFO - ============================================================
2025-10-29 14:30:52 - AILO - INFO - AILO Chatbot Logging System Initialized
2025-10-29 14:30:52 - AILO - INFO - ============================================================
2025-10-29 14:30:52 - AILO - INFO - Interactive chat session started
2025-10-29 14:30:52 - AILO - INFO - Testing LM Studio connection...
2025-10-29 14:30:52 - AILO - INFO - ✅ Connected to LM Studio server
2025-10-29 14:30:52 - AILO - INFO - ============================================================
2025-10-29 14:30:52 - AILO - INFO - STARTING KNOWLEDGE BASE LOADING
2025-10-29 14:30:52 - AILO - INFO - ============================================================
2025-10-29 14:30:53 - AILO - INFO - ✓ Successfully loaded 33873 documents into knowledge base
2025-10-29 14:30:55 - AILO - INFO - ✓ Knowledge base indexed by categories:
2025-10-29 14:30:55 - AILO - INFO -   - yrker: 5432 documents
2025-10-29 14:30:55 - AILO - INFO -   - utdanning: 8921 documents
2025-10-29 14:30:55 - AILO - INFO -   - lønn: 2341 documents
2025-10-29 14:30:55 - AILO - INFO - Interactive chat ready with 33873 documents
2025-10-29 14:31:05 - AILO - INFO - --- Interaction #1 ---
2025-10-29 14:31:05 - AILO - INFO - ================================================================================
2025-10-29 14:31:05 - AILO - INFO - NEW CHAT REQUEST
2025-10-29 14:31:05 - AILO - INFO - ================================================================================
2025-10-29 14:31:05 - AILO - INFO - User message: Hva er lønnen for sykepleiere?
2025-10-29 14:31:05 - AILO - INFO - ============================================================
2025-10-29 14:31:05 - AILO - INFO - KNOWLEDGE BASE SEARCH
2025-10-29 14:31:05 - AILO - INFO - ============================================================
2025-10-29 14:31:05 - AILO - INFO - Query: hva er lønnen for sykepleiere?
2025-10-29 14:31:05 - AILO - INFO - Question type identified: salary
2025-10-29 14:31:06 - AILO - INFO - Found 15 documents with score > 0
2025-10-29 14:31:06 - AILO - INFO - Returning top 5 results:
2025-10-29 14:31:06 - AILO - INFO -   1. Score: 45.00 - sammenligning_lonn - Sammenligning Lonn
2025-10-29 14:31:06 - AILO - INFO -   2. Score: 32.50 - yrker_sykepleier - Yrker Sykepleier
2025-10-29 14:31:06 - AILO - INFO - ✓ Context prepared: 2847 characters total
2025-10-29 14:31:06 - AILO - INFO - Calling LM Studio API at http://localhost:1234...
2025-10-29 14:31:12 - AILO - INFO - ✓ Successfully received response from LLM
2025-10-29 14:31:12 - AILO - INFO - Response length: 890 characters
2025-10-29 14:31:12 - AILO - INFO - Source citations found in response: 2
2025-10-29 14:31:12 - AILO - INFO - Response delivered to user
```

## Privacy Note

Log files contain:
- All user questions
- All AILO responses
- Technical debugging information

**Do not share log files publicly** if they contain sensitive or personal information.

## Configuration

The logging system is configured in the `_setup_logging()` method in `ailo_chatbot.py`:

- Console handler: INFO level (user-friendly output)
- File handler: DEBUG level (comprehensive logging)
- Automatic log file rotation: New file per session
- UTF-8 encoding: Full support for Norwegian characters

To change log levels or format, modify the `_setup_logging()` method.
