#!/usr/bin/env python3
"""
Fix HTTP 422 Validation Errors in URL List
Based on the actual API validation requirements discovered through testing.
"""

import json
from pathlib import Path

def main():
    print("=" * 80)
    print("Fixing HTTP 422 Validation Errors in URL List")
    print("=" * 80)
    
    # Load current URL list
    url_list_file = Path("url_list.json")
    print(f"\n📖 Reading {url_list_file}...")
    with open(url_list_file, 'r', encoding='utf-8') as f:
        url_list = json.load(f)
    
    original_count = len(url_list)
    print(f"   Original URL count: {original_count}")
    
    # Track changes
    removed_urls = []
    fixed_urls = []
    
    # Fix each problematic endpoint
    print("\n🔧 Applying fixes...")
    
    # 1. ovttas endpoints - all require 'lang' parameter (must be 'nb', 'se', 'sma', or 'smj')
    # prefix must match pattern: ^[01]\|(\d+\|?)?$  (examples: 0|, 1|, 0|123, 1|456|)
    ovttas_fixes = {
        'https://api.utdanning.no/ovttas/emne': {
            'fix': 'https://api.utdanning.no/ovttas/emne?lang=nb&prefix=0|',
            'reason': 'Requires lang=nb (Norwegian Bokmål) and prefix matching pattern ^[01]\\|(\\d+\\|?)?$'
        },
        'https://api.utdanning.no/ovttas/innholdstype': {
            'fix': 'https://api.utdanning.no/ovttas/innholdstype?lang=nb',
            'reason': 'Requires lang=nb (Norwegian Bokmål)'
        },
        'https://api.utdanning.no/ovttas/language': {
            'fix': 'https://api.utdanning.no/ovttas/language?lang=nb',
            'reason': 'Requires lang=nb (Norwegian Bokmål)'
        },
        'https://api.utdanning.no/ovttas/nivaa': {
            'fix': 'https://api.utdanning.no/ovttas/nivaa?lang=nb',
            'reason': 'Requires lang=nb (Norwegian Bokmål)'
        },
        'https://api.utdanning.no/ovttas/tilgjengelighet': {
            'fix': 'https://api.utdanning.no/ovttas/tilgjengelighet?lang=nb',
            'reason': 'Requires lang=nb (Norwegian Bokmål)'
        }
    }
    
    # 2. vov/fagkode_velger - requires 'q' parameter
    # This is a search endpoint, should be removed as it needs user input
    vov_removes = [
        'https://api.utdanning.no/vov/fagkode_velger'
    ]
    
    # 3. sammenligning/yrke base endpoint requires styrk98[] parameter
    # We already have individual yrke URLs with specific IDs, so remove the base one
    sammenligning_removes = [
        'https://api.utdanning.no/sammenligning/yrke'
    ]
    
    # Apply fixes
    new_url_list = []
    
    for url_entry in url_list:
        url = url_entry.get('url', '')
        
        # Check if URL should be removed
        if url in vov_removes + sammenligning_removes:
            removed_urls.append({
                'url': url,
                'reason': 'Requires dynamic user input parameter'
            })
            print(f"   ✗ Removing: {url}")
            continue
        
        # Check if URL needs to be fixed
        if url in ovttas_fixes:
            fix_info = ovttas_fixes[url]
            fixed_urls.append({
                'old': url,
                'new': fix_info['fix'],
                'reason': fix_info['reason']
            })
            new_url_list.append({
                'url': fix_info['fix'],
                'method': url_entry.get('method', 'GET')
            })
            print(f"   ✓ Fixed: {url}")
            print(f"     -> {fix_info['fix']}")
        else:
            # Keep URL as-is
            new_url_list.append(url_entry)
    
    # Save fixed URL list
    output_file = Path("url_list_fixed_422.json")
    print(f"\n💾 Saving fixed URL list to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_url_list, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("✅ URL List Fixed Successfully!")
    print("=" * 80)
    
    print(f"\n📊 Summary:")
    print(f"   Original URLs: {original_count}")
    print(f"   Fixed URLs: {len(fixed_urls)}")
    print(f"   Removed URLs: {len(removed_urls)}")
    print(f"   Final count: {len(new_url_list)}")
    
    if fixed_urls:
        print(f"\n🔧 Fixed URLs ({len(fixed_urls)}):")
        for fix in fixed_urls:
            print(f"   • {fix['old']}")
            print(f"     ✓ {fix['new']}")
            print(f"     Reason: {fix['reason']}")
    
    if removed_urls:
        print(f"\n🗑️  Removed URLs ({len(removed_urls)}):")
        for remove in removed_urls:
            print(f"   • {remove['url']}")
            print(f"     Reason: {remove['reason']}")
    
    # Create detailed report
    report_file = Path("HTTP_422_FIXES.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# HTTP 422 Validation Error Fixes\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Original URLs**: {original_count}\n")
        f.write(f"- **Fixed URLs**: {len(fixed_urls)}\n")
        f.write(f"- **Removed URLs**: {len(removed_urls)}\n")
        f.write(f"- **Final count**: {len(new_url_list)}\n\n")
        
        f.write("## Validation Errors Found\n\n")
        
        f.write("### OVTTAS Endpoints\n\n")
        f.write("**Error**: `Field required: lang`\n\n")
        f.write("All OVTTAS endpoints require a `lang` parameter (e.g., `lang=no` for Norwegian).\n\n")
        f.write("**Fixed URLs**:\n")
        for fix in fixed_urls:
            if 'ovttas' in fix['old']:
                f.write(f"- `{fix['old']}` → `{fix['new']}`\n")
        f.write("\n")
        
        f.write("### VOV Fagkode Velger\n\n")
        f.write("**Error**: `Field required: q`\n\n")
        f.write("This is a search endpoint that requires user input. Removed from automated downloads.\n")
        f.write(f"- ✗ `{vov_removes[0]}`\n\n")
        
        f.write("### Sammenligning Yrke Base\n\n")
        f.write("**Error**: `Field required: styrk98[]`\n\n")
        f.write("The base endpoint requires specific occupation codes. We already have individual URLs")
        f.write(" for each yrke (408 URLs), so the base endpoint is not needed.\n")
        f.write(f"- ✗ `{sammenligning_removes[0]}`\n\n")
        
        f.write("## Next Steps\n\n")
        f.write("1. Review the fixed URL list: `url_list_fixed_422.json`\n")
        f.write("2. Backup current list: `cp url_list.json url_list_backup.json`\n")
        f.write("3. Apply fixes: `mv url_list_fixed_422.json url_list.json`\n")
        f.write("4. Re-run download: `python main.py`\n")
        f.write("\n")
        f.write("All 422 validation errors should now be resolved.\n")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    print("\n📝 Next steps:")
    print("   1. Review: url_list_fixed_422.json")
    print("   2. Backup: cp url_list.json url_list_backup_422.json")
    print("   3. Apply: mv url_list_fixed_422.json url_list.json")
    print("   4. Run: python main.py")
    print()

if __name__ == "__main__":
    main()
