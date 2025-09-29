#!/usr/bin/env python3
"""
Main Execution Script for Utdanning.no API Data Pipeline
Orchestrates the complete download, processing, and vectorization preparation pipeline.

Usage:
    python main.py [--download-only] [--process-only] [--extract-only] [--output-dir OUTPUT_DIR]
"""

import asyncio
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, Any
import json
import sys

# Import our custom modules
from api_downloader import UtdanningAPIDownloader
from url_processor import URLProcessor, download_with_parameterized_support
from data_parser import UtdanningDataParser
from text_extractor import TextExtractor


class UtdanningDataPipeline:
    """
    Main pipeline orchestrator for the Utdanning.no API data processing.
    """
    
    def __init__(self, output_dir: str = "utdanning_data", config: Dict[str, Any] = None):
        """
        Initialize the pipeline.
        
        Args:
            output_dir: Base directory for all output
            config: Configuration dictionary
        """
        self.output_dir = Path(output_dir)
        self.config = config or {}
        
        # Create directory structure
        self.raw_data_dir = self.output_dir / "raw"
        self.processed_data_dir = self.output_dir / "processed"
        self.logs_dir = self.output_dir / "logs"
        
        for dir_path in [self.raw_data_dir, self.processed_data_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Pipeline statistics
        self.pipeline_stats = {
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "phases_completed": [],
            "total_files_downloaded": 0,
            "total_records_processed": 0,
            "total_documents_created": 0,
            "errors": []
        }
    
    def _setup_logging(self):
        """Setup comprehensive logging."""
        log_file = self.logs_dir / f"pipeline_{int(time.time())}.log"
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Setup root logger
        self.logger = logging.getLogger('UtdanningPipeline')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Pipeline initialized. Output directory: {self.output_dir}")
        self.logger.info(f"Log file: {log_file}")
    
    async def run_download_phase(self, url_list_file: str) -> Dict[str, Any]:
        """
        Run the data download phase.
        
        Args:
            url_list_file: Path to URL list JSON file
            
        Returns:
            Download phase summary
        """
        self.logger.info("=" * 60)
        self.logger.info("PHASE 1: DATA DOWNLOAD")
        self.logger.info("=" * 60)
        
        try:
            # Use the complete download function with parameterized support
            summary = await download_with_parameterized_support(
                url_list_file=url_list_file,
                output_dir=str(self.output_dir)
            )
            
            self.pipeline_stats["phases_completed"].append("download")
            self.pipeline_stats["total_files_downloaded"] = summary.get("total_successful", 0)
            
            self.logger.info(f"Download phase completed successfully")
            self.logger.info(f"Files downloaded: {self.pipeline_stats['total_files_downloaded']}")
            
            return summary
            
        except Exception as e:
            error_msg = f"Download phase failed: {e}"
            self.logger.error(error_msg)
            self.pipeline_stats["errors"].append(error_msg)
            raise
    
    def run_processing_phase(self) -> Dict[str, Any]:
        """
        Run the data processing phase.
        
        Returns:
            Processing phase summary
        """
        self.logger.info("=" * 60)
        self.logger.info("PHASE 2: DATA PROCESSING")
        self.logger.info("=" * 60)
        
        try:
            parser = UtdanningDataParser(
                raw_data_dir=str(self.raw_data_dir),
                processed_data_dir=str(self.processed_data_dir),
                logger=self.logger
            )
            
            summary = parser.process_all_files()
            
            self.pipeline_stats["phases_completed"].append("processing")
            self.pipeline_stats["total_records_processed"] = summary.get("total_records", 0)
            
            self.logger.info(f"Processing phase completed successfully")
            self.logger.info(f"Records processed: {self.pipeline_stats['total_records_processed']}")
            
            return summary
            
        except Exception as e:
            error_msg = f"Processing phase failed: {e}"
            self.logger.error(error_msg)
            self.pipeline_stats["errors"].append(error_msg)
            raise
    
    def run_extraction_phase(self) -> Dict[str, Any]:
        """
        Run the text extraction phase.
        
        Returns:
            Extraction phase summary
        """
        self.logger.info("=" * 60)
        self.logger.info("PHASE 3: TEXT EXTRACTION FOR VECTORIZATION")
        self.logger.info("=" * 60)
        
        try:
            extractor = TextExtractor(
                processed_data_dir=str(self.processed_data_dir),
                logger=self.logger
            )
            
            summary = extractor.create_vectorization_dataset()
            
            self.pipeline_stats["phases_completed"].append("extraction")
            self.pipeline_stats["total_documents_created"] = summary.get("total_documents", 0)
            
            self.logger.info(f"Extraction phase completed successfully")
            self.logger.info(f"Documents created: {self.pipeline_stats['total_documents_created']}")
            
            return summary
            
        except Exception as e:
            error_msg = f"Extraction phase failed: {e}"
            self.logger.error(error_msg)
            self.pipeline_stats["errors"].append(error_msg)
            raise
    
    async def run_complete_pipeline(self, url_list_file: str) -> Dict[str, Any]:
        """
        Run the complete pipeline from start to finish.
        
        Args:
            url_list_file: Path to URL list JSON file
            
        Returns:
            Complete pipeline summary
        """
        self.pipeline_stats["start_time"] = time.time()
        
        self.logger.info("🚀 Starting complete Utdanning.no data pipeline")
        self.logger.info(f"URL list file: {url_list_file}")
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info("🇳🇴 Norwegian character encoding: UTF-8 enabled")
        
        try:
            # Phase 1: Download
            download_summary = await self.run_download_phase(url_list_file)
            
            # Phase 2: Process
            processing_summary = self.run_processing_phase()
            
            # Phase 3: Extract
            extraction_summary = self.run_extraction_phase()
            
            # Final statistics
            self.pipeline_stats["end_time"] = time.time()
            self.pipeline_stats["duration_seconds"] = self.pipeline_stats["end_time"] - self.pipeline_stats["start_time"]
            
            # Create comprehensive summary
            complete_summary = {
                "pipeline_stats": self.pipeline_stats.copy(),
                "download_summary": download_summary,
                "processing_summary": processing_summary,
                "extraction_summary": extraction_summary,
                "success": True,
                "output_structure": self._create_output_structure_summary()
            }
            
            # Save complete summary
            summary_file = self.output_dir / "complete_pipeline_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(complete_summary, f, ensure_ascii=False, indent=2)
            
            self._log_final_summary(complete_summary)
            
            return complete_summary
            
        except Exception as e:
            self.pipeline_stats["end_time"] = time.time()
            self.pipeline_stats["duration_seconds"] = self.pipeline_stats["end_time"] - self.pipeline_stats["start_time"]
            
            error_summary = {
                "pipeline_stats": self.pipeline_stats.copy(),
                "success": False,
                "error": str(e)
            }
            
            self.logger.error(f"Pipeline failed: {e}")
            return error_summary
    
    def _create_output_structure_summary(self) -> Dict[str, Any]:
        """Create a summary of the output file structure."""
        structure = {
            "base_directory": str(self.output_dir),
            "raw_data": {
                "directory": "raw/",
                "files": list(f.name for f in self.raw_data_dir.glob("*.json") if f.is_file())[:10]  # First 10
            },
            "processed_data": {
                "directory": "processed/",
                "key_files": [
                    "all_records_normalized.json",
                    "records_summary.csv",
                    "processing_summary.json"
                ]
            },
            "vectorization_data": {
                "directory": "processed/text_for_llm/",
                "key_files": [
                    "vectorization_dataset.json",
                    "vectorization_dataset.csv",
                    "texts_only.txt",
                    "dataset_analysis.json"
                ]
            },
            "logs": {
                "directory": "logs/",
                "files": list(f.name for f in self.logs_dir.glob("*.log") if f.is_file())
            }
        }
        
        return structure
    
    def _log_final_summary(self, summary: Dict[str, Any]):
        """Log the final pipeline summary."""
        self.logger.info("=" * 80)
        self.logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        self.logger.info("=" * 80)
        
        duration_minutes = self.pipeline_stats["duration_seconds"] / 60
        
        self.logger.info(f"⏱️  Total duration: {duration_minutes:.1f} minutes")
        self.logger.info(f"📁 Files downloaded: {self.pipeline_stats['total_files_downloaded']}")
        self.logger.info(f"📊 Records processed: {self.pipeline_stats['total_records_processed']}")
        self.logger.info(f"📝 Documents created: {self.pipeline_stats['total_documents_created']}")
        self.logger.info(f"✅ Phases completed: {', '.join(self.pipeline_stats['phases_completed'])}")
        
        if self.pipeline_stats["errors"]:
            self.logger.warning(f"⚠️  Errors encountered: {len(self.pipeline_stats['errors'])}")
        
        # Key output files
        self.logger.info("\n📂 Key output files created:")
        vectorization_dir = self.processed_data_dir / "text_for_llm"
        if vectorization_dir.exists():
            for file_name in ["vectorization_dataset.json", "texts_only.txt"]:
                file_path = vectorization_dir / file_name
                if file_path.exists():
                    file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                    self.logger.info(f"   • {file_name} ({file_size:.1f} MB)")
        
        self.logger.info(f"\n🎯 Ready for LLM vectorization!")
        self.logger.info(f"📍 Output location: {self.output_dir}")


def create_default_config() -> Dict[str, Any]:
    """Create default configuration."""
    return {
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


async def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Download and process Utdanning.no API data for LLM vectorization"
    )
    
    parser.add_argument(
        "--output-dir", 
        default="utdanning_data",
        help="Output directory for all data (default: utdanning_data)"
    )
    
    parser.add_argument(
        "--url-list",
        default="url_list.json", 
        help="Path to URL list JSON file (default: url_list.json)"
    )
    
    parser.add_argument(
        "--download-only", 
        action="store_true",
        help="Only run the download phase"
    )
    
    parser.add_argument(
        "--process-only", 
        action="store_true",
        help="Only run the processing phase (requires existing raw data)"
    )
    
    parser.add_argument(
        "--extract-only", 
        action="store_true",
        help="Only run the extraction phase (requires existing processed data)"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration JSON file"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = create_default_config()
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config file {args.config}: {e}")
    
    # Initialize pipeline
    pipeline = UtdanningDataPipeline(
        output_dir=args.output_dir,
        config=config
    )
    
    try:
        # Run requested phases
        if args.download_only:
            summary = await pipeline.run_download_phase(args.url_list)
        elif args.process_only:
            summary = pipeline.run_processing_phase()
        elif args.extract_only:
            summary = pipeline.run_extraction_phase()
        else:
            # Run complete pipeline
            summary = await pipeline.run_complete_pipeline(args.url_list)
        
        # Print success message
        if summary.get("success", True):
            print(f"\n✅ Successfully completed! Check {args.output_dir} for results.")
        else:
            print(f"\n❌ Pipeline failed. Check logs in {args.output_dir}/logs/")
            
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we have the event loop for asyncio
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())