"""
Example: Integrating Utdanning.no Data with Online LLM Models
Demonstrates how to use the processed educational data with popular LLM APIs.
"""

import json
import openai
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import asyncio
import aiohttp
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class UtdanningLLMIntegration:
    """
    Integration class for using Utdanning.no data with various LLM services.
    """
    
    def __init__(self, data_dir: str = "utdanning_data/processed"):
        """
        Initialize with processed data directory.
        
        Args:
            data_dir: Path to processed data directory
        """
        self.data_dir = Path(data_dir)
        self.embeddings_cache = {}
        self.documents = []
        self.embeddings = None
        
        # Initialize embedding model for local processing
        try:
            # Use Norwegian-compatible multilingual model
            self.embedding_model = SentenceTransformer(
                'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
            )
            print("✅ Loaded local embedding model")
        except Exception as e:
            print(f"⚠️  Could not load local embedding model: {e}")
            self.embedding_model = None
    
    def load_processed_data(self) -> Dict[str, Any]:
        """
        Load the processed educational data.
        
        Returns:
            Summary of loaded data
        """
        # Load vectorization dataset
        vector_file = self.data_dir / "text_for_llm" / "vectorization_dataset.json"
        
        if not vector_file.exists():
            raise FileNotFoundError(
                f"Vectorization dataset not found at {vector_file}. "
                "Please run the main pipeline first: python main.py"
            )
        
        with open(vector_file, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
        
        print(f"📚 Loaded {len(self.documents)} documents from processed data")
        
        # Load analysis for insights
        analysis_file = self.data_dir / "text_for_llm" / "dataset_analysis.json"
        analysis = {}
        if analysis_file.exists():
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis = json.load(f)
        
        return {
            "total_documents": len(self.documents),
            "document_types": analysis.get("document_types", {}),
            "avg_length": np.mean([doc["content_length"] for doc in self.documents]),
            "high_relevance_docs": sum(1 for doc in self.documents if doc.get("educational_relevance", 0) > 0.7)
        }
    
    def create_local_embeddings(self, force_refresh: bool = False) -> np.ndarray:
        """
        Create embeddings using local model (free, works offline).
        
        Args:
            force_refresh: Force recreation of embeddings
            
        Returns:
            Numpy array of embeddings
        """
        if not self.embedding_model:
            raise ValueError("Local embedding model not available")
        
        embeddings_file = self.data_dir / "text_for_llm" / "local_embeddings.npy"
        
        # Load cached embeddings if available
        if embeddings_file.exists() and not force_refresh:
            print("📁 Loading cached embeddings...")
            self.embeddings = np.load(embeddings_file)
            return self.embeddings
        
        print("🔄 Creating new embeddings (this may take a few minutes)...")
        
        # Extract texts for embedding
        texts = []
        for doc in self.documents:
            # Use title + text for better context
            combined_text = f"{doc['title']}\n\n{doc['text']}"
            texts.append(combined_text)
        
        # Create embeddings in batches to avoid memory issues
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(
                batch, 
                show_progress_bar=True,
                convert_to_numpy=True
            )
            all_embeddings.append(batch_embeddings)
            print(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        # Combine all embeddings
        self.embeddings = np.vstack(all_embeddings)
        
        # Cache embeddings
        np.save(embeddings_file, self.embeddings)
        print(f"💾 Cached embeddings to {embeddings_file}")
        
        return self.embeddings
    
    async def create_openai_embeddings(self, api_key: str, force_refresh: bool = False) -> List[List[float]]:
        """
        Create embeddings using OpenAI API (requires API key, costs money).
        
        Args:
            api_key: OpenAI API key
            force_refresh: Force recreation of embeddings
            
        Returns:
            List of embedding vectors
        """
        embeddings_file = self.data_dir / "text_for_llm" / "openai_embeddings.json"
        
        # Load cached embeddings if available
        if embeddings_file.exists() and not force_refresh:
            print("📁 Loading cached OpenAI embeddings...")
            with open(embeddings_file, 'r') as f:
                cached = json.load(f)
            return cached['embeddings']
        
        print("🔄 Creating OpenAI embeddings...")
        
        openai.api_key = api_key
        
        # Extract texts
        texts = [f"{doc['title']}\n\n{doc['text'][:8000]}" for doc in self.documents]  # Limit length for API
        
        # Create embeddings in batches
        batch_size = 100  # OpenAI rate limits
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = await openai.Embedding.acreate(
                    input=batch,
                    model="text-embedding-ada-002"
                )
                
                batch_embeddings = [item['embedding'] for item in response['data']]
                all_embeddings.extend(batch_embeddings)
                
                print(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
                
            except Exception as e:
                print(f"Error creating embeddings for batch {i}: {e}")
                # Create dummy embeddings as fallback
                dummy_embeddings = [[0.0] * 1536] * len(batch)
                all_embeddings.extend(dummy_embeddings)
        
        # Cache embeddings
        cache_data = {
            'embeddings': all_embeddings,
            'model': 'text-embedding-ada-002',
            'created_at': pd.Timestamp.now().isoformat()
        }
        
        with open(embeddings_file, 'w') as f:
            json.dump(cache_data, f)
        
        print(f"💾 Cached OpenAI embeddings to {embeddings_file}")
        
        return all_embeddings
    
    def semantic_search(self, query: str, top_k: int = 5, use_openai: bool = False) -> List[Dict[str, Any]]:
        """
        Perform semantic search on the educational data.
        
        Args:
            query: Search query in Norwegian or English
            top_k: Number of results to return
            use_openai: Whether to use OpenAI embeddings (if available)
            
        Returns:
            List of most relevant documents
        """
        if self.embeddings is None:
            raise ValueError("No embeddings available. Create embeddings first.")
        
        # Create query embedding
        if use_openai and os.getenv('OPENAI_API_KEY'):
            # Use OpenAI for query embedding (more expensive but potentially better)
            response = openai.Embedding.create(
                input=[query],
                model="text-embedding-ada-002"
            )
            query_embedding = np.array(response['data'][0]['embedding']).reshape(1, -1)
        else:
            # Use local model
            if not self.embedding_model:
                raise ValueError("Local embedding model not available")
            query_embedding = self.embedding_model.encode([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            doc = self.documents[idx]
            results.append({
                'document': doc,
                'similarity': float(similarities[idx]),
                'rank': len(results) + 1
            })
        
        return results
    
    async def generate_answer_with_gpt(self, question: str, context_docs: List[Dict], api_key: str) -> str:
        """
        Generate an answer using GPT with educational context.
        
        Args:
            question: User question
            context_docs: Relevant documents from semantic search
            api_key: OpenAI API key
            
        Returns:
            Generated answer
        """
        openai.api_key = api_key
        
        # Prepare context from documents
        context_parts = []
        for i, result in enumerate(context_docs[:3]):  # Use top 3 documents
            doc = result['document']
            context_parts.append(
                f"Kilde {i+1} ({doc.get('source_endpoint', 'ukjent')}):\n{doc['text'][:1000]}..."
            )
        
        context = "\n\n".join(context_parts)
        
        # Create prompt in Norwegian
        prompt = f"""Du er en ekspert på norsk utdanning og arbeidsmarked. Svar på spørsmålet basert på den gitte konteksten.

Kontekst fra utdanning.no:
{context}

Spørsmål: {question}

Svar på norsk med følgende struktur:
1. Kort svar på spørsmålet
2. Utdypende informasjon basert på konteksten
3. Relevante kilder eller videre ressurser hvis aktuelt

Svar:"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Du er en hjelpsom assistent som spesialiserer seg på norsk utdanning og karriereveiledning."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Kunne ikke generere svar: {e}"
    
    async def ask_question(self, question: str, use_gpt: bool = True) -> Dict[str, Any]:
        """
        Complete question-answering pipeline.
        
        Args:
            question: User question in Norwegian
            use_gpt: Whether to use GPT for answer generation
            
        Returns:
            Complete answer with sources
        """
        print(f"🔍 Searching for: {question}")
        
        # Semantic search
        search_results = self.semantic_search(question, top_k=5)
        
        answer_data = {
            'question': question,
            'search_results': search_results,
            'generated_answer': None,
            'sources': []
        }
        
        # Extract sources
        for result in search_results:
            doc = result['document']
            answer_data['sources'].append({
                'title': doc['title'],
                'source_endpoint': doc.get('source_endpoint', 'ukjent'),
                'relevance_score': result['similarity'],
                'educational_relevance': doc.get('educational_relevance', 0),
                'preview': doc['text'][:200] + "..."
            })
        
        # Generate answer with GPT if requested
        if use_gpt and os.getenv('OPENAI_API_KEY'):
            print("🤖 Generating answer with GPT...")
            answer = await self.generate_answer_with_gpt(
                question, 
                search_results, 
                os.getenv('OPENAI_API_KEY')
            )
            answer_data['generated_answer'] = answer
        
        return answer_data


# Example usage functions
async def example_basic_search():
    """Example: Basic semantic search without GPT."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Semantic Search")
    print("=" * 60)
    
    # Initialize integration
    integration = UtdanningLLMIntegration()
    
    # Load data
    data_summary = integration.load_processed_data()
    print(f"Data loaded: {data_summary}")
    
    # Create local embeddings (free)
    embeddings = integration.create_local_embeddings()
    print(f"Created embeddings: {embeddings.shape}")
    
    # Example searches
    queries = [
        "Hvordan bli sykepleier?",
        "Hvilke utdanninger fører til høy lønn?", 
        "Lærlingsplasser i Bergen",
        "Programmering og IT-utdanning"
    ]
    
    for query in queries:
        print(f"\n🔍 Søk: {query}")
        results = integration.semantic_search(query, top_k=3)
        
        for i, result in enumerate(results, 1):
            doc = result['document']
            print(f"  {i}. {doc['title']} (relevans: {result['similarity']:.3f})")
            print(f"     Kilde: {doc.get('source_endpoint', 'ukjent')}")
            print(f"     Tekst: {doc['text'][:150]}...")
            print()


async def example_gpt_integration():
    """Example: Full integration with GPT for answer generation."""
    print("=" * 60)
    print("EXAMPLE 2: GPT Integration (requires OpenAI API key)")
    print("=" * 60)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Set OPENAI_API_KEY environment variable to run this example")
        return
    
    # Initialize integration
    integration = UtdanningLLMIntegration()
    integration.load_processed_data()
    integration.create_local_embeddings()
    
    # Example question
    question = "Jeg vil bli programvareutvikler. Hvilke utdanningsveier anbefaler du?"
    
    print(f"Spørsmål: {question}")
    
    # Get complete answer
    answer_data = await integration.ask_question(question, use_gpt=True)
    
    print(f"\n🤖 GPT Svar:")
    print(answer_data['generated_answer'])
    
    print(f"\n📚 Kilder:")
    for i, source in enumerate(answer_data['sources'][:3], 1):
        print(f"  {i}. {source['title']}")
        print(f"     Relevans: {source['relevance_score']:.3f}")
        print(f"     Kilde: {source['source_endpoint']}")
        print()


def example_data_export():
    """Example: Export data for external use."""
    print("=" * 60)
    print("EXAMPLE 3: Data Export for External Systems")
    print("=" * 60)
    
    integration = UtdanningLLMIntegration()
    integration.load_processed_data()
    
    # Export high-relevance documents
    high_relevance_docs = [
        doc for doc in integration.documents 
        if doc.get('educational_relevance', 0) > 0.7
    ]
    
    print(f"Found {len(high_relevance_docs)} high-relevance documents")
    
    # Create export for other systems
    export_data = []
    for doc in high_relevance_docs:
        export_data.append({
            'id': doc['id'],
            'title': doc['title'],
            'text': doc['text'],
            'source': doc.get('source_endpoint', 'unknown'),
            'relevance': doc.get('educational_relevance', 0),
            'keywords': doc.get('keywords', [])
        })
    
    # Save in multiple formats
    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)
    
    # JSON export
    with open(output_dir / "high_relevance_education_data.json", 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    # CSV export
    df = pd.DataFrame(export_data)
    df.to_csv(output_dir / "high_relevance_education_data.csv", index=False, encoding='utf-8')
    
    # Simple text export for basic LLM training
    with open(output_dir / "education_texts.txt", 'w', encoding='utf-8') as f:
        for doc in export_data:
            f.write(f"Title: {doc['title']}\n")
            f.write(f"Source: {doc['source']}\n")
            f.write(f"Text: {doc['text']}\n")
            f.write("=" * 80 + "\n\n")
    
    print(f"✅ Exported data to {output_dir}/")
    print(f"   - JSON format: high_relevance_education_data.json")
    print(f"   - CSV format: high_relevance_education_data.csv")
    print(f"   - Text format: education_texts.txt")


async def main():
    """Run all examples."""
    print("🎓 Utdanning.no LLM Integration Examples")
    print("=" * 60)
    
    # Check if processed data exists
    data_dir = Path("utdanning_data/processed/text_for_llm")
    if not data_dir.exists():
        print("❌ No processed data found!")
        print("Please run the main pipeline first:")
        print("   python main.py")
        return
    
    try:
        # Example 1: Basic search
        await example_basic_search()
        
        # Example 2: GPT integration (only if API key available)
        if os.getenv('OPENAI_API_KEY'):
            await example_gpt_integration()
        else:
            print("\n⚠️  Skipping GPT example (no OPENAI_API_KEY set)")
        
        # Example 3: Data export
        example_data_export()
        
        print("\n🎉 All examples completed!")
        print("\n📖 Usage Summary:")
        print("1. Set OPENAI_API_KEY environment variable for GPT features")
        print("2. Use local embeddings for free semantic search")
        print("3. Use exported data formats for other LLM systems")
        print("4. Customize the integration class for your specific needs")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    asyncio.run(main())