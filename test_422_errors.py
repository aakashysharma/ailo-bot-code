#!/usr/bin/env python3
"""
Test specific URLs to capture 422 validation error details.
"""

import asyncio
import aiohttp
import json

async def test_422_urls():
    # Test specific URLs that are showing 422 errors
    test_urls = [
        'https://api.utdanning.no/ovttas/emne',
        'https://api.utdanning.no/ovttas/innholdstype',
        'https://api.utdanning.no/ovttas/language',
        'https://api.utdanning.no/ovttas/nivaa',
        'https://api.utdanning.no/ovttas/tilgjengelighet',
        'https://api.utdanning.no/vov/fagkode_velger',
        'https://api.utdanning.no/sammenligning/yrke',
    ]
    
    print("=" * 80)
    print("Testing URLs for 422 Validation Errors")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        for url in test_urls:
            try:
                async with session.get(url) as response:
                    if response.status == 422:
                        error_data = await response.json()
                        print(f'\n{"="*80}')
                        print(f'URL: {url}')
                        print(f'Status: 422 Validation Error')
                        print(f'\nError Response:')
                        print(json.dumps(error_data, indent=2, ensure_ascii=False))
                        print("=" * 80)
                    else:
                        print(f'\n✓ {url}')
                        print(f'  Status: {response.status}')
            except Exception as e:
                print(f'\n✗ {url}')
                print(f'  Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_422_urls())
