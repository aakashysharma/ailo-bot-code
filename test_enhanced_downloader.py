#!/usr/bin/env python3
"""
Test script for the enhanced API downloader functionality
Tests parameter extraction and query parameter support
"""

import asyncio
import sys
import json
from api_downloader import UtdanningAPIDownloader


async def test_parameter_extraction():
    """Test parameter extraction from existing data."""
    print("Testing parameter extraction...")
    
    downloader = UtdanningAPIDownloader(
        output_dir="utdanning_data",
        max_concurrent=2,
        rate_limit=0.5
    )
    
    # Test parameter analysis
    parameter_values = downloader._analyze_downloaded_data_for_parameters()
    
    print("\nExtracted parameter values:")
    for param, values in parameter_values.items():
        if values:
            print(f"  {param}: {len(values)} values - {list(values)[:5]}...")
        else:
            print(f"  {param}: No values found")
    
    # Test query parameter detection
    test_urls = [
        "https://api.utdanning.no/sammenligning/lonn",
        "https://api.utdanning.no/sammenligning/arbeidsledighet", 
        "https://api.utdanning.no/sammenligning/main",
        "https://api.utdanning.no/jobbkompasset/yrker"
    ]
    
    print("\nQuery parameter detection:")
    for url in test_urls:
        needs_params = downloader._has_query_parameters_that_need_values(url)
        print(f"  {url}: {'Needs parameters' if needs_params else 'Simple URL'}")
    
    return parameter_values


async def test_small_download():
    """Test downloading with a small subset of URLs."""
    print("\nTesting small download with query parameters...")
    
    # Create a minimal test URL list
    test_urls = [
        {"url": "https://api.utdanning.no/sammenligning/main", "method": "GET"},
        {"url": "https://api.utdanning.no/sammenligning/lonn", "method": "GET"}
    ]
    
    # Save test URL list
    with open("test_urls.json", "w", encoding="utf-8") as f:
        json.dump(test_urls, f, indent=2)
    
    downloader = UtdanningAPIDownloader(
        output_dir="test_download",
        max_concurrent=2,
        rate_limit=1.0
    )
    
    async with downloader:
        summary = await downloader.download_all_endpoints("test_urls.json")
        
        print(f"\nDownload Summary:")
        print(f"  Total endpoints: {summary.get('total_endpoints', 0)}")
        print(f"  Simple endpoints: {summary.get('simple_endpoints', 0)}")
        print(f"  Query param endpoints: {summary.get('query_param_endpoints', 0)}")
        print(f"  Successful downloads: {summary.get('successful_downloads', 0)}")
        print(f"  Failed downloads: {summary.get('failed_downloads', 0)}")
        print(f"  Total parameter combinations: {summary.get('total_parameter_combinations', 0)}")
        
        # Show some successful results
        if summary.get('successful_results'):
            print(f"\nFirst few successful results:")
            for i, result in enumerate(summary['successful_results'][:3]):
                print(f"  {i+1}. {result.get('url', 'N/A')}")
                if result.get('total_combinations'):
                    print(f"     - Generated {result['total_combinations']} combinations")
                    print(f"     - {result.get('successful_combinations', 0)} successful")


async def main():
    """Main test function."""
    print("🧪 Testing Enhanced UtdanningAPIDownloader")
    print("=" * 50)
    
    try:
        # Test 1: Parameter extraction
        await test_parameter_extraction()
        
        # Test 2: Small download test
        await test_small_download()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())