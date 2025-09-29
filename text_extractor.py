"""
Text Extraction and Vectorization Preparation for Utdanning.no API Data
Extracts and prepares text content for LLM vectorization and embedding generation.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
from datetime import datetime
import hashlib


class TextExtractor:
    """
    Extracts and prepares text content for vectorization.
    """
    
    def __init__(self, processed_data_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize text extractor.
        
        Args:
            processed_data_dir: Directory containing processed data
            logger: Logger instance
        """
        self.processed_data_dir = Path(processed_data_dir)
        self.logger = logger or logging.getLogger(__name__)
        
        # Create output directories
        self.text_output_dir = self.processed_data_dir / "text_for_llm"
        self.text_output_dir.mkdir(exist_ok=True)
        
        # Text processing configuration
        self.min_text_length = 20
        self.max_chunk_size = 1500  # Optimal for most embedding models
        self.chunk_overlap = 200
        self.context_separator = "\n---\n"
        
        # Domain-specific terminology for educational content
        self.educational_keywords = [
            'utdanning', 'studium', 'skole', 'universitet', 'høgskole', 'fagskole',
            'programområde', 'fag', 'yrke', 'kompetanse', 'kvalifikasjon',
            'læring', 'kurs', 'eksamen', 'grad', 'diplom', 'sertifikat',
            'arbeidsmarked', 'karriere', 'jobb', 'stilling', 'bedrift',
            'lærlingeplass', 'praksis', 'internship', 'opplæring'
        ]
    
    def enhance_text_with_context(self, text: str, metadata: Dict[str, Any], source_endpoint: str) -> str:
        """
        Enhance text with contextual information for better LLM understanding.
        
        Args:
            text: Original text content
            metadata: Associated metadata
            source_endpoint: API endpoint source
            
        Returns:
            Enhanced text with context
        """
        context_parts = []
        
        # Add source context
        endpoint_context = self._get_endpoint_context(source_endpoint)
        if endpoint_context:
            context_parts.append(f"Kilde: {endpoint_context}")
        
        # Add relevant metadata as context
        context_metadata = []
        for key, value in metadata.items():
            if value and str(value).strip():
                # Convert technical field names to readable Norwegian
                readable_key = self._translate_field_name(key)
                context_metadata.append(f"{readable_key}: {value}")
        
        if context_metadata:
            context_parts.append("Metadata: " + "; ".join(context_metadata[:5]))  # Limit to 5 most relevant
        
        # Combine context and text
        if context_parts:
            enhanced_text = "\n".join(context_parts) + self.context_separator + text
        else:
            enhanced_text = text
        
        return enhanced_text
    
    def _get_endpoint_context(self, endpoint: str) -> str:
        """
        Get human-readable context for API endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Human-readable description
        """
        endpoint_contexts = {
            'arbeidsmarkedskart': 'Arbeidsmarkedsdata og statistikk',
            'finnlarebedrift': 'Informasjon om lærebedrifter og læreplasser',
            'jobbkompasset': 'Jobbveiledning og yrkesråd',
            'karakterkalkulator': 'Karakterberegning og poengkalkulator',
            'kategorisystemer': 'Utdannings- og yrkeskategorisering',
            'linje': 'Utdanningsprogrammer og artikler',
            'sammenligning': 'Sammenligning av yrker og utdanninger',
            'studievelgeren': 'Hjelp til valg av studier',
            'utdanningsdata': 'Utdanningsstatistikk og data',
            'vgs': 'Videregående skole informasjon',
            'yrkearbeidsliv': 'Yrkesliv og arbeidsmarked',
            'ovttas': 'Voksenopplæring og kursvirksomhet',
            'regionalkompetanse': 'Regional kompetanse og arbeidsmarked',
            'veientilfagbrev': 'Veier til fagbrev og yrkeskvalifikasjon'
        }
        
        for key, description in endpoint_contexts.items():
            if key in endpoint:
                return description
        
        return endpoint.replace('/', ' ').replace('_', ' ').title()
    
    def _translate_field_name(self, field_name: str) -> str:
        """
        Translate technical field names to readable Norwegian.
        
        Args:
            field_name: Technical field name
            
        Returns:
            Human-readable Norwegian field name
        """
        translations = {
            'id': 'ID',
            'nid': 'Node ID',
            'title': 'Tittel',
            'navn': 'Navn',
            'beskrivelse': 'Beskrivelse',
            'type': 'Type',
            'kategori': 'Kategori',
            'kode': 'Kode',
            'dato': 'Dato',
            'status': 'Status',
            'programomradekode10': 'Programområdekode',
            'yrkeskode_styrk08': 'Yrkeskode',
            'nus_kode': 'NUS-kode',
            'styrk98_kode': 'STYRK98-kode',
            'uno_id': 'UNO ID'
        }
        
        # Clean the field name
        clean_name = field_name.lower().split('.')[-1]  # Remove path prefixes
        
        return translations.get(clean_name, clean_name.replace('_', ' ').title())
    
    def create_vectorization_dataset(self) -> Dict[str, Any]:
        """
        Create a comprehensive dataset for vectorization.
        
        Returns:
            Dataset summary
        """
        # Load processed records
        records_file = self.processed_data_dir / "all_records_normalized.json"
        if not records_file.exists():
            raise FileNotFoundError("No processed records found. Run data parser first.")
        
        with open(records_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        # Create different types of text documents
        documents = []
        document_id = 0
        
        # Type 1: Full record documents (for comprehensive context)
        full_documents = self._create_full_documents(records, document_id)
        documents.extend(full_documents)
        document_id += len(full_documents)
        
        # Type 2: Chunked documents (for detailed information retrieval)
        chunked_documents = self._create_chunked_documents(records, document_id)
        documents.extend(chunked_documents)
        document_id += len(chunked_documents)
        
        # Type 3: Semantic documents (grouped by topic/endpoint)
        semantic_documents = self._create_semantic_documents(records, document_id)
        documents.extend(semantic_documents)
        
        # Save the complete dataset
        self._save_vectorization_dataset(documents)
        
        # Create analysis and statistics
        summary = self._analyze_dataset(documents)
        
        return summary
    
    def _create_full_documents(self, records: List[Dict], start_id: int) -> List[Dict[str, Any]]:
        """Create full document representations."""
        documents = []
        
        for i, record in enumerate(records):
            if len(record["content"].strip()) < self.min_text_length:
                continue
            
            enhanced_text = self.enhance_text_with_context(
                record["content"],
                record["metadata"],
                record["source_endpoint"]
            )
            
            doc = {
                "id": start_id + i,
                "type": "full_document",
                "source_record_id": record["id"],
                "source_endpoint": record["source_endpoint"],
                "title": self._extract_title(record),
                "text": enhanced_text,
                "metadata": record["metadata"],
                "content_length": len(enhanced_text),
                "keywords": self._extract_keywords(enhanced_text),
                "educational_relevance": self._calculate_educational_relevance(enhanced_text)
            }
            
            documents.append(doc)
        
        return documents
    
    def _create_chunked_documents(self, records: List[Dict], start_id: int) -> List[Dict[str, Any]]:
        """Create chunked document representations."""
        documents = []
        doc_id = start_id
        
        for record in records:
            if len(record["content"].strip()) < self.min_text_length:
                continue
            
            enhanced_text = self.enhance_text_with_context(
                record["content"],
                record["metadata"],
                record["source_endpoint"]
            )
            
            # Create chunks
            chunks = self._split_text_into_chunks(enhanced_text)
            
            for i, chunk_text in enumerate(chunks):
                doc = {
                    "id": doc_id,
                    "type": "chunked_document",
                    "source_record_id": record["id"],
                    "source_endpoint": record["source_endpoint"],
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "title": f"{self._extract_title(record)} (Del {i+1})",
                    "text": chunk_text,
                    "metadata": record["metadata"],
                    "content_length": len(chunk_text),
                    "keywords": self._extract_keywords(chunk_text),
                    "educational_relevance": self._calculate_educational_relevance(chunk_text)
                }
                
                documents.append(doc)
                doc_id += 1
        
        return documents
    
    def _create_semantic_documents(self, records: List[Dict], start_id: int) -> List[Dict[str, Any]]:
        """Create semantically grouped documents."""
        documents = []
        
        # Group records by endpoint
        endpoint_groups = {}
        for record in records:
            endpoint = record["source_endpoint"]
            if endpoint not in endpoint_groups:
                endpoint_groups[endpoint] = []
            endpoint_groups[endpoint].append(record)
        
        doc_id = start_id
        
        # Create combined documents for each endpoint
        for endpoint, endpoint_records in endpoint_groups.items():
            if len(endpoint_records) < 2:  # Skip single records
                continue
            
            # Combine content from multiple records
            combined_texts = []
            combined_metadata = {}
            
            for record in endpoint_records[:10]:  # Limit to first 10 records
                if len(record["content"].strip()) >= self.min_text_length:
                    enhanced_text = self.enhance_text_with_context(
                        record["content"],
                        record["metadata"],
                        record["source_endpoint"]
                    )
                    combined_texts.append(enhanced_text)
                    
                    # Merge metadata
                    for key, value in record["metadata"].items():
                        if key not in combined_metadata and value:
                            combined_metadata[key] = value
            
            if combined_texts:
                combined_text = f"\n{self.context_separator}\n".join(combined_texts)
                
                doc = {
                    "id": doc_id,
                    "type": "semantic_document",
                    "source_endpoint": endpoint,
                    "records_count": len(endpoint_records),
                    "title": f"Samlet informasjon: {self._get_endpoint_context(endpoint)}",
                    "text": combined_text,
                    "metadata": combined_metadata,
                    "content_length": len(combined_text),
                    "keywords": self._extract_keywords(combined_text),
                    "educational_relevance": self._calculate_educational_relevance(combined_text)
                }
                
                documents.append(doc)
                doc_id += 1
        
        return documents
    
    def _extract_title(self, record: Dict) -> str:
        """Extract or generate a title for the record."""
        # Look for title in metadata
        for key, value in record["metadata"].items():
            if 'title' in key.lower() or 'navn' in key.lower():
                if isinstance(value, str) and len(value.strip()) > 0:
                    return value.strip()
        
        # Generate from source endpoint
        endpoint_context = self._get_endpoint_context(record["source_endpoint"])
        return f"Informasjon fra {endpoint_context}"
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.max_chunk_size, len(text))
            
            # Try to break at word boundaries
            if end < len(text):
                # Look for a good breaking point
                break_point = text.rfind(' ', start, end)
                if break_point > start + self.max_chunk_size // 2:
                    end = break_point
            
            chunk = text[start:end].strip()
            if len(chunk) >= self.min_text_length:
                chunks.append(chunk)
            
            start = max(end - self.chunk_overlap, start + 1)
        
        return chunks
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        keywords = []
        text_lower = text.lower()
        
        # Find educational keywords
        for keyword in self.educational_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        # Extract potential other keywords (simple approach)
        words = re.findall(r'\b[a-zA-ZæøåÆØÅ]{4,}\b', text)
        word_freq = {}
        for word in words:
            word_lower = word.lower()
            if word_lower not in ['dette', 'være', 'skal', 'eller', 'hvor', 'også', 'hvis']:
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
        
        # Add most frequent words
        frequent_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        keywords.extend([word for word, freq in frequent_words if freq > 1])
        
        return list(set(keywords))  # Remove duplicates
    
    def _calculate_educational_relevance(self, text: str) -> float:
        """Calculate educational relevance score (0-1)."""
        text_lower = text.lower()
        
        # Count educational keywords
        keyword_matches = sum(1 for keyword in self.educational_keywords if keyword in text_lower)
        keyword_score = min(keyword_matches / 10.0, 1.0)  # Normalize
        
        # Check for educational context indicators
        context_indicators = [
            'utdanning', 'skole', 'studium', 'læring', 'kurs', 'eksamen',
            'kompetanse', 'kvalifikasjon', 'yrke', 'karriere', 'jobb'
        ]
        
        context_matches = sum(1 for indicator in context_indicators if indicator in text_lower)
        context_score = min(context_matches / 5.0, 1.0)  # Normalize
        
        # Length factor (longer texts might be more comprehensive)
        length_score = min(len(text) / 2000.0, 1.0)
        
        # Weighted average
        relevance = (keyword_score * 0.4) + (context_score * 0.4) + (length_score * 0.2)
        
        return round(relevance, 3)
    
    def _save_vectorization_dataset(self, documents: List[Dict]) -> None:
        """Save the vectorization dataset in multiple formats."""
        # JSON format
        with open(self.text_output_dir / "vectorization_dataset.json", 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
        
        # CSV format for easy analysis
        df_data = []
        for doc in documents:
            df_data.append({
                "id": doc["id"],
                "type": doc["type"],
                "source_endpoint": doc.get("source_endpoint", ""),
                "title": doc["title"][:100] + "..." if len(doc["title"]) > 100 else doc["title"],
                "content_length": doc["content_length"],
                "keyword_count": len(doc["keywords"]),
                "educational_relevance": doc["educational_relevance"],
                "text_preview": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"]
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(self.text_output_dir / "vectorization_dataset.csv", index=False, encoding='utf-8')
        df.to_parquet(self.text_output_dir / "vectorization_dataset.parquet", index=False)
        
        # Text-only file for simple vectorization
        with open(self.text_output_dir / "texts_only.txt", 'w', encoding='utf-8') as f:
            for doc in documents:
                f.write(f"ID: {doc['id']}\n")
                f.write(f"Title: {doc['title']}\n")
                f.write(f"Text: {doc['text']}\n")
                f.write("=" * 80 + "\n\n")
    
    def _analyze_dataset(self, documents: List[Dict]) -> Dict[str, Any]:
        """Analyze the created dataset."""
        total_docs = len(documents)
        
        # Document type distribution
        type_counts = {}
        for doc in documents:
            doc_type = doc["type"]
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        # Endpoint distribution
        endpoint_counts = {}
        for doc in documents:
            endpoint = doc.get("source_endpoint", "unknown")
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
        
        # Content statistics
        content_lengths = [doc["content_length"] for doc in documents]
        relevance_scores = [doc["educational_relevance"] for doc in documents]
        
        summary = {
            "total_documents": total_docs,
            "document_types": type_counts,
            "endpoint_distribution": dict(sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "content_statistics": {
                "total_content_length": sum(content_lengths),
                "average_content_length": np.mean(content_lengths) if content_lengths else 0,
                "min_content_length": min(content_lengths) if content_lengths else 0,
                "max_content_length": max(content_lengths) if content_lengths else 0,
                "median_content_length": np.median(content_lengths) if content_lengths else 0
            },
            "educational_relevance": {
                "average_relevance": np.mean(relevance_scores) if relevance_scores else 0,
                "high_relevance_docs": sum(1 for score in relevance_scores if score > 0.7),
                "medium_relevance_docs": sum(1 for score in relevance_scores if 0.3 <= score <= 0.7),
                "low_relevance_docs": sum(1 for score in relevance_scores if score < 0.3)
            },
            "files_created": [
                "vectorization_dataset.json",
                "vectorization_dataset.csv", 
                "vectorization_dataset.parquet",
                "texts_only.txt"
            ]
        }
        
        # Save analysis summary
        with open(self.text_output_dir / "dataset_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return summary


def main():
    """Main function for testing text extraction."""
    extractor = TextExtractor("utdanning_data/processed")
    
    summary = extractor.create_vectorization_dataset()
    
    print("\nText Extraction Summary:")
    print(f"Total documents created: {summary['total_documents']}")
    print(f"Document types: {summary['document_types']}")
    print(f"Average content length: {summary['content_statistics']['average_content_length']:.0f} characters")
    print(f"Average educational relevance: {summary['educational_relevance']['average_relevance']:.3f}")
    print(f"High relevance documents: {summary['educational_relevance']['high_relevance_docs']}")


if __name__ == "__main__":
    main()