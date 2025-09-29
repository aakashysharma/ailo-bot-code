# Utdanning.no API Data Pipeline

A comprehensive Python pipeline for downloading, processing, and preparing data from the Norwegian education API (api.utdanning.no) for Large Language Model (LLM) vectorization and analysis.

## 🎯 Overview

This pipeline provides a complete solution for:
- **Downloading** all available data from api.utdanning.no endpoints
- **Processing** and normalizing the raw JSON data  
- **Extracting** meaningful text content for LLM vectorization
- **Preparing** data in formats suitable for embedding generation and semantic search

The system handles both simple and parameterized API endpoints, implements proper error handling and rate limiting, and creates well-structured outputs ready for machine learning workflows.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Download  │───▶│  Data Processing │───▶│ Text Extraction │
│                 │    │                 │    │                 │
│ • Rate limiting │    │ • Normalization │    │ • Text chunking │
│ • Error recovery│    │ • Metadata      │    │ • Context enhancement
│ • Parameterized │    │ • Text cleaning │    │ • Educational relevance
│   URL handling  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Raw JSON      │    │  Normalized     │    │ Vectorization   │
│   Files         │    │  Records        │    │ Dataset         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Components

### 1. API Downloader (`api_downloader.py`)
- **Async HTTP client** with configurable concurrency and rate limiting
- **Error recovery** with exponential backoff
- **Progress tracking** with detailed statistics
- **Data persistence** with organized file structure

### 2. URL Processor (`url_processor.py`)  
- **Parameterized URL handling** by extracting IDs from downloaded data
- **Two-phase download** process (simple URLs first, then parameterized)
- **ID extraction** from multiple data sources and formats

### 3. Data Parser (`data_parser.py`)
- **Text extraction** from nested JSON structures
- **Data normalization** and cleaning
- **Metadata preservation** and categorization
- **Multiple output formats** (JSON, CSV, Parquet)

### 4. Text Extractor (`text_extractor.py`)
- **Context enhancement** with Norwegian educational domain knowledge
- **Multiple document types** (full, chunked, semantic)
- **Educational relevance scoring**
- **Optimized chunking** for embedding models

### 5. Main Pipeline (`main.py`)
- **Complete orchestration** of all processing phases
- **CLI interface** with flexible execution options
- **Comprehensive logging** and progress tracking
- **Error handling** and recovery

## 🚀 Quick Start

### Installation

1. **Clone or download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

**Run the complete pipeline:**
```bash
python main.py
```

**Custom output directory:**
```bash
python main.py --output-dir my_education_data
```

**Run individual phases:**
```bash
# Download only
python main.py --download-only

# Process existing raw data
python main.py --process-only

# Extract text from existing processed data
python main.py --extract-only
```

### Expected Output Structure

```
utdanning_data/
├── raw/                              # Raw JSON files from API
│   ├── arbeidsmarkedskart_endring_arbeidsmarked.json
│   ├── sammenligning_main.json
│   └── ...
├── processed/
│   ├── normalized/                   # Individual processed files
│   ├── text_for_llm/                # Ready for vectorization
│   │   ├── vectorization_dataset.json
│   │   ├── vectorization_dataset.csv
│   │   ├── texts_only.txt
│   │   └── dataset_analysis.json
│   ├── all_records_normalized.json   # Combined dataset
│   └── records_summary.csv           # Analysis data
└── logs/                             # Processing logs
```

## 📊 Data Output Formats

### For LLM Vectorization

**`vectorization_dataset.json`** - Complete dataset with:
```json
{
  "id": 1,
  "type": "full_document",
  "title": "Informasjon om utdanningsprogrammer",
  "text": "Enhanced text with context...",
  "metadata": {...},
  "educational_relevance": 0.85,
  "keywords": ["utdanning", "studium", ...]
}
```

**`texts_only.txt`** - Simple text format for basic vectorization

**`vectorization_dataset.csv`** - Tabular format for analysis

### Document Types Created

1. **Full Documents** - Complete records with context
2. **Chunked Documents** - Split into optimal sizes for embedding models  
3. **Semantic Documents** - Grouped by topic/endpoint for comprehensive coverage

## ⚙️ Configuration

Create a `config.json` file to customize behavior:

```json
{
  "downloader": {
    "max_concurrent": 5,
    "rate_limit": 0.2,
    "retry_attempts": 3,
    "timeout": 30
  },
  "parser": {
    "min_text_length": 20
  },
  "extractor": {
    "max_chunk_size": 1500,
    "chunk_overlap": 200
  }
}
```

Use with: `python main.py --config config.json`

## �🇴 Norwegian Language Support

The system is specifically designed for Norwegian bokmål content:

- **UTF-8 encoding** preservation for Norwegian characters (æøåÆØÅ)
- **Encoding error correction** for common API response issues
- **Norwegian punctuation** handling (–, —, "", '', etc.)
- **Character normalization** while preserving meaning

## �🎓 Educational Domain Features

The system includes specialized handling for Norwegian educational content:

- **Domain vocabulary** recognition (utdanning, programområde, yrke, etc.)
- **Educational relevance scoring** for content prioritization  
- **Norwegian context enhancement** with proper terminology
- **Metadata translation** to human-readable Norwegian

## 📈 Performance & Statistics

The pipeline provides comprehensive statistics:
- **Download metrics**: Success/failure rates, data volumes, timing
- **Processing metrics**: Records processed, text extracted, errors
- **Content analysis**: Relevance scores, keyword distribution, endpoint coverage

## 🔧 Advanced Usage

### Processing Existing Data

If you already have raw data:
```bash
# Skip download and process existing files
python main.py --process-only --output-dir existing_data
```

### Custom URL Lists

Use a different endpoint list:
```bash
python main.py --url-list custom_urls.json
```

### Programmatic Usage

```python
from main import UtdanningDataPipeline
import asyncio

async def process_data():
    pipeline = UtdanningDataPipeline("my_output_dir")
    summary = await pipeline.run_complete_pipeline("url_list.json")
    return summary

# Run the pipeline
summary = asyncio.run(process_data())
```

## 🛠️ Troubleshooting

### Common Issues

**Connection Errors**
- Check internet connectivity
- Verify api.utdanning.no is accessible
- Reduce `max_concurrent` in configuration

**Memory Issues**  
- Reduce `max_concurrent` and `chunk_size`
- Process in smaller batches using individual phases

**Empty Results**
- Check if API endpoints are still active
- Review logs in `output_dir/logs/`
- Verify URL list format

### Debugging

Enable detailed logging by checking the log files:
```bash
tail -f utdanning_data/logs/pipeline_*.log
```

## 📋 Requirements

- **Python 3.8+**
- **Dependencies**: See `requirements.txt`
  - `aiohttp` - Async HTTP client
  - `pandas` - Data processing
  - `tqdm` - Progress bars
  - `numpy` - Numerical operations

## 🤝 Contributing

To extend the pipeline:

1. **Add new processors** in the respective module files
2. **Update the main pipeline** to include new phases
3. **Add configuration options** for new features
4. **Update documentation** for new capabilities

## 📜 License

This project is designed for educational and research purposes. Please respect the terms of use of the api.utdanning.no service.

## 🤖 LLM Integration Examples

The pipeline includes complete integration examples for popular LLM services:

### Quick Start with Local Models (Free)
```bash
# Run the integration examples
python llm_integration_example.py
```

### OpenAI Integration
```bash
# Set your API key
export OPENAI_API_KEY="your-key-here"

# Or create .env file from template
cp .env.template .env
# Edit .env with your API key

# Run with GPT integration
python llm_integration_example.py
```

### Example Usage in Code
```python
from llm_integration_example import UtdanningLLMIntegration
import asyncio

async def ask_question():
    integration = UtdanningLLMIntegration()
    integration.load_processed_data()
    integration.create_local_embeddings()
    
    # Ask a question in Norwegian
    answer = await integration.ask_question(
        "Hvordan bli programvareutvikler?"
    )
    
    print(answer['generated_answer'])
    return answer

# Run the example
asyncio.run(ask_question())
```

## 🎯 LLM Integration Features

The included integration supports:

1. **Local Embeddings** (Free):
   - Uses `sentence-transformers` with Norwegian support
   - Works offline after initial model download
   - Perfect for semantic search and similarity matching

2. **OpenAI Integration**:
   - GPT-4 for intelligent answer generation
   - Ada-002 embeddings for enhanced search quality
   - Automatic context preparation from search results

3. **Semantic Search**:
   - Norwegian language queries
   - Educational relevance scoring
   - Source attribution and metadata preservation

4. **Multiple Export Formats**:
   - JSON for API integration
   - CSV for data analysis
   - Plain text for model training

## 🎯 Next Steps for Advanced Integration

After running this pipeline, your data is ready for:

1. **Vector Database Storage**:
   - Use with Pinecone, Weaviate, or Chroma
   - Store embeddings with metadata for enhanced search

2. **RAG Implementation**:
   - Use as knowledge base for educational chatbots
   - Implement semantic search for study guidance
   - Create context-aware educational assistants

3. **Custom Model Training**:
   - Fine-tune models on Norwegian educational content
   - Use exported text data for domain-specific training

---

**Happy Learning! 🎓📚**