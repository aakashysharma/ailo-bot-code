#!/usr/bin/env python3
"""
Automatic Data Update Scheduler for AILO
Runs the data pipeline every night at midnight to keep knowledge base fresh
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import sys


class AILODataScheduler:
    """
    Scheduler to automatically update AILO's knowledge base
    """
    
    def __init__(self, data_dir: str = "utdanning_data", log_dir: str = "scheduler_logs"):
        """
        Initialize the scheduler.
        
        Args:
            data_dir: Directory where data is stored
            log_dir: Directory for scheduler logs
        """
        self.data_dir = Path(data_dir)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.log_dir / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - AILOScheduler - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('AILOScheduler')
    
    def run_data_pipeline(self):
        """
        Run the complete data pipeline to update knowledge base.
        """
        self.logger.info("=" * 60)
        self.logger.info("🔄 Starting scheduled data update")
        self.logger.info("=" * 60)
        
        try:
            # Run the main pipeline
            result = subprocess.run(
                [sys.executable, "main.py"],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                self.logger.info("✅ Data pipeline completed successfully")
                self.logger.info(f"Output:\n{result.stdout}")
                
                # Log summary
                self._log_update_summary()
                
            else:
                self.logger.error(f"❌ Data pipeline failed with code {result.returncode}")
                self.logger.error(f"Error output:\n{result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Data pipeline timed out after 1 hour")
        except Exception as e:
            self.logger.error(f"❌ Error running data pipeline: {e}")
    
    def _log_update_summary(self):
        """Log summary of the data update."""
        try:
            # Check data directories
            raw_count = len(list(self.data_dir.glob("raw/*.json")))
            processed_count = len(list(self.data_dir.glob("processed/**/*.json")))
            
            self.logger.info(f"📊 Update Summary:")
            self.logger.info(f"   Raw files: {raw_count}")
            self.logger.info(f"   Processed files: {processed_count}")
            
            # Check vectorization dataset
            vector_file = self.data_dir / "processed" / "text_for_llm" / "vectorization_dataset.json"
            if vector_file.exists():
                import json
                with open(vector_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    doc_count = len(data) if isinstance(data, list) else len(data.get('documents', []))
                    self.logger.info(f"   Vectorization documents: {doc_count}")
            
            self.logger.info(f"   Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.logger.warning(f"Could not generate update summary: {e}")
    
    def schedule_midnight_update(self):
        """
        Schedule the data pipeline to run at midnight every day.
        """
        schedule.every().day.at("00:00").do(self.run_data_pipeline)
        self.logger.info("📅 Scheduled daily update at midnight (00:00)")
    
    def schedule_custom_time(self, time_str: str):
        """
        Schedule update at a custom time.
        
        Args:
            time_str: Time in HH:MM format (e.g., "02:30")
        """
        schedule.every().day.at(time_str).do(self.run_data_pipeline)
        self.logger.info(f"📅 Scheduled daily update at {time_str}")
    
    def run_scheduler(self):
        """
        Run the scheduler loop (blocking).
        """
        self.logger.info("🚀 AILO Data Scheduler started")
        self.logger.info(f"Next scheduled run: {schedule.next_run()}")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("⏹️  Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Scheduler error: {e}")


def main():
    """Main function to run the scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AILO Data Scheduler - Automatic nightly updates"
    )
    parser.add_argument(
        "--time",
        default="00:00",
        help="Time to run update (HH:MM format, default: 00:00)"
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run data pipeline immediately"
    )
    parser.add_argument(
        "--data-dir",
        default="utdanning_data",
        help="Data directory (default: utdanning_data)"
    )
    
    args = parser.parse_args()
    
    # Initialize scheduler
    scheduler = AILODataScheduler(data_dir=args.data_dir)
    
    # Run immediately if requested
    if args.run_now:
        scheduler.logger.info("Running data pipeline immediately...")
        scheduler.run_data_pipeline()
        return
    
    # Schedule updates
    scheduler.schedule_custom_time(args.time)
    
    # Run scheduler loop
    scheduler.run_scheduler()


if __name__ == "__main__":
    main()
