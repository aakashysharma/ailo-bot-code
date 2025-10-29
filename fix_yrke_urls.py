#!/usr/bin/env python3
"""
Fix URLs for sammenligning/yrke endpoints.
Extracts valid y_ and u_ IDs from sammenligning_main.json and creates proper URLs.
"""

import json
from pathlib import Path

def main():
    print("=" * 80)
    print("Fixing sammenligning/yrke URL patterns")
    print("=" * 80)
    
    # Read sammenligning_main.json to get valid IDs
    sammenligning_file = Path("utdanning_data/raw/sammenligning_main.json")
    
    if not sammenligning_file.exists():
        print(f"❌ Error: {sammenligning_file} not found")
        print("   Run the data download first: python main.py")
        return
    
    print(f"\n📖 Reading {sammenligning_file}...")
    with open(sammenligning_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract valid y_ and u_ IDs
    y_ids = sorted([key for key in data.keys() if key.startswith('y_')])
    u_ids = sorted([key for key in data.keys() if key.startswith('u_')])
    
    print(f"\n✓ Found {len(y_ids)} yrke IDs (y_*)")
    print(f"✓ Found {len(u_ids)} utdanning IDs (u_*)")
    
    # Read current url_list.json
    url_list_file = Path("url_list.json")
    print(f"\n📖 Reading {url_list_file}...")
    with open(url_list_file, 'r', encoding='utf-8') as f:
        url_list = json.load(f)
    
    # Find and remove old sammenligning/yrke URLs
    print("\n🗑️  Removing old sammenligning/yrke URLs...")
    original_count = len(url_list)
    url_list = [
        url_entry for url_entry in url_list 
        if 'sammenligning/yrke' not in url_entry.get('url', '')
        or url_entry.get('url') == 'https://api.utdanning.no/sammenligning/yrke2utdanning'
    ]
    removed = original_count - len(url_list)
    print(f"   Removed {removed} old URLs")
    
    # Add base sammenligning/yrke URL (no parameters)
    print("\n➕ Adding base URL...")
    url_list.append({
        "url": "https://api.utdanning.no/sammenligning/yrke",
        "method": "GET"
    })
    
    # Add URLs for each valid y_ ID
    print(f"\n➕ Adding {len(y_ids)} URLs for yrke IDs...")
    for y_id in y_ids:
        url_list.append({
            "url": f"https://api.utdanning.no/sammenligning/yrke/{y_id}",
            "method": "GET"
        })
    
    # Add URLs for each valid u_ ID
    print(f"➕ Adding {len(u_ids)} URLs for utdanning comparison...")
    for u_id in u_ids:
        url_list.append({
            "url": f"https://api.utdanning.no/sammenligning/utdanning/{u_id}",
            "method": "GET"
        })
    
    # Keep yrke2utdanning URL (it's already in the list)
    
    # Save updated url_list.json
    output_file = Path("url_list_fixed_yrke.json")
    print(f"\n💾 Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(url_list, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("✅ URL list fixed successfully!")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  • Total URLs: {len(url_list)}")
    print(f"  • Yrke base: 1")
    print(f"  • Yrke with y_ IDs: {len(y_ids)}")
    print(f"  • Utdanning with u_ IDs: {len(u_ids)}")
    print(f"  • Other URLs: {len(url_list) - 1 - len(y_ids) - len(u_ids)}")
    print(f"\n📝 Next steps:")
    print(f"  1. Review: {output_file}")
    print(f"  2. Backup: cp url_list.json url_list_backup.json")
    print(f"  3. Replace: mv {output_file} url_list.json")
    print(f"  4. Re-run: python main.py")
    print()
    
    # Show some examples
    print("📋 Example URLs created:")
    print(f"  • https://api.utdanning.no/sammenligning/yrke")
    print(f"  • https://api.utdanning.no/sammenligning/yrke/{y_ids[0]}")
    print(f"  • https://api.utdanning.no/sammenligning/yrke/{y_ids[1]}")
    print(f"  • https://api.utdanning.no/sammenligning/utdanning/{u_ids[0]}")
    print(f"  • https://api.utdanning.no/sammenligning/utdanning/{u_ids[1]}")
    print()

if __name__ == "__main__":
    main()
