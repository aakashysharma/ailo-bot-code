#!/usr/bin/env python3
"""
Systematically test and fix all 422 validation errors.
Tests each problematic URL to find the correct parameter combinations.
"""

import asyncio
import aiohttp
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

async def test_url_with_params(session, base_url, params_to_test):
    """Test a URL with different parameter combinations."""
    results = []
    
    for param_combo in params_to_test:
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        query_params.update(param_combo)
        
        # Flatten lists in query params
        flat_params = {k: v[0] if isinstance(v, list) and len(v) == 1 else v 
                      for k, v in query_params.items()}
        
        new_query = urlencode(flat_params, doseq=True)
        test_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, 
                              parsed.params, new_query, parsed.fragment))
        
        try:
            async with session.get(test_url) as response:
                result = {
                    'url': test_url,
                    'params': param_combo,
                    'status': response.status,
                    'success': response.status == 200
                }
                
                if response.status == 422:
                    error_data = await response.json()
                    result['error'] = error_data
                elif response.status == 200:
                    data = await response.json()
                    result['data_type'] = type(data).__name__
                    if isinstance(data, dict):
                        result['keys'] = list(data.keys())[:5]
                    elif isinstance(data, list):
                        result['count'] = len(data)
                
                results.append(result)
        except Exception as e:
            results.append({
                'url': test_url,
                'params': param_combo,
                'status': 'error',
                'error': str(e),
                'success': False
            })
    
    return results

async def main():
    print("=" * 80)
    print("Testing and Fixing All 422 Validation Errors")
    print("=" * 80)
    
    # Define problematic URLs and parameter combinations to test
    test_cases = [
        {
            'base_url': 'https://api.utdanning.no/ovttas/result?q=norsk',
            'description': 'OVTTAS result endpoint',
            'params_to_test': [
                {'lang': 'nb'},
                {'lang': 'se'},
                {'lang': 'sma'},
                {'lang': 'smj'},
            ]
        },
        {
            'base_url': 'https://api.utdanning.no/ovttas/suggest?q=nor',
            'description': 'OVTTAS suggest endpoint',
            'params_to_test': [
                {'lang': 'nb'},
                {'lang': 'se'},
            ]
        },
        {
            'base_url': 'https://api.utdanning.no/search/facet?facet=type',
            'description': 'Search facet endpoint (wrong facet value)',
            'params_to_test': [
                {'facet': 'hovedfasett'},
                {'facet': 'innholdstype'},
                {'facet': 'omrade'},
                {'facet': 'utdanningsniva'},
                {'facet': 'utdanningsprogram'},
                {'facet': 'interesse'},
                {'facet': 'organisasjon'},
                {'facet': 'fagomrade'},
                {'facet': 'niva'},
            ]
        },
        {
            'base_url': 'https://api.utdanning.no/search/facet?facet=fylke',
            'description': 'Search facet=fylke',
            'params_to_test': [
                {},  # Test as-is first
                {'facet': 'omrade'},
            ]
        },
        {
            'base_url': 'https://api.utdanning.no/search/facet?facet=studieniva',
            'description': 'Search facet=studieniva (wrong)',
            'params_to_test': [
                {'facet': 'niva'},
                {'facet': 'utdanningsniva'},
            ]
        },
    ]
    
    all_fixes = {}
    
    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"\n{'='*80}")
            print(f"Testing: {test_case['description']}")
            print(f"Base URL: {test_case['base_url']}")
            print("-" * 80)
            
            results = await test_url_with_params(
                session, 
                test_case['base_url'],
                test_case['params_to_test']
            )
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            print(f"\nResults: {len(successful)} successful, {len(failed)} failed")
            
            if successful:
                print(f"\n✅ Working combinations:")
                for result in successful:
                    print(f"   • {result['url']}")
                    if 'data_type' in result:
                        print(f"     Type: {result['data_type']}", end='')
                        if 'count' in result:
                            print(f", Count: {result['count']}")
                        elif 'keys' in result:
                            print(f", Keys: {result['keys']}")
                        else:
                            print()
                
                # Store the first working combination
                all_fixes[test_case['base_url']] = successful[0]['url']
            
            if failed:
                print(f"\n❌ Failed combinations:")
                for result in failed[:3]:  # Show first 3 failures
                    print(f"   • Params: {result['params']}")
                    if 'error' in result and isinstance(result['error'], dict):
                        if 'detail' in result['error']:
                            for detail in result['error']['detail'][:1]:
                                print(f"     Error: {detail.get('msg', 'Unknown')}")
                                if 'ctx' in detail and 'expected' in detail['ctx']:
                                    print(f"     Expected: {detail['ctx']['expected']}")
            
            await asyncio.sleep(0.5)  # Be nice to the API
    
    # Save results
    print(f"\n{'='*80}")
    print("Summary of Fixes")
    print("=" * 80)
    
    if all_fixes:
        print(f"\n✅ Found {len(all_fixes)} working URL fixes:\n")
        for old_url, new_url in all_fixes.items():
            print(f"OLD: {old_url}")
            print(f"NEW: {new_url}")
            print()
        
        # Save to JSON
        with open('url_fixes_tested.json', 'w', encoding='utf-8') as f:
            json.dump(all_fixes, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Fixes saved to: url_fixes_tested.json")
    else:
        print("\n❌ No working combinations found")
    
    print("\n📝 Next step: Review the fixes and update url_list.json")

if __name__ == "__main__":
    asyncio.run(main())
