"""
Data Parser and Cleaner for Utdanning.no API Data
Processes and cleans downloaded JSON data for vectorization preparation.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import re
from datetime import datetime
import hashlib


class UtdanningDataParser:
    """
    Parses and cleans downloaded API data for LLM processing.
    """
    
    def __init__(self, raw_data_dir: str, processed_data_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the data parser.
        
        Args:
            raw_data_dir: Directory containing raw JSON files
            processed_data_dir: Directory for processed output
            logger: Logger instance
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        self.logger = logger or logging.getLogger(__name__)
        
        # Create output directories
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        (self.processed_data_dir / "normalized").mkdir(exist_ok=True)
        (self.processed_data_dir / "text_content").mkdir(exist_ok=True)
        (self.processed_data_dir / "metadata").mkdir(exist_ok=True)
        
        # Processing statistics
        self.stats = {
            "files_processed": 0,
            "records_extracted": 0,
            "text_chunks_created": 0,
            "errors": 0
        }
        
        # Text extraction patterns
        self.text_fields = [
            'title', 'navn', 'name', 'beskrivelse', 'description', 'content', 
            'innhold', 'tekst', 'text', 'body', 'sammendrag', 'summary',
            'kort_beskrivelse', 'lang_beskrivelse', 'info', 'information',
            'detaljer', 'details', 'kommentar', 'comment', 'notater', 'notes'
        ]
        
        # Metadata fields to preserve
        self.metadata_fields = [
            'id', 'nid', 'uno_id', 'kode', 'code', 'type', 'kategori', 'category',
            'dato', 'date', 'created', 'updated', 'modified', 'status', 'url',
            'programomradekode10', 'yrkeskode_styrk08', 'styrk98_kode', 'nus_kode'
        ]
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize Norwegian text content while preserving special characters.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text with proper Norwegian encoding
        """
        if not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Ensure proper UTF-8 encoding
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='ignore')
        
        # Remove HTML tags but preserve Norwegian characters
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Keep Norwegian characters (æøå ÆØÅ) and common punctuation
        # Remove only problematic characters, not Norwegian ones
        text = re.sub(r'[^\w\s\.,!?;:()\-æøåÆØÅ""''–—/%]', '', text)
        
        # Fix common Norwegian encoding issues from API responses
        encoding_fixes = {
            'Ã¦': 'æ', 'Ã¸': 'ø', 'Ã¥': 'å',
            'Ã†': 'Æ', 'Ã˜': 'Ø', 'Ã…': 'Å',
            'â€œ': '"', 'â€': '"', 'â€™': "'",
            'â€"': '–', 'â€"': '—'
        }
        
        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)
        
        # Strip and return
        return text.strip()
    
    def extract_text_content(self, data: Any, path: str = "") -> List[Dict[str, str]]:
        """
        Recursively extract text content from JSON data.
        
        Args:
            data: JSON data to process
            path: Current path in the data structure
            
        Returns:
            List of text content dictionaries
        """
        text_chunks = []
        
        def recursive_extract(obj, current_path=""):
            """Recursively extract text from nested structures."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{current_path}.{key}" if current_path else key
                    
                    # Check if this is a text field
                    if any(text_field in key.lower() for text_field in self.text_fields):
                        if isinstance(value, str) and len(value.strip()) > 10:
                            cleaned_text = self.clean_text(value)
                            if len(cleaned_text) > 10:  # Only keep substantial text
                                text_chunks.append({
                                    "path": new_path,
                                    "field": key,
                                    "text": cleaned_text,
                                    "length": len(cleaned_text)
                                })
                    
                    # Recurse into nested objects
                    recursive_extract(value, new_path)
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{current_path}[{i}]" if current_path else f"[{i}]"
                    recursive_extract(item, new_path)
        
        recursive_extract(data, path)
        return text_chunks
    
    def extract_metadata(self, data: Any) -> Dict[str, Any]:
        """
        Extract metadata from JSON data.
        
        Args:
            data: JSON data to process
            
        Returns:
            Metadata dictionary
        """
        metadata = {}
        
        def recursive_metadata_extract(obj, path=""):
            """Recursively extract metadata."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if this is a metadata field
                    if any(meta_field in key.lower() for meta_field in self.metadata_fields):
                        if isinstance(value, (str, int, float, bool)) and value is not None:
                            metadata[current_path] = value
                    
                    # Also recurse to find nested metadata
                    if isinstance(value, (dict, list)):
                        recursive_metadata_extract(value, current_path)
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, dict):
                        recursive_metadata_extract(item, f"{path}[{i}]")
        
        recursive_metadata_extract(data)
        return metadata
    
    def normalize_record(self, data: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """
        Normalize a single record.
        
        Args:
            data: Raw data record
            source_file: Source filename
            
        Returns:
            Normalized record
        """
        # Extract components
        text_chunks = self.extract_text_content(data)
        metadata = self.extract_metadata(data)
        
        # Create a record ID
        record_id = hashlib.md5(f"{source_file}_{json.dumps(data, sort_keys=True)}".encode()).hexdigest()[:16]
        
        # Combine all text into a single content field
        combined_text = " ".join([chunk["text"] for chunk in text_chunks])
        
        normalized = {
            "id": record_id,
            "source_file": source_file,
            "source_endpoint": source_file.replace("_", "/").replace("param ", ""),
            "content": combined_text,
            "text_chunks": text_chunks,
            "metadata": metadata,
            "processing_timestamp": datetime.now().isoformat(),
            "content_length": len(combined_text),
            "chunk_count": len(text_chunks)
        }
        
        return normalized
    
    def process_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Process a single JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of normalized records
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            records = []
            source_file = file_path.stem
            
            # Handle different data structures
            if isinstance(raw_data, dict):
                if "hydra:member" in raw_data:
                    # Hydra collection format
                    for item in raw_data["hydra:member"]:
                        record = self.normalize_record(item, source_file)
                        records.append(record)
                else:
                    # Single object
                    record = self.normalize_record(raw_data, source_file)
                    records.append(record)
                    
            elif isinstance(raw_data, list):
                # Array of objects
                for i, item in enumerate(raw_data):
                    if isinstance(item, dict):
                        record = self.normalize_record(item, f"{source_file}_{i}")
                        records.append(record)
            
            self.stats["files_processed"] += 1
            self.stats["records_extracted"] += len(records)
            
            return records
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            self.stats["errors"] += 1
            return []
    
    def process_all_files(self) -> Dict[str, Any]:
        """
        Process all JSON files in the raw data directory.
        
        Returns:
            Processing summary
        """
        self.logger.info("Starting data processing...")
        
        all_records = []
        file_summaries = []
        
        # Process each JSON file
        for json_file in self.raw_data_dir.glob("*.json"):
            if json_file.name.endswith("_summary.json"):
                continue  # Skip summary files
            
            self.logger.info(f"Processing: {json_file.name}")
            records = self.process_json_file(json_file)
            
            if records:
                all_records.extend(records)
                
                # Save individual processed file
                output_file = self.processed_data_dir / "normalized" / f"{json_file.stem}_normalized.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
                
                file_summaries.append({
                    "source_file": json_file.name,
                    "records_count": len(records),
                    "total_text_length": sum(r["content_length"] for r in records),
                    "output_file": output_file.name
                })
        
        # Save combined dataset
        if all_records:
            combined_file = self.processed_data_dir / "all_records_normalized.json"
            with open(combined_file, 'w', encoding='utf-8') as f:
                json.dump(all_records, f, ensure_ascii=False, indent=2)
            
            # Create a pandas DataFrame for analysis
            df_records = []
            for record in all_records:
                df_records.append({
                    "id": record["id"],
                    "source_file": record["source_file"],
                    "source_endpoint": record["source_endpoint"],
                    "content_length": record["content_length"],
                    "chunk_count": record["chunk_count"],
                    "has_content": len(record["content"].strip()) > 0
                })
            
            df = pd.DataFrame(df_records)
            df.to_csv(self.processed_data_dir / "records_summary.csv", index=False)
            df.to_parquet(self.processed_data_dir / "records_summary.parquet", index=False)
        
        # Create processing summary
        summary = {
            "processing_stats": self.stats.copy(),
            "total_records": len(all_records),
            "file_summaries": file_summaries,
            "output_files": {
                "combined_records": "all_records_normalized.json",
                "summary_csv": "records_summary.csv",
                "summary_parquet": "records_summary.parquet"
            },
            "content_statistics": {
                "total_content_length": sum(r["content_length"] for r in all_records),
                "avg_content_length": np.mean([r["content_length"] for r in all_records]) if all_records else 0,
                "records_with_content": sum(1 for r in all_records if len(r["content"].strip()) > 0)
            }
        }
        
        # Save summary
        with open(self.processed_data_dir / "processing_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Processing complete: {len(all_records)} records from {self.stats['files_processed']} files")
        
        return summary
    
    def create_text_chunks_for_vectorization(self, max_chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]:
        """
        Create text chunks suitable for vectorization.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            overlap: Character overlap between chunks
            
        Returns:
            List of text chunks
        """
        combined_file = self.processed_data_dir / "all_records_normalized.json"
        if not combined_file.exists():
            self.logger.error("No normalized data found. Run process_all_files() first.")
            return []
        
        with open(combined_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        chunks = []
        chunk_id = 0
        
        for record in records:
            content = record["content"]
            if len(content.strip()) < 50:  # Skip very short content
                continue
            
            # Split into chunks
            if len(content) <= max_chunk_size:
                # Single chunk
                chunks.append({
                    "chunk_id": chunk_id,
                    "record_id": record["id"],
                    "source_endpoint": record["source_endpoint"],
                    "text": content,
                    "metadata": record["metadata"],
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "length": len(content)
                })
                chunk_id += 1
            else:
                # Multiple chunks with overlap
                start = 0
                chunk_index = 0
                total_chunks = (len(content) + max_chunk_size - overlap - 1) // (max_chunk_size - overlap)
                
                while start < len(content):
                    end = min(start + max_chunk_size, len(content))
                    chunk_text = content[start:end]
                    
                    chunks.append({
                        "chunk_id": chunk_id,
                        "record_id": record["id"],
                        "source_endpoint": record["source_endpoint"],
                        "text": chunk_text,
                        "metadata": record["metadata"],
                        "chunk_index": chunk_index,
                        "total_chunks": total_chunks,
                        "length": len(chunk_text)
                    })
                    
                    chunk_id += 1
                    chunk_index += 1
                    start += max_chunk_size - overlap
        
        # Save chunks
        chunks_file = self.processed_data_dir / "text_content" / "vectorization_chunks.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        # Also save as CSV for easy analysis
        chunks_df = pd.DataFrame(chunks)
        chunks_df.to_csv(self.processed_data_dir / "text_content" / "vectorization_chunks.csv", index=False)
        
        self.logger.info(f"Created {len(chunks)} text chunks for vectorization")
        
        return chunks


def main():
    """Main function for testing the parser."""
    parser = UtdanningDataParser(
        raw_data_dir="utdanning_data/raw",
        processed_data_dir="utdanning_data/processed"
    )
    
    # Process all files
    summary = parser.process_all_files()
    
    # Create chunks for vectorization
    chunks = parser.create_text_chunks_for_vectorization()
    
    print(f"\nProcessing Summary:")
    print(f"Files processed: {summary['processing_stats']['files_processed']}")
    print(f"Records extracted: {summary['total_records']}")
    print(f"Text chunks created: {len(chunks)}")
    print(f"Total content length: {summary['content_statistics']['total_content_length']} characters")


if __name__ == "__main__":
    main()