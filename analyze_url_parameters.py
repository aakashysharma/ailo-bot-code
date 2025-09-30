#!/usr/bin/env python3
"""
Comprehensive URL Parameter Analysis
Checks all URLs in the list to identify which ones need parameters
"""

import json
import asyncio
from api_downloader import UtdanningAPIDownloader


async def analyze_all_urls():
    """Analyze all URLs to identify parameter requirements."""
    print("🔍 Comprehensive URL Parameter Analysis")
    print("=" * 60)
    
    # Initialize downloader
    downloader = UtdanningAPIDownloader(
        output_dir="utdanning_data",
        max_concurrent=1,
        rate_limit=1.0
    )
    
    # Load URL list
    urls = downloader.load_url_list("url_list.json")
    
    # Categorize URLs
    categories = {
        'simple': [],
        'parameterized': [],
        'query_params_needed': [],
        'uncertain': []
    }
    
    print(f"Analyzing {len(urls)} URLs...\n")
    
    for url_config in urls:
        url = url_config['url']
        method = url_config.get('method', 'GET')
        
        if method != 'GET':
            continue
            
        # Categorize URL
        if downloader._is_parameterized_url(url):
            categories['parameterized'].append(url_config)
        elif downloader._has_query_parameters_that_need_values(url):
            categories['query_params_needed'].append(url_config)
        elif any(pattern in url for pattern in ['/result', '/search', '/navnesok', '/suggest', '/facet']):
            categories['uncertain'].append(url_config)
        else:
            categories['simple'].append(url_config)
    
    # Print results
    print("📊 URL Categorization Results:")
    print(f"  ✅ Simple URLs (no parameters needed): {len(categories['simple'])}")
    print(f"  🔗 Parameterized URLs ({{id}} style): {len(categories['parameterized'])}")
    print(f"  ❓ Query parameter URLs (identified): {len(categories['query_params_needed'])}")
    print(f"  ⚠️  Uncertain URLs (may need parameters): {len(categories['uncertain'])}")
    
    print("\n🔗 Parameterized URLs (need ID extraction):")
    for url_config in categories['parameterized']:
        print(f"  - {url_config['url']}")
    
    print("\n❓ URLs identified as needing query parameters:")
    for url_config in categories['query_params_needed']:
        print(f"  - {url_config['url']}")
    
    print("\n⚠️  Uncertain URLs that might need parameters:")
    for url_config in categories['uncertain']:
        print(f"  - {url_config['url']}")
        
    # Analyze parameter extraction potential
    print("\n🔍 Analyzing parameter extraction from existing data...")
    parameter_values = downloader._analyze_downloaded_data_for_parameters()
    
    print("\n📋 Available parameter values:")
    for param, values in parameter_values.items():
        if values:
            print(f"  {param}: {len(values)} values (e.g., {list(values)[:3]})")
        else:
            print(f"  {param}: No values found")
    
    # Generate recommendations
    print("\n💡 Recommendations:")
    
    if categories['uncertain']:
        print(f"  1. Review {len(categories['uncertain'])} uncertain URLs - they likely need parameters")
        print("     Common patterns that need parameters:")
        patterns = {}
        for url_config in categories['uncertain']:
            url = url_config['url']
            for pattern in ['/result', '/search', '/navnesok', '/suggest', '/facet']:
                if pattern in url:
                    patterns[pattern] = patterns.get(pattern, 0) + 1
        
        for pattern, count in patterns.items():
            print(f"     - {pattern}: {count} URLs")
    
    if not parameter_values.get('fylke'):
        print("  2. Consider downloading location data first to get fylke/kommune parameters")
        
    if not parameter_values.get('q'):
        print("  3. Define sample search queries for search/suggest endpoints")
    
    return categories, parameter_values


async def test_sample_urls():
    """Test a few URLs to see if they actually need parameters."""
    print("\n🧪 Testing sample URLs without parameters...")
    
    downloader = UtdanningAPIDownloader(
        output_dir="test_sample",
        max_concurrent=1,
        rate_limit=2.0
    )
    
    # Test some uncertain URLs without parameters
    test_urls = [
        "https://api.utdanning.no/search/result",
        "https://api.utdanning.no/finnlarebedrift/result", 
        "https://api.utdanning.no/ovttas/result",
        "https://api.utdanning.no/sammenligning/suggest"
    ]
    
    async with downloader:
        for url in test_urls:
            try:
                print(f"  Testing: {url}")
                data = await downloader._make_request(url, downloader.session)
                if data:
                    print(f"    ✅ Returns data: {len(str(data))} characters")
                    # Check if it looks like it needs parameters
                    if isinstance(data, dict):
                        if data.get('hydra:member') == []:
                            print(f"    ⚠️  Empty results - likely needs parameters")
                        elif 'error' in str(data).lower():
                            print(f"    ❌ Error response - definitely needs parameters")
                        else:
                            print(f"    ✅ Valid data returned - parameters optional")
                else:
                    print(f"    ❌ No data returned")
                    
                await asyncio.sleep(1)  # Be gentle with API
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")


async def main():
    """Main analysis function."""
    try:
        # Analyze all URLs
        categories, parameters = await analyze_all_urls()
        
        # Test sample URLs  
        await test_sample_urls()
        
        # Save analysis results
        analysis_results = {
            'url_categories': {k: [url['url'] for url in v] for k, v in categories.items()},
            'parameter_availability': {k: list(v) for k, v in parameters.items()},
            'recommendations': {
                'total_urls_needing_attention': len(categories['query_params_needed']) + len(categories['uncertain']),
                'parameterized_urls': len(categories['parameterized']),
                'simple_urls': len(categories['simple'])
            }
        }
        
        with open('url_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Analysis results saved to 'url_analysis_results.json'")
        print(f"\n🎯 Summary: {analysis_results['recommendations']['total_urls_needing_attention']} URLs need parameter handling")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())