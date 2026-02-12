"""
URL Processing Logic for Utdanning.no API
Handles parameterized URLs by extracting IDs from downloaded data.
"""

import json
import re
import asyncio
import aiohttp
from typing import Dict, List, Set, Any, Optional
from pathlib import Path
import logging


class URLProcessor:
    """
    Processes URLs and handles parameter extraction for the Utdanning API.
    """
    
    def __init__(self, downloader, logger: Optional[logging.Logger] = None):
        """
        Initialize URL processor.
        
        Args:
            downloader: UtdanningAPIDownloader instance
            logger: Logger instance
        """
        self.downloader = downloader
        self.logger = logger or logging.getLogger(__name__)
        self.extracted_ids = {}  # Cache for extracted IDs
    
    def extract_ids_from_data(self, data: Any, id_fields: List[str] = None) -> Set[str]:
        """
        Extract potential IDs from JSON data.
        
        Args:
            data: JSON data to search
            id_fields: Specific field names to look for IDs
            
        Returns:
            Set of extracted ID values
        """
        if id_fields is None:
            id_fields = [
                'id', 'nid', 'uno_id', 'programomradekode10', 'yrkeskode_styrk08', 
                'styrk98_kode', 'nus_kode', 'vilbli_org_id', 'org_id'
            ]
        
        ids = set()
        
        def is_valid_id(val: str) -> bool:
            """Check if a string looks like a valid ID rather than a path or filename."""
            if not val or len(val) > 40:
                return False
            # Exclude strings that look like internal JSON paths or complex structures
            if val.count('_') > 4 or val.count('.') > 2 or ';' in val:
                return False
            # Typical IDs: numeric, y_*, u_*, or alphanumeric codes
            if re.match(r'^(y_|u_|v_|[0-9]+|[a-zA-Z0-9-]+)$', val):
                return True
            return False

        def recursive_extract(obj, path=""):
            """Recursively extract IDs from nested data."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if this field might be an ID
                    if any(id_field in key.lower() for id_field in id_fields):
                        if isinstance(value, (str, int)):
                            str_val = str(value)
                            if is_valid_id(str_val):
                                ids.add(str_val)
                    
                    # Recurse into nested objects
                    recursive_extract(value, current_path)
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    recursive_extract(item, f"{path}[{i}]")
            
            elif isinstance(obj, (str, int)) and obj:
                # Check if this looks like an ID (numeric or alphanumeric)
                str_val = str(obj)
                if is_valid_id(str_val):
                    if path and any(id_field in path.lower() for id_field in id_fields):
                        ids.add(str_val)
        
        recursive_extract(data)
        return ids
    
    def analyze_downloaded_data_for_ids(self) -> Dict[str, Set[str]]:
        """
        Analyze all downloaded data to extract potential IDs.
        
        Returns:
            Dictionary mapping ID types to sets of values
        """
        id_collections = {}
        raw_data_dir = self.downloader.raw_data_dir
        
        self.logger.info("Analyzing downloaded data for ID extraction...")
        
        for json_file in raw_data_dir.glob("*.json"):
            # Skip summary files and parameterized download results
            if json_file.stem in ['complete_download_summary', 'parameterized_download_summary'] or json_file.stem.startswith('param_'):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract IDs from this file
                ids = self.extract_ids_from_data(data)
                
                # Categorize IDs based on filename/context
                filename = json_file.stem
                id_collections[filename] = ids
                
                if ids:
                    self.logger.debug(f"Found {len(ids)} potential IDs in {filename}")
                
            except Exception as e:
                self.logger.warning(f"Error processing {json_file}: {e}")
        
        return id_collections
    
    def match_ids_to_parameterized_urls(self, parameterized_urls: List[str], id_collections: Dict[str, Set[str]]) -> Dict[str, List[str]]:
        """
        Match extracted IDs to parameterized URLs.
        
        Args:
            parameterized_urls: List of URLs with parameters
            id_collections: Extracted IDs by source
            
        Returns:
            Dictionary mapping URL templates to lists of concrete URLs
        """
        url_mappings = {}
        
        for url_template in parameterized_urls:
            # Extract parameter names from URL
            param_names = re.findall(r'\{([^}]+)\}', url_template)
            concrete_urls = []
            
            for param_name in param_names:
                # Find matching IDs for this parameter
                matching_ids = set()
                
                # Prefix filtering logic
                prefix_filter = None
                if "/sammenligning/yrke/" in url_template or "yrke" in url_template.lower():
                    prefix_filter = "y_"
                elif "/sammenligning/utdanning/" in url_template or "utdanning" in url_template.lower():
                    prefix_filter = "u_"

                # Look for IDs that might match this parameter
                for source, ids in id_collections.items():
                    # Simple heuristics for matching
                    field_match = param_name.lower() in source.lower() or (param_name == 'id' and 'id' in source.lower())
                    
                    if field_match:
                        for val in ids:
                            if prefix_filter:
                                if val.startswith(prefix_filter):
                                    matching_ids.add(val)
                            else:
                                matching_ids.add(val)
                
                # Generate concrete URLs
                if matching_ids:
                    # Sort to ensure consistency and take a limited sample
                    sorted_ids = sorted(list(matching_ids))
                    for id_val in sorted_ids[:100]:  # Limit to first 100 IDs
                        concrete_url = url_template.replace(f'{{{param_name}}}', str(id_val))
                        concrete_urls.append(concrete_url)
            
            if concrete_urls:
                url_mappings[url_template] = concrete_urls
                self.logger.info(f"Generated {len(concrete_urls)} URLs from template: {url_template}")
        
        return url_mappings
    
    async def download_parameterized_endpoints(self, url_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Download data from parameterized endpoints using extracted IDs.
        
        Args:
            url_list: List of all URL configurations
            
        Returns:
            Summary of parameterized downloads
        """
        # Get parameterized URLs
        param_urls = [
            url_config["url"] for url_config in url_list 
            if self.downloader._is_parameterized_url(url_config["url"]) 
            and url_config.get("method", "GET") == "GET"
        ]
        
        if not param_urls:
            return {"message": "No parameterized URLs to process"}
        
        # Analyze downloaded data for IDs
        id_collections = self.analyze_downloaded_data_for_ids()
        
        # Match IDs to URLs
        url_mappings = self.match_ids_to_parameterized_urls(param_urls, id_collections)
        
        # Download concrete URLs
        results = []
        semaphore = asyncio.Semaphore(self.downloader.max_concurrent)
        
        for template, concrete_urls in url_mappings.items():
            self.logger.info(f"Downloading {len(concrete_urls)} URLs for template: {template}")
            
            # Limit concurrent downloads per template
            for i in range(0, len(concrete_urls), 50):  # Process in batches of 50
                batch = concrete_urls[i:i+50]
                tasks = []
                
                for url in batch:
                    task = self._download_parameterized_url(url, semaphore)
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                results.extend([r for r in batch_results if not isinstance(r, Exception)])
        
        # Compile summary
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        
        summary = {
            "parameterized_templates": len(url_mappings),
            "total_concrete_urls": sum(len(urls) for urls in url_mappings.values()),
            "successful_downloads": len(successful),
            "failed_downloads": len(failed),
            "url_mappings": {k: len(v) for k, v in url_mappings.items()},
            "id_collections_summary": {k: len(v) for k, v in id_collections.items()}
        }
        
        # Save summary
        await self.downloader._save_data(summary, "parameterized_download_summary")
        
        return summary
    
    async def _download_parameterized_url(self, url: str, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """
        Download a single parameterized URL.
        
        Args:
            url: Concrete URL to download
            semaphore: Concurrency limiter
            
        Returns:
            Result dictionary
        """
        async with semaphore:
            await asyncio.sleep(self.downloader.rate_limit)
            
            data = await self.downloader._make_request(url, self.downloader.session)
            if data is not None:
                # Create a safe filename for parameterized URLs
                filename = self.downloader._sanitize_filename(url)
                # Add a prefix to distinguish from simple URLs
                filename = f"param_{filename}"
                
                if await self.downloader._save_data(data, filename):
                    self.logger.info(f"Downloaded parameterized: {url}")
                    return {
                        "success": True, 
                        "url": url, 
                        "filename": filename, 
                        "data_size": len(str(data))
                    }
            
            return {"success": False, "url": url, "reason": "Request failed"}


# Integration with the main downloader
async def download_with_parameterized_support(url_list_file: str, output_dir: str = "utdanning_data"):
    """
    Complete download process including parameterized URLs.
    
    Args:
        url_list_file: Path to URL list JSON
        output_dir: Output directory for data
    """
    from api_downloader import UtdanningAPIDownloader
    
    downloader = UtdanningAPIDownloader(
        output_dir=output_dir,
        max_concurrent=5,
        rate_limit=0.2
    )
    
    async with downloader:
        # Phase 1: Download simple endpoints
        print("Phase 1: Downloading simple endpoints...")
        summary1 = await downloader.download_all_endpoints(url_list_file)
        
        # Phase 2: Process parameterized endpoints
        print("Phase 2: Processing parameterized endpoints...")
        processor = URLProcessor(downloader)
        url_list = downloader.load_url_list(url_list_file)
        summary2 = await processor.download_parameterized_endpoints(url_list)
        
        # Combined summary
        total_summary = {
            "phase1_simple": summary1,
            "phase2_parameterized": summary2,
            "total_successful": summary1["successful_downloads"] + summary2.get("successful_downloads", 0),
            "total_failed": summary1["failed_downloads"] + summary2.get("failed_downloads", 0)
        }
        
        await downloader._save_data(total_summary, "complete_download_summary")
        
        print(f"\nComplete Download Summary:")
        print(f"Simple endpoints: {summary1['successful_downloads']}/{summary1['simple_endpoints']}")
        print(f"Parameterized endpoints: {summary2.get('successful_downloads', 0)}")
        print(f"Total successful: {total_summary['total_successful']}")
        
        return total_summary