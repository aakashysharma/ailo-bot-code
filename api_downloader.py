"""
Utdanning.no API Data Downloader
A comprehensive tool to download and process data from api.utdanning.no for LLM vectorization.
"""

import asyncio
import aiohttp
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlparse, parse_qs
import re
from tqdm.asyncio import tqdm as atqdm


class UtdanningAPIDownloader:
    """
    Main class for downloading data from the Utdanning.no API.
    Handles rate limiting, error recovery, and data persistence.
    """
    
    def __init__(
        self,
        base_url: str = "https://api.utdanning.no",
        output_dir: str = "data",
        max_concurrent: int = 10,
        rate_limit: float = 0.1,
        retry_attempts: int = 3,
        timeout: int = 30
    ):
        """
        Initialize the API downloader.
        
        Args:
            base_url: Base URL for the API
            output_dir: Directory to save downloaded data
            max_concurrent: Maximum concurrent requests
            rate_limit: Minimum time between requests (seconds)
            retry_attempts: Number of retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit
        self.retry_attempts = retry_attempts
        self.timeout = timeout
        
        # Create output directories
        self.raw_data_dir = self.output_dir / "raw"
        self.processed_data_dir = self.output_dir / "processed"
        self.logs_dir = self.output_dir / "logs"
        
        for dir_path in [self.raw_data_dir, self.processed_data_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_data_size": 0,
            "endpoints_processed": 0
        }
        
        # Session for requests
        self.session: Optional[aiohttp.ClientSession] = None
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs_dir / f"downloader_{int(time.time())}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def load_url_list(self, url_list_file: str) -> List[Dict[str, str]]:
        """
        Load the URL list from the JSON file.
        
        Args:
            url_list_file: Path to the URL list JSON file
            
        Returns:
            List of URL configurations
        """
        try:
            with open(url_list_file, 'r', encoding='utf-8') as f:
                urls = json.load(f)
            self.logger.info(f"Loaded {len(urls)} URLs from {url_list_file}")
            return urls
        except Exception as e:
            self.logger.error(f"Error loading URL list: {e}")
            raise
    
    def _sanitize_filename(self, url: str) -> str:
        """
        Create a safe filename from a URL.
        
        Args:
            url: The URL to convert
            
        Returns:
            Safe filename string
        """
        # Remove the base URL and clean up
        path = url.replace(self.base_url, "").lstrip("/")
        # Replace problematic characters
        safe_name = re.sub(r'[<>:"/\\|?*{}]', '_', path)
        # Replace multiple underscores with single
        safe_name = re.sub(r'_+', '_', safe_name)
        return safe_name.strip('_')
    
    def _is_parameterized_url(self, url: str) -> bool:
        """
        Check if URL contains parameters like {id}.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL has parameters
        """
        return '{' in url and '}' in url
    
    def _extract_parameter_names(self, url: str) -> List[str]:
        """
        Extract parameter names from a parameterized URL.
        
        Args:
            url: Parameterized URL
            
        Returns:
            List of parameter names
        """
        return re.findall(r'\{([^}]+)\}', url)
    
    async def _make_request(self, url: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """
        Make a single HTTP request with error handling.
        
        Args:
            url: URL to request
            session: aiohttp session
            
        Returns:
            Response data or None if failed
        """
        for attempt in range(self.retry_attempts):
            try:
                self.stats["total_requests"] += 1
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.stats["successful_requests"] += 1
                        self.stats["total_data_size"] += len(str(data))
                        return data
                    else:
                        self.logger.warning(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout for {url} (attempt {attempt + 1})")
            except Exception as e:
                self.logger.warning(f"Error requesting {url} (attempt {attempt + 1}): {e}")
            
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        self.stats["failed_requests"] += 1
        return None
    
    async def _save_data(self, data: Dict, filename: str) -> bool:
        """
        Save data to a JSON file.
        
        Args:
            data: Data to save
            filename: Output filename
            
        Returns:
            True if successful
        """
        try:
            file_path = self.raw_data_dir / f"{filename}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving {filename}: {e}")
            return False
    
    async def _download_endpoint(self, url_config: Dict[str, str], session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """
        Download data from a single endpoint.
        
        Args:
            url_config: URL configuration dict
            session: aiohttp session
            semaphore: Concurrency limiter
            
        Returns:
            Result dict with success status and data
        """
        async with semaphore:
            url = url_config["url"]
            method = url_config.get("method", "GET")
            
            if method != "GET":
                # Skip non-GET requests for now
                return {"success": False, "url": url, "reason": "Non-GET method"}
            
            if self._is_parameterized_url(url):
                return await self._handle_parameterized_url(url, session)
            else:
                return await self._handle_simple_url(url, session)
    
    async def _handle_simple_url(self, url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """
        Handle a simple URL without parameters.
        
        Args:
            url: URL to download
            session: aiohttp session
            
        Returns:
            Result dict
        """
        await asyncio.sleep(self.rate_limit)  # Rate limiting
        
        data = await self._make_request(url, session)
        if data is not None:
            filename = self._sanitize_filename(url)
            if await self._save_data(data, filename):
                self.logger.info(f"Downloaded: {url}")
                return {"success": True, "url": url, "filename": filename, "data_size": len(str(data))}
        
        return {"success": False, "url": url, "reason": "Request failed"}
    
    async def _handle_parameterized_url(self, url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """
        Handle URLs with parameters like {id}.
        
        Args:
            url: Parameterized URL
            session: aiohttp session
            
        Returns:
            Result dict
        """
        # For now, skip parameterized URLs - we'll handle them in phase 2
        # after we have data to extract IDs from
        self.logger.info(f"Skipping parameterized URL for now: {url}")
        return {"success": False, "url": url, "reason": "Parameterized URL - needs ID extraction"}
    
    async def download_all_endpoints(self, url_list_file: str) -> Dict[str, Any]:
        """
        Download data from all endpoints in the URL list.
        
        Args:
            url_list_file: Path to URL list JSON file
            
        Returns:
            Summary of download results
        """
        urls = self.load_url_list(url_list_file)
        
        # Filter out non-GET requests and group by type
        get_urls = [url for url in urls if url.get("method", "GET") == "GET"]
        simple_urls = [url for url in get_urls if not self._is_parameterized_url(url["url"])]
        param_urls = [url for url in get_urls if self._is_parameterized_url(url["url"])]
        
        self.logger.info(f"Found {len(simple_urls)} simple URLs and {len(param_urls)} parameterized URLs")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Download simple URLs first
        results = []
        if simple_urls:
            self.logger.info("Downloading simple endpoints...")
            tasks = [
                self._download_endpoint(url_config, self.session, semaphore)
                for url_config in simple_urls
            ]
            
            results = await atqdm.gather(*tasks, desc="Downloading endpoints")
        
        # Process results
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        
        self.stats["endpoints_processed"] = len(results)
        
        summary = {
            "total_endpoints": len(urls),
            "simple_endpoints": len(simple_urls),
            "parameterized_endpoints": len(param_urls),
            "successful_downloads": len(successful),
            "failed_downloads": len(failed),
            "stats": self.stats.copy(),
            "successful_results": successful,
            "failed_results": failed
        }
        
        # Save summary with proper encoding
        await self._save_data(summary, "download_summary")
        
        self.logger.info(f"Download complete: {len(successful)}/{len(simple_urls)} successful")
        
        return summary


async def main():
    """Main function for testing the downloader."""
    downloader = UtdanningAPIDownloader(
        output_dir="utdanning_data",
        max_concurrent=5,
        rate_limit=0.2
    )
    
    async with downloader:
        summary = await downloader.download_all_endpoints("url_list.json")
        
        print(f"\nDownload Summary:")
        print(f"Successful: {summary['successful_downloads']}")
        print(f"Failed: {summary['failed_downloads']}")
        print(f"Total data size: {summary['stats']['total_data_size']} characters")


if __name__ == "__main__":
    asyncio.run(main())