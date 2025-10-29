#!/usr/bin/env python3
"""
Script to analyze 404 errors and provide solutions for better parameter extraction.
This will help us understand which endpoints are failing and why.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Any


class URLErrorAnalyzer:
    """Analyze HTTP 404 errors and suggest solutions."""
    
    def __init__(self, log_dir: str = "utdanning_data/logs"):
        self.log_dir = Path(log_dir)
        self.raw_data_dir = Path("utdanning_data/raw")
        self.errors = defaultdict(list)
        self.successful_urls = set()
        
    def analyze_logs(self):
        """Parse log files to extract error patterns."""
        print("Analyzing log files for HTTP errors...")
        
        for log_file in self.log_dir.glob("downloader_*.log"):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if "HTTP 404" in line:
                        # Extract URL from log line
                        match = re.search(r'https://api\.utdanning\.no/([^\s]+)', line)
                        if match:
                            url_path = match.group(1)
                            self.errors['404'].append(url_path)
                    elif "Successfully downloaded" in line or "HTTP 200" in line:
                        match = re.search(r'https://api\.utdanning\.no/([^\s]+)', line)
                        if match:
                            self.successful_urls.add(match.group(1))
        
        print(f"Found {len(self.errors['404'])} 404 errors")
        print(f"Found {len(self.successful_urls)} successful downloads")
        
    def categorize_errors(self) -> Dict[str, List[str]]:
        """Categorize errors by endpoint pattern."""
        categorized = defaultdict(list)
        
        for url in self.errors['404']:
            # Extract base endpoint
            if 'finnlarebedrift/bedrift/' in url:
                categorized['finnlarebedrift_bedrift'].append(url)
            elif '/bedrift/' in url:
                categorized['bedrift_param'].append(url)
            elif '?' in url:
                # Query parameter URLs
                base = url.split('?')[0]
                categorized[f'query_{base}'].append(url)
            else:
                # Simple endpoint failures
                categorized[url].append(url)
        
        return categorized
    
    def extract_valid_ids_from_data(self) -> Dict[str, Set[str]]:
        """Extract valid IDs from successfully downloaded data."""
        valid_ids = {
            'bedrift_ids': set(),
            'uno_ids': set(),
            'nus_kodes': set(),
            'styrk08_kodes': set(),
            'programomrade_kodes': set(),
            'vilbli_org_ids': set(),
            'yrke_ids': set()
        }
        
        print("\nExtracting valid IDs from downloaded data...")
        
        # Check bedrifter data
        bedrifter_files = [
            'finnlarebedrift_bedrifter_alle.json',
            'finnlarebedrift_bedrifter_godkjente.json',
            'finnlarebedrift_bedrifter_m_lareplass.json'
        ]
        
        for filename in bedrifter_files:
            file_path = self.raw_data_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'hydra:member' in data:
                            for item in data['hydra:member']:
                                if 'org_id' in item:
                                    valid_ids['bedrift_ids'].add(str(item['org_id']))
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and 'org_id' in item:
                                    valid_ids['bedrift_ids'].add(str(item['org_id']))
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        # Check sammenligning data for uno_ids
        sammenligning_files = ['sammenligning_yrke.json', 'sammenligning_main.json']
        for filename in sammenligning_files:
            file_path = self.raw_data_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self._extract_uno_ids(data, valid_ids['uno_ids'])
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        # Check kategorisystemer data
        for filename in ['kategorisystemer_nus.json', 'kategorisystemer_styrk08.json']:
            file_path = self.raw_data_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'nus' in filename:
                            self._extract_codes(data, valid_ids['nus_kodes'], 'nus_kode')
                        elif 'styrk08' in filename:
                            self._extract_codes(data, valid_ids['styrk08_kodes'], 'yrkeskode_styrk08')
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        # Check vgs data
        vgs_files = ['vgs_programomrade_info.json', 'linje_programomrade.json']
        for filename in vgs_files:
            file_path = self.raw_data_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self._extract_codes(data, valid_ids['programomrade_kodes'], 'programomradekode10')
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        # Print summary
        print("\nValid IDs found:")
        for id_type, ids in valid_ids.items():
            print(f"  {id_type}: {len(ids)} IDs")
            if ids and len(ids) <= 10:
                print(f"    Sample: {list(ids)[:5]}")
        
        return valid_ids
    
    def _extract_uno_ids(self, data: Any, uno_ids: Set[str]):
        """Recursively extract uno_id values."""
        if isinstance(data, dict):
            if 'uno_id' in data and data['uno_id']:
                uno_ids.add(str(data['uno_id']))
            for value in data.values():
                self._extract_uno_ids(value, uno_ids)
        elif isinstance(data, list):
            for item in data:
                self._extract_uno_ids(item, uno_ids)
    
    def _extract_codes(self, data: Any, code_set: Set[str], key_name: str):
        """Recursively extract codes from data."""
        if isinstance(data, dict):
            if key_name in data and data[key_name]:
                code_set.add(str(data[key_name]))
            for value in data.values():
                self._extract_codes(value, code_set, key_name)
        elif isinstance(data, list):
            for item in data:
                self._extract_codes(item, code_set, key_name)
    
    def generate_recommendations(self):
        """Generate recommendations for fixing 404 errors."""
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS FOR FIXING 404 ERRORS")
        print("=" * 80)
        
        categorized = self.categorize_errors()
        valid_ids = self.extract_valid_ids_from_data()
        
        # Analyze finnlarebedrift/bedrift errors
        bedrift_errors = categorized.get('finnlarebedrift_bedrift', [])
        if bedrift_errors:
            print(f"\n1. finnlarebedrift/bedrift endpoint ({len(bedrift_errors)} errors)")
            print("   Problem: Using invalid org_id values")
            print(f"   Solution: Use only the {len(valid_ids['bedrift_ids'])} valid org_ids from bedrifter_alle")
            
            # Show what IDs were tried vs what's valid
            tried_ids = set()
            for url in bedrift_errors[:10]:
                match = re.search(r'/bedrift/([^/?]+)', url)
                if match:
                    tried_ids.add(match.group(1))
            
            print(f"   Example invalid IDs tried: {list(tried_ids)[:5]}")
            if valid_ids['bedrift_ids']:
                print(f"   Example valid IDs available: {list(valid_ids['bedrift_ids'])[:5]}")
        
        # Analyze query parameter errors
        query_errors = {k: v for k, v in categorized.items() if k.startswith('query_')}
        if query_errors:
            print(f"\n2. Query parameter endpoints ({sum(len(v) for v in query_errors.values())} errors)")
            for endpoint, urls in query_errors.items():
                endpoint_name = endpoint.replace('query_', '')
                print(f"\n   Endpoint: {endpoint_name}")
                print(f"   Errors: {len(urls)}")
                
                # Analyze what parameters were used
                params_used = set()
                for url in urls[:5]:
                    if '?' in url:
                        params_used.add(url.split('?')[1])
                
                if params_used:
                    print(f"   Example failed params: {list(params_used)[:3]}")
                
                print("   Solution: These endpoints may require specific query combinations")
                print("             or may not support all parameter values")
        
        # Endpoints that consistently fail
        simple_failures = [k for k, v in categorized.items() 
                          if not k.startswith('query_') and k != 'finnlarebedrift_bedrift']
        if simple_failures:
            print(f"\n3. Endpoints that consistently fail ({len(simple_failures)} endpoints)")
            for endpoint in simple_failures[:10]:
                print(f"   - {endpoint}")
            print("   Solution: These endpoints may be deprecated or require authentication")
            print("             Consider excluding them from url_list.json")
        
        return valid_ids
    
    def create_improved_url_list(self, valid_ids: Dict[str, Set[str]], output_file: str = "url_list_improved.json"):
        """Create an improved URL list with only valid parameters."""
        print(f"\n\nCreating improved URL list: {output_file}")
        
        # Load original URL list
        with open('url_list.json', 'r') as f:
            original_urls = json.load(f)
        
        improved_urls = []
        
        # Endpoints to exclude (consistently fail)
        exclude_patterns = [
            'search_logs',  # Requires authentication
            'personalisering/malgruppe',  # May be deprecated
            'yrkearbeidsliv/potensielle-larebedrifter',  # May require special params
            'regionalkompetanse/arbeidsstyrker/',  # Consistently fails
        ]
        
        for url_entry in original_urls:
            url = url_entry['url']
            
            # Skip excluded endpoints
            if any(pattern in url for pattern in exclude_patterns):
                print(f"  Excluding: {url}")
                continue
            
            # Handle parameterized endpoints
            if '{id}' in url and 'finnlarebedrift/bedrift' in url:
                # Replace with valid org_ids only
                if valid_ids['bedrift_ids']:
                    print(f"  Replacing {url} with {len(valid_ids['bedrift_ids'])} valid IDs")
                    for org_id in list(valid_ids['bedrift_ids'])[:50]:  # Limit to first 50
                        improved_urls.append({
                            "url": url.replace('{id}', str(org_id)),
                            "method": url_entry['method']
                        })
                else:
                    # If we don't have valid IDs, skip the parameterized version
                    print(f"  Skipping {url} - no valid IDs found")
                continue
            
            elif '{uno_id}' in url:
                if valid_ids['uno_ids']:
                    print(f"  Replacing {url} with {len(valid_ids['uno_ids'])} valid uno_ids")
                    for uno_id in list(valid_ids['uno_ids'])[:100]:
                        improved_urls.append({
                            "url": url.replace('{uno_id}', str(uno_id)),
                            "method": url_entry['method']
                        })
                else:
                    print(f"  Skipping {url} - no valid uno_ids found")
                continue
            
            elif '{nus_kode}' in url:
                if valid_ids['nus_kodes']:
                    for code in list(valid_ids['nus_kodes'])[:100]:
                        improved_urls.append({
                            "url": url.replace('{nus_kode}', str(code)),
                            "method": url_entry['method']
                        })
                continue
            
            elif '{yrkeskode_styrk08}' in url:
                if valid_ids['styrk08_kodes']:
                    for code in list(valid_ids['styrk08_kodes'])[:100]:
                        improved_urls.append({
                            "url": url.replace('{yrkeskode_styrk08}', str(code)),
                            "method": url_entry['method']
                        })
                continue
            
            elif '{programomradekode10}' in url:
                if valid_ids['programomrade_kodes']:
                    for code in list(valid_ids['programomrade_kodes'])[:100]:
                        improved_urls.append({
                            "url": url.replace('{programomradekode10}', str(code)),
                            "method": url_entry['method']
                        })
                continue
            
            # Keep non-parameterized URLs
            improved_urls.append(url_entry)
        
        # Save improved URL list
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(improved_urls, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Created {output_file} with {len(improved_urls)} URLs")
        print(f"  Original: {len(original_urls)} URLs")
        print(f"  Improved: {len(improved_urls)} URLs")


def main():
    """Main analysis function."""
    analyzer = URLErrorAnalyzer()
    
    print("=" * 80)
    print("URL ERROR ANALYSIS AND SOLUTION GENERATOR")
    print("=" * 80)
    
    # Step 1: Analyze logs
    analyzer.analyze_logs()
    
    # Step 2: Generate recommendations
    valid_ids = analyzer.generate_recommendations()
    
    # Step 3: Create improved URL list
    analyzer.create_improved_url_list(valid_ids)
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Review url_list_improved.json")
    print("2. Backup your current url_list.json:")
    print("   cp url_list.json url_list_backup.json")
    print("3. Replace with improved version:")
    print("   cp url_list_improved.json url_list.json")
    print("4. Run the pipeline again:")
    print("   python main.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
