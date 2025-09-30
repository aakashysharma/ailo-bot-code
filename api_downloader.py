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
from typing import Dict, List, Optional, Union, Any, Set, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re
from tqdm.asyncio import tqdm as atqdm
from itertools import product


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
            "endpoints_processed": 0,
            "parameter_combinations_generated": 0,
            "missing_dependencies": 0
        }
        
        # Session for requests
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Data store for extracted values
        self.extracted_data = {}
        
        # Parameter value cache
        self.parameter_values = {}
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.logs_dir / f"downloader_{int(time.time())}.log"
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Setup logger
        self.logger = logging.getLogger('UtdanningAPIDownloader')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
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
    
    def _sanitize_filename(self, url: str, params: Dict = None) -> str:
        """
        Create a safe filename from a URL and parameters.
        
        Args:
            url: The URL to convert
            params: Additional parameters to include in filename
            
        Returns:
            Safe filename string
        """
        # Remove the base URL and clean up
        path = url.replace(self.base_url, "").lstrip("/")
        
        # Add parameters to filename if present
        if params:
            param_str = "_".join([f"{k}-{v}" for k, v in sorted(params.items())])
            path = f"{path}_{param_str}"
        
        # Replace problematic characters
        safe_name = re.sub(r'[<>:"/\\|?*{}]', '_', path)
        # Replace multiple underscores with single
        safe_name = re.sub(r'_+', '_', safe_name)
        return safe_name.strip('_')
    
    def _has_query_parameters_that_need_values(self, url: str) -> bool:
        """
        Check if URL needs query parameters based on context.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL likely needs query parameters
        """
        # URLs that typically need parameters - expanded list
        needs_params = [
            # Sammenligning endpoints
            '/sammenligning/lonn',
            '/sammenligning/arbeidsledighet', 
            '/sammenligning/arbeidsmarked',
            '/sammenligning/entrepenorskap',
            '/sammenligning/stillinger-yrke',
            '/sammenligning/utdanning-yrke-rr',
            '/sammenligning/utdanning2yrke',
            '/sammenligning/yrke2utdanning',
            '/sammenligning/suggest',
            
            # Search endpoints
            '/search/facet',
            '/search/result',
            
            # Finnlarebedrift endpoints
            '/finnlarebedrift/result',
            '/finnlarebedrift/navnesok',
            
            # Studievelgeren endpoints
            '/studievelgeren/facet',
            '/studievelgeren/result',
            
            # OVTTAS endpoints
            '/ovttas/result',
            '/ovttas/suggest',
            
            # Character calculator
            '/karakterkalkulator/points',
            
            # ONet endpoints
            '/onet/onet_by_occupation',
            '/onet/onet_by_value', 
            '/onet/onet_by_yrke'
        ]
        return any(param_url in url for param_url in needs_params)
    
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
    
    def _get_query_parameters(self, url: str) -> Dict[str, List[str]]:
        """
        Extract query parameters from URL.
        
        Args:
            url: URL with query parameters
            
        Returns:
            Dict of parameter names to their values (as lists)
        """
        parsed = urlparse(url)
        return parse_qs(parsed.query)
    
    def _extract_values_from_data(self, data: Any, field_name: str) -> Set[str]:
        """
        Extract values for a specific field from nested JSON data.
        
        Args:
            data: JSON data to search
            field_name: Field name to extract values for
            
        Returns:
            Set of unique values found
        """
        values = set()
        
        def recursive_search(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Direct field match
                    if key == field_name:
                        if isinstance(value, (str, int)) and value:
                            values.add(str(value))
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, (str, int)) and item:
                                    values.add(str(item))
                    
                    # Check if this could be a nested structure with the field
                    if isinstance(value, dict):
                        # Special handling for sammenligning data structure
                        if field_name in ['sektor', 'arbeidstid', 'aldersklasse', 'ansiennitet']:
                            if key in ['P', 'S', 'A', 'H', 'F']:  # Common parameter values
                                values.add(key)
                    
                    recursive_search(value, current_path)
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    recursive_search(item, f"{path}[{i}]")
        
        recursive_search(data)
        return values
    
    def _analyze_downloaded_data_for_parameters(self) -> Dict[str, Set[str]]:
        """
        Analyze downloaded data to extract parameter values.
        
        Returns:
            Dict mapping parameter names to sets of possible values
        """
        parameter_values = {
            # Basic IDs
            'uno_id': set(),
            'id': set(),
            'nid': set(),
            'programomradekode10': set(),
            'yrkeskode_styrk08': set(),
            'styrk98_kode': set(),
            'nus_kode': set(),
            'vilbli_org_id': set(),
            
            # Sammenligning parameters
            'sektor': set(),
            'arbeidstid': set(), 
            'aldersklasse': set(),
            'ansiennitet': set(),
            
            # Search parameters
            'q': set(),  # Query string
            'facet': set(),  # Facet values
            'type': set(),  # Content type
            
            # Location parameters
            'fylke': set(),
            'kommune': set(),
            'region': set(),
            'sted': set(),
            
            # Education parameters  
            'utdanningsniva': set(),
            'studieniva': set(),
            'programomrade': set(),
            'fagkode': set(),
            
            # ONet parameters
            'occupation': set(),
            'interest': set(),
            'value': set(),
            
            # Finnlarebedrift parameters
            'fagomrade': set(),
            'bedrift': set(),
            'naringskode': set()
        }
        
        for json_file in self.raw_data_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract common parameter values
                for param in parameter_values:
                    values = self._extract_values_from_data(data, param)
                    parameter_values[param].update(values)
                
                # Special handling for different data types
                if 'sammenligning' in json_file.name:
                    self._extract_sammenligning_parameters(data, parameter_values)
                elif 'search' in json_file.name or 'studievelgeren' in json_file.name:
                    self._extract_search_parameters(data, parameter_values)
                elif 'finnlarebedrift' in json_file.name:
                    self._extract_finnlarebedrift_parameters(data, parameter_values)
                elif 'utdanningsdata' in json_file.name or 'stedsvelger' in json_file.name:
                    self._extract_location_parameters(data, parameter_values)
                    
            except Exception as e:
                self.logger.warning(f"Error analyzing {json_file}: {e}")
        
        # Log findings
        for param, values in parameter_values.items():
            if values:
                self.logger.info(f"Found {len(values)} values for parameter '{param}': {list(values)[:10]}")
        
        return parameter_values
    
    def _extract_sammenligning_parameters(self, data: Dict, parameter_values: Dict[str, Set[str]]):
        """
        Extract specific parameter values from sammenligning data structure.
        
        Args:
            data: Sammenligning JSON data
            parameter_values: Dict to update with found values
        """
        def traverse_nested(obj, level=0):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Level-based parameter detection for nested structure
                    if level == 0:  # uno_id level
                        parameter_values['uno_id'].add(key)
                    elif level == 2:  # sektor level (P, S)
                        if key in ['P', 'S']:
                            parameter_values['sektor'].add(key)
                    elif level == 3:  # arbeidstid level (H, F, A)
                        if key in ['H', 'F', 'A']:
                            parameter_values['arbeidstid'].add(key)
                    elif level == 4:  # aldersklasse level
                        if key in ['A', '1', '2', '3', '4', '5']:
                            parameter_values['aldersklasse'].add(key)
                    elif level == 5:  # ansiennitet level
                        if key in ['A', '1', '2', '3', '4', '5']:
                            parameter_values['ansiennitet'].add(key)
                    
                    if isinstance(value, dict):
                        traverse_nested(value, level + 1)
        
        traverse_nested(data)
    
    def _extract_search_parameters(self, data: Dict, parameter_values: Dict[str, Set[str]]):
        """Extract parameter values from search/studievelgeren data."""
        def extract_from_search(obj):
            if isinstance(obj, dict):
                # Extract common search-related fields
                for key, value in obj.items():
                    if key in ['fylke', 'type', 'utdanningsniva', 'studieniva', 'organisasjon']:
                        if isinstance(value, str) and value:
                            parameter_values.get(key, set()).add(value)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str) and item:
                                    parameter_values.get(key, set()).add(item)
                    
                    # Extract titles as potential search queries
                    if key in ['title', 'tittel', 'navn'] and isinstance(value, str):
                        # Extract first few words as potential query terms
                        words = value.lower().split()[:3]
                        for word in words:
                            if len(word) > 3:  # Only meaningful words
                                parameter_values['q'].add(word)
                
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        extract_from_search(value)
                        
            elif isinstance(obj, list):
                for item in obj:
                    extract_from_search(item)
        
        extract_from_search(data)
    
    def _extract_finnlarebedrift_parameters(self, data: Dict, parameter_values: Dict[str, Set[str]]):
        """Extract parameter values from finnlarebedrift data."""
        def extract_from_bedrift(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Extract location and education parameters
                    if key in ['fylke', 'kommune', 'sted', 'fagkode', 'fagomrade', 'naringskode']:
                        if isinstance(value, str) and value:
                            parameter_values.get(key, set()).add(value)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str) and item:
                                    parameter_values.get(key, set()).add(item)
                    
                    # Extract company names as search terms
                    if key in ['navn', 'bedriftsnavn', 'organisasjon'] and isinstance(value, str):
                        # Extract key words from company names
                        words = value.lower().split()
                        for word in words:
                            if len(word) > 2 and word not in ['as', 'asa', 'ab', 'og', 'av']:
                                parameter_values['bedrift'].add(word[:10])  # Limit length
                
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        extract_from_bedrift(value)
                        
            elif isinstance(obj, list):
                for item in obj:
                    extract_from_bedrift(item)
        
        extract_from_bedrift(data)
    
    def _extract_location_parameters(self, data: Dict, parameter_values: Dict[str, Set[str]]):
        """Extract location parameters from geographical data."""
        def extract_from_location(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Extract geographical identifiers
                    if key in ['fylke', 'fylkesnavn', 'kommune', 'kommunenavn', 'region', 'stedsnavn']:
                        if isinstance(value, str) and value:
                            # Map to appropriate parameter
                            if 'fylke' in key:
                                parameter_values['fylke'].add(value)
                            elif 'kommune' in key:
                                parameter_values['kommune'].add(value)
                            elif 'region' in key:
                                parameter_values['region'].add(value)
                            elif 'sted' in key:
                                parameter_values['sted'].add(value)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str) and item:
                                    if 'fylke' in key:
                                        parameter_values['fylke'].add(item)
                                    elif 'kommune' in key:
                                        parameter_values['kommune'].add(item)
                
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        extract_from_location(value)
                        
            elif isinstance(obj, list):
                for item in obj:
                    extract_from_location(item)
        
        extract_from_location(data)
    
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
            elif self._has_query_parameters_that_need_values(url):
                # Handle URLs that need query parameters
                results = await self._handle_urls_with_query_parameters(url, session)
                # Return the first result or a summary
                if results:
                    successful_results = [r for r in results if r.get("success", False)]
                    return {
                        "success": True,
                        "url": url,
                        "total_combinations": len(results),
                        "successful_combinations": len(successful_results),
                        "results": results[:5]  # Show first 5 results as sample
                    }
                else:
                    return {"success": False, "url": url, "reason": "No parameter combinations generated"}
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
    
    async def _handle_urls_with_query_parameters(self, url: str, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """
        Handle URLs that need query parameters by generating combinations.
        
        Args:
            url: Base URL that needs parameters
            session: aiohttp session
            
        Returns:
            List of result dicts
        """
        results = []
        
        # Analyze downloaded data for parameter values
        if not self.parameter_values:
            self.parameter_values = self._analyze_downloaded_data_for_parameters()
        
        # Define parameter combinations based on URL type
        param_combinations = []
        
        if '/sammenligning/lonn' in url:
            # Parameters: arbeidstid, sektor, uno_id, historie (optional)
            required_params = ['arbeidstid', 'sektor', 'uno_id']
            missing_params = []
            
            for param in required_params:
                if not self.parameter_values.get(param):
                    missing_params.append(param)
            
            if missing_params:
                self.logger.warning(f"Missing parameter values for {url}: {missing_params}")
                self.stats["missing_dependencies"] += 1
                return [{"success": False, "url": url, "reason": f"Missing parameters: {missing_params}"}]
            
            # Limit combinations to prevent excessive requests
            arbeidstid_values = list(self.parameter_values['arbeidstid'])[:3]  # Limit to 3
            sektor_values = list(self.parameter_values['sektor'])[:2]  # Limit to 2
            uno_id_values = list(self.parameter_values['uno_id'])[:10]  # Limit to 10
            
            for arbeidstid, sektor, uno_id in product(arbeidstid_values, sektor_values, uno_id_values):
                params = {
                    'arbeidstid': arbeidstid,
                    'sektor': sektor,
                    'uno_id': uno_id,
                    'historie': 'true'
                }
                param_combinations.append(params)
        
        elif '/sammenligning/arbeidsledighet' in url:
            # Similar structure but different parameters might be needed
            uno_id_values = list(self.parameter_values['uno_id'])[:10]
            for uno_id in uno_id_values:
                params = {'uno_id': uno_id}
                param_combinations.append(params)
                
        elif '/sammenligning/arbeidsmarked' in url:
            uno_id_values = list(self.parameter_values['uno_id'])[:10]
            for uno_id in uno_id_values:
                params = {'uno_id': uno_id}
                param_combinations.append(params)
                
        elif '/sammenligning/entrepenorskap' in url:
            uno_id_values = list(self.parameter_values['uno_id'])[:10]
            for uno_id in uno_id_values:
                params = {'uno_id': uno_id}
                param_combinations.append(params)
                
        elif '/sammenligning/suggest' in url:
            # Usually needs a query term
            sample_queries = ['sykepleier', 'ingeniør', 'lærer', 'programmerer', 'kokk']
            for query in sample_queries:
                params = {'q': query}
                param_combinations.append(params)
                
        elif '/search/result' in url:
            # Search endpoint needs query parameters
            sample_queries = ['sykepleier', 'ingeniør', 'utdanning', 'bachelor', 'læreplass']
            for query in sample_queries:
                params = {'q': query, 'type': 'all'}
                param_combinations.append(params)
                
        elif '/search/facet' in url:
            # Facet endpoint typically needs facet type
            facet_types = ['type', 'utdanningsniva', 'fylke', 'studieniva']
            for facet in facet_types:
                params = {'facet': facet}
                param_combinations.append(params)
                
        elif '/finnlarebedrift/result' in url:
            # Needs location or education parameters
            if self.parameter_values.get('fylke'):
                fylke_values = list(self.parameter_values['fylke'])[:5]
                for fylke in fylke_values:
                    params = {'fylke': fylke}
                    param_combinations.append(params)
            # Also try with fagkode if available
            if self.parameter_values.get('fagkode'):
                fagkode_values = list(self.parameter_values['fagkode'])[:5]
                for fagkode in fagkode_values:
                    params = {'fagkode': fagkode}
                    param_combinations.append(params)
                    
        elif '/finnlarebedrift/navnesok' in url:
            # Name search - try some common company terms
            search_terms = ['AS', 'kommune', 'sykehus', 'skole', 'barnehage']
            for term in search_terms:
                params = {'q': term}
                param_combinations.append(params)
                
        elif '/studievelgeren/result' in url:
            # Study selector needs interest or location parameters
            if self.parameter_values.get('fylke'):
                fylke_values = list(self.parameter_values['fylke'])[:5]
                for fylke in fylke_values:
                    params = {'fylke': fylke}
                    param_combinations.append(params)
                    
        elif '/ovttas/result' in url:
            # Adult learning search
            search_terms = ['norsk', 'matematikk', 'engelsk', 'data', 'helse']
            for term in search_terms:
                params = {'q': term}
                param_combinations.append(params)
                
        elif '/ovttas/suggest' in url:
            # Suggestion endpoint
            search_terms = ['nor', 'mat', 'eng', 'dat']
            for term in search_terms:
                params = {'q': term}
                param_combinations.append(params)
                
        elif '/karakterkalkulator/points' in url:
            # Character calculator - try some sample grades
            sample_data = [
                {'subjects': 'NO,MA,EN', 'grades': '4,5,4'},
                {'subjects': 'NO,MA,EN,HI', 'grades': '5,5,4,4'}
            ]
            param_combinations.extend(sample_data)
            
        elif '/onet/onet_by_occupation' in url:
            # ONet occupation lookup
            if self.parameter_values.get('occupation'):
                occupations = list(self.parameter_values['occupation'])[:10]
                for occ in occupations:
                    params = {'occupation': occ}
                    param_combinations.append(params)
                    
        elif '/onet/onet_by_yrke' in url:
            # ONet by job code
            if self.parameter_values.get('uno_id'):
                uno_ids = list(self.parameter_values['uno_id'])[:10]
                for uno_id in uno_ids:
                    params = {'yrke': uno_id}
                    param_combinations.append(params)
        
        # If no specific combinations found, try some generic parameters
        if not param_combinations:
            self.logger.warning(f"No specific parameter combinations defined for {url}, trying generic parameters")
            # Try some common generic parameters
            if 'result' in url or 'search' in url:
                param_combinations.append({'q': 'utdanning'})
                param_combinations.append({'q': 'læreplass'})
            elif 'suggest' in url:
                param_combinations.append({'q': 'syk'})
                param_combinations.append({'q': 'ing'})
        
        # Download each parameter combination
        self.logger.info(f"Generating {len(param_combinations)} parameter combinations for {url}")
        self.stats["parameter_combinations_generated"] += len(param_combinations)
        
        for i, params in enumerate(param_combinations[:50]):  # Limit to 50 combinations
            try:
                # Create URL with parameters
                parsed = urlparse(url)
                query_string = urlencode(params)
                parameterized_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, query_string, parsed.fragment
                ))
                
                await asyncio.sleep(self.rate_limit)  # Rate limiting
                
                data = await self._make_request(parameterized_url, session)
                if data is not None:
                    filename = self._sanitize_filename(url, params)
                    if await self._save_data(data, filename):
                        self.logger.info(f"Downloaded parameterized URL [{i+1}/{len(param_combinations)}]: {parameterized_url}")
                        results.append({
                            "success": True, 
                            "url": parameterized_url, 
                            "filename": filename,
                            "params": params,
                            "data_size": len(str(data))
                        })
                    else:
                        results.append({
                            "success": False, 
                            "url": parameterized_url, 
                            "reason": "Failed to save data",
                            "params": params
                        })
                else:
                    results.append({
                        "success": False, 
                        "url": parameterized_url, 
                        "reason": "Request failed",
                        "params": params
                    })
                    
            except Exception as e:
                self.logger.warning(f"Error processing parameter combination {params}: {e}")
                results.append({
                    "success": False, 
                    "url": url, 
                    "reason": f"Parameter processing error: {e}",
                    "params": params
                })
        
        return results
    
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
        param_urls = [url for url in get_urls if self._is_parameterized_url(url["url"])]
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
                # Separate URLs by type
        simple_urls = [url for url in get_urls if not self._is_parameterized_url(url["url"]) and not self._has_query_parameters_that_need_values(url["url"])]
        query_param_urls = [url for url in get_urls if self._has_query_parameters_that_need_values(url["url"])]
        
        self.logger.info(f"URL Classification:")
        self.logger.info(f"  - Simple URLs: {len(simple_urls)}")
        self.logger.info(f"  - URLs needing query parameters: {len(query_param_urls)}")
        self.logger.info(f"  - Parameterized URLs ({{id}}): {len(param_urls)}")
        
        if query_param_urls:
            self.logger.info(f"URLs requiring query parameters:")
            for url_config in query_param_urls:
                self.logger.info(f"  - {url_config['url']}")
        
        # Download simple URLs first
        results = []
        
        # Phase 1: Simple URLs
        if simple_urls:
            self.logger.info("Phase 1: Downloading simple endpoints...")
            tasks = [
                self._download_endpoint(url_config, self.session, semaphore)
                for url_config in simple_urls
            ]
            simple_results = await atqdm.gather(*tasks, desc="Downloading simple endpoints")
            results.extend(simple_results)
        
        # Phase 2: URLs with query parameters
        if query_param_urls:
            self.logger.info("Phase 2: Downloading endpoints with query parameters...")
            tasks = [
                self._download_endpoint(url_config, self.session, semaphore)
                for url_config in query_param_urls
            ]
            param_results = await atqdm.gather(*tasks, desc="Downloading parameterized endpoints")
            results.extend(param_results)
        
        # Process results
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        
        self.stats["endpoints_processed"] = len(results)
        
        # Calculate total successful combinations
        total_combinations = 0
        for result in successful:
            if result.get("total_combinations"):
                total_combinations += result.get("successful_combinations", 0)
            else:
                total_combinations += 1
        
        summary = {
            "total_endpoints": len(urls),
            "simple_endpoints": len(simple_urls) if 'simple_urls' in locals() else 0,
            "query_param_endpoints": len(query_param_urls) if 'query_param_urls' in locals() else 0,
            "parameterized_endpoints": len(param_urls),
            "successful_downloads": len(successful),
            "failed_downloads": len(failed),
            "total_parameter_combinations": total_combinations,
            "stats": self.stats.copy(),
            "successful_results": successful[:10],  # Limit to first 10 for readability
            "failed_results": failed[:10]  # Limit to first 10 for readability
        }
        
        # Save summary with proper encoding
        await self._save_data(summary, "download_summary")
        
        self.logger.info(f"Download complete: {len(successful)} endpoint groups successful, {total_combinations} total downloads")
        
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