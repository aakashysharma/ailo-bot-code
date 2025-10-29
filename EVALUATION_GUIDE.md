# 🧪 AILO Evaluation Framework Guide

## Overview

The AILO Evaluation Framework is a comprehensive testing system that evaluates AILO's ability to answer real user questions from `questions.txt`. It provides detailed scoring, performance metrics, and recommendations for improvement.

---

## Quick Start

### Run Quick Test (10 questions)
```bash
python run_evaluation.py
# Choose option 1
```

### Run Full Evaluation (All questions)
```bash
python ailo_evaluation_framework.py
```

### Run Custom Test
```bash
python ailo_evaluation_framework.py --max-questions 50 --sample-categories
```

---

## Features

### 1. 📊 Comprehensive Scoring System

Each response is scored 0-100 based on:

**High-Quality Response (with sources):**
- ✅ Has source citation: **40 points**
- ✅ Has relevant content: **20 points**
- ✅ Contains specific data: **20 points**
- ✅ Appropriate length (200-2000 chars): **10 points**
- ✅ Multiple relevant keywords: **10 points**

**Honest Response (no data available):**
- ✅ Admits limitation: **30 points**
- ✅ Helpful response (≥100 chars): **20 points**
- ✅ Suggests alternatives: **10 points**

**Poor Response (no sources, not honest):**
- ⚠️  Has relevant content: **10 points**
- ⚠️  Contains some data: **10 points**

### 2. 📁 Question Categories

Automatically categorizes questions:
- **job_duties**: "Hva gjør en lærer?"
- **salary**: "Hvor mye tjener en sykepleier?"
- **education_path**: "Hvordan bli ingeniør?"
- **requirements**: "Hva er opptakskravet for medisin?"
- **comparison**: "Forskjellen på bachelor og master?"
- **definition**: "Hva betyr informatikk?"
- **job_locations**: "Hvor jobber kjemikere?"
- **study_locations**: "Hvor kan jeg studere psykologi?"
- **career_options**: "Hva kan man bli med TIP?"
- **study_duration**: "Hvor lenge er bachelor?"
- **work_conditions**: "Hvordan er det å være lærer?"
- **authorization**: "Hvem kan kalle seg psykolog?"

### 3. 📈 Performance Metrics

Tracks:
- Average score across all questions
- Source citation rate
- Honest limitation rate
- Data-containing response rate
- Processing time per question
- Score distribution (Excellent/Good/Fair/Poor)
- Category-specific performance

### 4. 💡 Automatic Recommendations

Provides specific recommendations based on results:
- Configuration adjustments
- Model suggestions
- Temperature tuning
- Token limit changes

---

## Command-Line Options

### Basic Usage
```bash
python ailo_evaluation_framework.py
```

### Test Specific Number of Questions
```bash
python ailo_evaluation_framework.py --max-questions 30
```

### Sample Evenly from Categories
```bash
python ailo_evaluation_framework.py --max-questions 50 --sample-categories
```

### Custom Output File
```bash
python ailo_evaluation_framework.py --output my_evaluation.json
```

### Combined Options
```bash
python ailo_evaluation_framework.py --max-questions 100 --sample-categories --output full_test.json
```

---

## Understanding the Scores

### Score Ranges

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 80-100 | Excellent - Comprehensive answer with sources |
| B | 70-79 | Good - Quality answer, may have minor issues |
| C | 60-69 | Satisfactory - Acceptable but needs improvement |
| D | 50-59 | Needs Improvement - Missing sources or incomplete |
| F | 0-49 | Poor - Requires major improvements |

### What Makes a Good Score?

**High Score (80+):**
```
Question: Hva er lønnen for en lærer?
Response: En lærer i grunnskolen har en gjennomsnittlig 
          månedslønn på 48.500 kr (Kilde: https://utdanning.no
          /yrker/beskrivelse/laerer-grunnskole).

✅ Source cited
✅ Specific data (48.500 kr)
✅ Relevant content
✅ Appropriate length
Score: 90/100
```

**Medium Score (60-70):**
```
Question: Hvordan bli ingeniør?
Response: For å bli ingeniør trenger du bachelor i ingeniørfag 
          (Kilde: https://utdanning.no/utdanning/...). Dette 
          tar vanligvis 3 år.

✅ Source cited
⚠️  Less specific data
⚠️  Could be more comprehensive
Score: 65/100
```

**Low Score (<50):**
```
Question: Hva gjør en tømrer?
Response: En tømrer jobber med bygging og konstruksjon.

❌ No source
❌ Generic information
❌ Not based on utdanning.no data
Score: 20/100
```

---

## Output Files

### 1. Main Report: `ailo_evaluation_report_[timestamp].json`

Contains:
```json
{
  "summary": {
    "total_questions": 100,
    "average_score": 75.5,
    "source_citation_rate": 68.0,
    "honest_limitation_rate": 15.0,
    "data_containing_rate": 82.0,
    "avg_processing_time": 3.2
  },
  "score_distribution": {
    "excellent (80-100)": 45,
    "good (60-79)": 35,
    "fair (40-59)": 15,
    "poor (0-39)": 5
  },
  "category_performance": {...},
  "best_response": {...},
  "worst_response": {...},
  "recommendations": [...]
}
```

### 2. Detailed Report: `ailo_evaluation_report_[timestamp]_detailed.json`

Contains individual evaluation for each question:
```json
[
  {
    "question": "Hva er lønnen for en lærer?",
    "response": "En lærer...",
    "has_source": true,
    "has_relevant_content": true,
    "response_length": 245,
    "is_honest_about_limitation": false,
    "contains_data": true,
    "score": 90.0,
    "category": "salary",
    "keywords_found": ["lærer", "lønn", "kr", "utdanning"],
    "processing_time": 3.1
  },
  ...
]
```

---

## Interpreting Results

### Category Performance

Shows how AILO performs on different question types:

```
📁 CATEGORY PERFORMANCE
====================================================================
salary                    | Avg: 78.5 | Count:  25 | Range: 45-95
education_path            | Avg: 72.3 | Count:  30 | Range: 50-90
job_duties                | Avg: 68.1 | Count:  20 | Range: 40-85
comparison                | Avg: 65.5 | Count:  15 | Range: 35-88
definition                | Avg: 62.0 | Count:  10 | Range: 30-80
```

**What to look for:**
- Categories with low averages need more data or better search
- Wide ranges indicate inconsistent performance
- High-count categories with low scores are priority improvements

### Source Citation Rate

Percentage of responses that include source URLs:

- **>70%**: Excellent - Most responses cite sources ✅
- **50-70%**: Good - Majority cite sources, room for improvement ⚠️
- **<50%**: Poor - Need configuration changes ❌

**Low citation rate solutions:**
1. Lower temperature to 0.3
2. Increase max_tokens to 2000
3. Try different LLM model
4. Increase max_context_docs

### Honest Limitation Rate

Percentage of responses that honestly admit when data is missing:

- **10-20%**: Good - Honest about gaps ✅
- **<5%**: Concerning - May be making up information ⚠️
- **>30%**: Too many gaps - Need more data ❌

---

## Improvements Made to AILO

### 1. Enhanced Search Algorithm

**Before:**
```python
# Simple word matching
for word in query_words:
    if word in text:
        score += text.count(word)
```

**After:**
```python
# Intelligent search with:
- Stop word filtering
- Key term extraction
- Question type identification
- Weighted scoring
- Diminishing returns for repetition
```

**Benefits:**
- Better matches for complex questions
- Understands question intent
- Prioritizes relevant content
- Reduces false positives

### 2. Question Type Detection

Identifies 8 question types:
- salary, education_path, job_duties, comparison
- definition, location, duration, general

**Enables:**
- Targeted search strategies
- Better document scoring
- Improved context selection

### 3. Improved Document Scoring

**Factors considered:**
- Title matches (high weight)
- Source endpoint relevance
- Question type alignment
- Content quality
- Appropriate length

---

## Troubleshooting

### Problem: Low Average Score (<60)

**Solutions:**
1. **Increase context documents:**
   ```json
   {
     "chatbot": {
       "max_context_docs": 10
     }
   }
   ```

2. **Lower temperature:**
   ```json
   {
     "chatbot": {
       "temperature": 0.3
     }
   }
   ```

3. **Check data currency:**
   ```bash
   python main.py  # Re-download latest data
   ```

### Problem: Low Source Citation Rate (<50%)

**Solutions:**
1. **Increase token limit:**
   ```json
   {
     "chatbot": {
       "max_tokens": 2000
     }
   }
   ```

2. **Try different model:**
   - In LM Studio, try models known for following instructions
   - Gemma, Llama, or Mistral variants

3. **Verify system prompt is loaded:**
   ```bash
   grep "KRITISK VIKTIG" ailo_chatbot.py
   ```

### Problem: Many "No Data" Responses

**Solutions:**
1. **Update knowledge base:**
   ```bash
   python main.py  # Full data pipeline
   ```

2. **Check knowledge base size:**
   ```bash
   jq 'length' utdanning_data/processed/text_for_llm/vectorization_dataset.json
   ```
   Should be >30,000 documents

3. **Verify all categories loaded:**
   ```python
   python -c "from ailo_chatbot import AILOChatbot; \
              a = AILOChatbot(); a.load_knowledge_base(); \
              print(f'Loaded: {len(a.knowledge_base)} docs')"
   ```

### Problem: Slow Performance

**Solutions:**
1. **Reduce context documents:**
   ```json
   {"max_context_docs": 3}
   ```

2. **Use smaller/faster model in LM Studio**

3. **Reduce max_tokens:**
   ```json
   {"max_tokens": 1000}
   ```

---

## Best Practices

### For Testing

1. **Start small:** Test with 10-30 questions first
2. **Sample categories:** Use `--sample-categories` for balanced testing
3. **Compare configurations:** Run multiple tests with different settings
4. **Save reports:** Always use `--output` to track improvements over time

### For Analysis

1. **Focus on categories:** Improve low-performing categories first
2. **Review worst responses:** Identify patterns in failures
3. **Check source rates:** Ensure >70% citation rate
4. **Monitor timing:** Keep avg processing time <5 seconds

### For Improvement

1. **Iterate on configuration:** Small changes, test, repeat
2. **Update data regularly:** Run `python main.py` weekly
3. **Try different models:** Some follow instructions better
4. **Document changes:** Note what works in your tests

---

## Example Workflow

### 1. Baseline Test
```bash
# Run initial evaluation
python ailo_evaluation_framework.py --max-questions 50 --sample-categories --output baseline.json
```

### 2. Review Results
```bash
# Check the report
cat baseline.json | jq '.summary'
```

### 3. Make Improvements
```json
// In ailo_config.json
{
  "chatbot": {
    "max_context_docs": 8,  // Increased from 5
    "temperature": 0.4,      // Lowered from 0.5
    "max_tokens": 1800       // Increased from 1500
  }
}
```

### 4. Re-test
```bash
python ailo_evaluation_framework.py --max-questions 50 --sample-categories --output improved.json
```

### 5. Compare
```bash
# Compare scores
echo "Baseline:" && cat baseline.json | jq '.summary.average_score'
echo "Improved:" && cat improved.json | jq '.summary.average_score'
```

---

## Scoring Formula Details

```python
def calculate_score(response):
    score = 0
    
    if has_source:
        score += 40  # Source citation
        if has_relevant_content:
            score += 20  # Relevant to question
        if contains_data:
            score += 20  # Specific facts/numbers
        if 200 <= len(response) <= 2000:
            score += 10  # Appropriate length
        if keyword_count >= 3:
            score += 10  # Multiple relevant terms
            
    elif is_honest_about_limitation:
        score += 30  # Admits no data
        if len(response) >= 100:
            score += 20  # Helpful explanation
        if suggests_alternatives:
            score += 10  # Guides user
            
    else:
        # No source and not honest = poor
        if has_relevant_content:
            score += 10
        if contains_data:
            score += 10
    
    return min(score, 100)
```

---

## Advanced Usage

### Filter by Category

Edit the script to test specific categories:

```python
# In ailo_evaluation_framework.py
questions = framework.load_questions()

# Filter to salary questions only
salary_questions = [q for q in questions 
                    if framework.categorize_question(q) == 'salary']

# Run evaluation
framework.run_evaluation(questions=salary_questions)
```

### Custom Scoring Weights

Modify `_calculate_score()` to adjust weights:

```python
if has_source:
    score += 50  # Increase importance of sources
    if contains_data:
        score += 30  # Value data more
```

### Export to Different Formats

```python
# After running evaluation
import pandas as pd

df = pd.DataFrame([asdict(e) for e in framework.evaluations])
df.to_csv('evaluation_results.csv', index=False)
df.to_excel('evaluation_results.xlsx', index=False)
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: AILO Quality Check

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements_ailo.txt
      - name: Run evaluation
        run: |
          python main.py  # Ensure data is current
          python ailo_evaluation_framework.py --max-questions 30
      - name: Check score
        run: |
          SCORE=$(jq '.summary.average_score' ailo_evaluation_report_*.json)
          if (( $(echo "$SCORE < 60" | bc -l) )); then
            echo "Score too low: $SCORE"
            exit 1
          fi
```

---

## FAQ

**Q: How long does a full evaluation take?**  
A: With ~250 questions and 3s per response, expect 12-15 minutes for full test.

**Q: Can I run multiple evaluations in parallel?**  
A: Not recommended - LM Studio may struggle with concurrent requests.

**Q: What's a good target score?**  
A: Aim for 70+ average. 80+ is excellent.

**Q: How often should I run evaluations?**  
A: After any configuration change, data update, or model change.

**Q: Can I add my own questions?**  
A: Yes! Add them to `questions.txt`, one per line.

---

## Related Files

- `ailo_evaluation_framework.py` - Main evaluation script
- `run_evaluation.py` - Quick test runner
- `questions.txt` - Test questions
- `ailo_chatbot.py` - AILO implementation
- `ailo_config.json` - Configuration

---

## Support

For issues:
1. Check this guide
2. Review generated reports
3. Test with fewer questions first
4. Verify LM Studio is running
5. Ensure knowledge base is loaded

---

**Remember:** Consistent high scores = reliable, trustworthy AILO! 🎯✨
