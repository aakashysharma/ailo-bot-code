# Quick Start Guide: Norwegian Educational Data for LLM

## 🇳🇴 Norwegian Language Features

This pipeline is specifically designed for **Norwegian bokmål** content from utdanning.no:

### Automatic Handling
- **Norwegian characters**: æøå ÆØÅ preserved correctly
- **Special punctuation**: –, —, "", '' handled properly  
- **Encoding fixes**: Corrects common API encoding issues
- **UTF-8 throughout**: All files saved with proper Norwegian support

### Example Norwegian Content
The pipeline will handle content like:
```
"Høgskolen i Østfold tilbyr utdanning innen økonomi og administrasjon. 
Programområdene inkluderer bygg- og anleggsteknikk, helse- og oppvekstfag."
```

## 🚀 Quick Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Norwegian support**:
   ```bash
   python setup.py
   ```

3. **Run the complete pipeline**:
   ```bash
   python main.py
   ```

## 🤖 LLM Integration Examples

### 1. Free Local Search (No API Key Required)
```python
from llm_integration_example import UtdanningLLMIntegration
import asyncio

async def search_education():
    # Initialize with processed data
    integration = UtdanningLLMIntegration()
    integration.load_processed_data()
    
    # Create embeddings (free, works offline)
    integration.create_local_embeddings()
    
    # Search in Norwegian
    results = integration.semantic_search("Hvordan bli sykepleier?", top_k=3)
    
    for result in results:
        doc = result['document']
        print(f"Tittel: {doc['title']}")
        print(f"Relevans: {result['similarity']:.3f}")
        print(f"Tekst: {doc['text'][:200]}...")
        print()

# Run the search
asyncio.run(search_education())
```

### 2. GPT Integration (Requires OpenAI API Key)
```python
import os
from llm_integration_example import UtdanningLLMIntegration
import asyncio

# Set your OpenAI API key
os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

async def ask_gpt():
    integration = UtdanningLLMIntegration()
    integration.load_processed_data()
    integration.create_local_embeddings()
    
    # Ask a question in Norwegian
    answer = await integration.ask_question(
        "Jeg vil bli programvareutvikler. Hvilke utdanningsveier anbefaler du?",
        use_gpt=True
    )
    
    print("🤖 GPT Svar:")
    print(answer['generated_answer'])
    
    print("\n📚 Kilder:")
    for source in answer['sources'][:3]:
        print(f"- {source['title']}")

asyncio.run(ask_gpt())
```

### 3. Export for Other LLM Systems
```python
from llm_integration_example import UtdanningLLMIntegration
import json

# Load and export high-quality Norwegian educational content
integration = UtdanningLLMIntegration()
integration.load_processed_data()

# Filter for high-relevance Norwegian content
high_quality_docs = [
    {
        'text': doc['text'],
        'title': doc['title'], 
        'source': doc.get('source_endpoint', ''),
        'relevance': doc.get('educational_relevance', 0)
    }
    for doc in integration.documents
    if doc.get('educational_relevance', 0) > 0.7 and len(doc['text']) > 100
]

# Save for use with other LLM systems
with open('norwegian_education_data.json', 'w', encoding='utf-8') as f:
    json.dump(high_quality_docs, f, ensure_ascii=False, indent=2)

print(f"Exported {len(high_quality_docs)} high-quality Norwegian educational documents")
```

## 📊 Output Files with Norwegian Content

After running the pipeline, you'll have:

### Vectorization-Ready Data
```
utdanning_data/processed/text_for_llm/
├── vectorization_dataset.json    # Complete dataset with Norwegian text
├── texts_only.txt               # Pure text for simple embedding
└── dataset_analysis.json        # Analysis of Norwegian content
```

### Example Content Structure
```json
{
  "id": 1,
  "title": "Utdanning innen helse og sosialfag",
  "text": "Høgskolen tilbyr bachelor i sykepleie...",
  "keywords": ["sykepleie", "helse", "utdanning"],
  "educational_relevance": 0.95,
  "metadata": {
    "programområde": "Helse- og oppvekstfag",
    "nivå": "Bachelor"
  }
}
```

## 🎯 Common Use Cases

### Educational Chatbot
```python
# Use the processed Norwegian data as knowledge base
async def education_chatbot(user_question):
    integration = UtdanningLLMIntegration()
    integration.load_processed_data()
    integration.create_local_embeddings()
    
    # Get answer with Norwegian context
    return await integration.ask_question(user_question, use_gpt=True)

# Example questions:
# "Hvilke utdanninger fører til høy lønn?"
# "Hvordan søke på læreplass?"
# "Forskjellen på bachelor og master?"
```

### Study Recommendation System
```python
# Find relevant educational programs
def find_study_programs(interests):
    integration = UtdanningLLMIntegration()
    integration.load_processed_data()
    integration.create_local_embeddings()
    
    query = f"Utdanning innen {interests}"
    results = integration.semantic_search(query, top_k=10)
    
    recommendations = []
    for result in results:
        if result['similarity'] > 0.6:  # High relevance
            recommendations.append({
                'program': result['document']['title'],
                'description': result['document']['text'][:300],
                'relevance': result['similarity']
            })
    
    return recommendations

# Example: 
# programs = find_study_programs("teknologi og programmering")
```

### Research and Analysis
```python
# Analyze Norwegian educational data
import pandas as pd
from collections import Counter

integration = UtdanningLLMIntegration()
integration.load_processed_data()

# Extract keywords from all documents
all_keywords = []
for doc in integration.documents:
    all_keywords.extend(doc.get('keywords', []))

# Most common educational topics
topic_frequency = Counter(all_keywords)
print("Most common topics in Norwegian education:")
for topic, count in topic_frequency.most_common(10):
    print(f"  {topic}: {count}")

# Create analysis DataFrame
df = pd.DataFrame([
    {
        'source': doc.get('source_endpoint', ''),
        'length': doc['content_length'],
        'relevance': doc.get('educational_relevance', 0),
        'keywords_count': len(doc.get('keywords', []))
    }
    for doc in integration.documents
])

print(f"\nDataset statistics:")
print(f"Average text length: {df['length'].mean():.0f} characters")
print(f"High relevance docs: {(df['relevance'] > 0.7).sum()}")
print(f"Most productive endpoint: {df['source'].value_counts().head(1)}")
```

## 🔧 Troubleshooting Norwegian Text

### Common Encoding Issues
```python
# If you see garbled text like "Ã¦Ã¸Ã¥"
def fix_norwegian_encoding(text):
    fixes = {
        'Ã¦': 'æ', 'Ã¸': 'ø', 'Ã¥': 'å',
        'Ã†': 'Æ', 'Ã˜': 'Ø', 'Ã…': 'Å'
    }
    for wrong, correct in fixes.items():
        text = text.replace(wrong, correct)
    return text

# The pipeline does this automatically, but you can use this for manual fixes
```

### Verify Norwegian Character Support
```bash
# Run setup to check Norwegian support
python setup.py

# Test with sample data
python test_pipeline.py
```

## 🎉 Ready to Use!

Your Norwegian educational data is now ready for:
- ✅ Semantic search in Norwegian
- ✅ GPT-powered Q&A systems  
- ✅ Educational recommendation engines
- ✅ Research and analysis
- ✅ Training Norwegian domain-specific models

All with proper handling of Norwegian characters and educational terminology! 🇳🇴📚