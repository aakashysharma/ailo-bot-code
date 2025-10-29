#!/usr/bin/env python3
"""
Analyze HTTP 422 Validation Errors
Extracts 422 errors from logs, parses error messages, and suggests fixes.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse, parse_qs

def parse_log_file(log_file):
    """Extract all 422 errors from a log file."""
    errors_422 = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '422' in line and 'ERROR' in line:
                errors_422.append(line.strip())
    
    return errors_422

def extract_error_details(log_line):
    """Extract URL, parameters, and error message from log line."""
    details = {
        'url': None,
        'params': {},
        'error_msg': None,
        'validation_errors': []
    }
    
    # Extract URL
    url_match = re.search(r'(https?://[^\s]+)', log_line)
    if url_match:
        details['url'] = url_match.group(1)
        
        # Parse query parameters
        parsed = urlparse(details['url'])
        details['params'] = parse_qs(parsed.query)
    
    # Extract error message (JSON response)
    json_match = re.search(r'\{.*\}', log_line)
    if json_match:
        try:
            error_data = json.loads(json_match.group(0))
            details['error_msg'] = error_data
            
            # Extract validation errors
            if 'detail' in error_data:
                for item in error_data['detail']:
                    if isinstance(item, dict):
                        details['validation_errors'].append({
                            'field': item.get('loc', [])[-1] if item.get('loc') else 'unknown',
                            'message': item.get('msg', ''),
                            'input': item.get('input', ''),
                            'expected': item.get('ctx', {}).get('expected', '')
                        })
        except json.JSONDecodeError:
            pass
    
    return details

def categorize_errors(errors):
    """Group errors by type and field."""
    categorized = defaultdict(list)
    
    for error in errors:
        details = extract_error_details(error)
        
        for val_error in details['validation_errors']:
            field = val_error['field']
            message = val_error['message']
            key = f"{field}: {message}"
            
            categorized[key].append({
                'url': details['url'],
                'input': val_error['input'],
                'expected': val_error['expected'],
                'full_params': details['params']
            })
    
    return categorized

def suggest_fix(field, message, expected, occurrences):
    """Suggest a fix based on the error pattern."""
    fixes = []
    
    # Get unique invalid inputs
    invalid_inputs = set(occ['input'] for occ in occurrences if occ['input'])
    
    if 'should be' in message.lower() and expected:
        fixes.append(f"**Fix**: Use only these values: {expected}")
        fixes.append(f"**Invalid values found**: {', '.join(map(str, invalid_inputs))}")
        
        # If expected is a simple list, provide mapping suggestion
        if expected:
            expected_clean = expected.replace("'", "").replace('"', '')
            fixes.append(f"**Valid options**: {expected_clean}")
    
    elif 'string does not match regex' in message.lower():
        fixes.append(f"**Fix**: Input must match the required pattern")
        fixes.append(f"**Invalid values found**: {', '.join(map(str, invalid_inputs))}")
    
    elif 'extra inputs are not permitted' in message.lower():
        fixes.append(f"**Fix**: Remove the '{field}' parameter from requests")
        fixes.append(f"This parameter is not accepted by the API")
    
    elif 'field required' in message.lower():
        fixes.append(f"**Fix**: The '{field}' parameter is required but missing")
        fixes.append(f"Add this parameter to the URL")
    
    else:
        fixes.append(f"**Fix**: Check API documentation for '{field}' parameter")
    
    return fixes

def main():
    print("=" * 80)
    print("HTTP 422 Validation Error Analysis")
    print("=" * 80)
    
    # Find all log files
    log_dir = Path("utdanning_data/logs")
    if not log_dir.exists():
        print(f"\n❌ Error: {log_dir} not found")
        print("   Run the data download first: python main.py")
        return
    
    log_files = list(log_dir.glob("*.log"))
    print(f"\n📂 Found {len(log_files)} log files")
    
    # Collect all 422 errors
    all_422_errors = []
    for log_file in log_files:
        errors = parse_log_file(log_file)
        all_422_errors.extend(errors)
        if errors:
            print(f"   • {log_file.name}: {len(errors)} 422 errors")
    
    if not all_422_errors:
        print("\n✅ No 422 errors found!")
        return
    
    print(f"\n📊 Total 422 errors found: {len(all_422_errors)}")
    
    # Categorize errors
    print("\n🔍 Analyzing error patterns...")
    categorized = categorize_errors(all_422_errors)
    
    print(f"\n📋 Found {len(categorized)} unique error patterns\n")
    print("=" * 80)
    
    # Generate report
    report_lines = ["# HTTP 422 Validation Errors - Analysis & Fixes\n"]
    report_lines.append(f"**Total Errors**: {len(all_422_errors)}\n")
    report_lines.append(f"**Unique Patterns**: {len(categorized)}\n")
    report_lines.append("\n---\n")
    
    for idx, (error_key, occurrences) in enumerate(sorted(categorized.items()), 1):
        field, message = error_key.rsplit(': ', 1)
        
        print(f"\n## Error Pattern #{idx}")
        print(f"   Field: {field}")
        print(f"   Message: {message}")
        print(f"   Occurrences: {len(occurrences)}")
        
        report_lines.append(f"\n## Error Pattern #{idx}\n")
        report_lines.append(f"**Field**: `{field}`\n")
        report_lines.append(f"**Message**: {message}\n")
        report_lines.append(f"**Occurrences**: {len(occurrences)}\n")
        
        # Get first occurrence details
        first_occ = occurrences[0]
        
        if first_occ['expected']:
            print(f"   Expected: {first_occ['expected']}")
            report_lines.append(f"**Expected**: {first_occ['expected']}\n")
        
        # Show unique invalid inputs
        invalid_inputs = set(str(occ['input']) for occ in occurrences if occ['input'])
        if invalid_inputs:
            print(f"   Invalid inputs: {', '.join(list(invalid_inputs)[:5])}")
            if len(invalid_inputs) > 5:
                print(f"                   ... and {len(invalid_inputs) - 5} more")
            report_lines.append(f"**Invalid Inputs**: {', '.join(list(invalid_inputs)[:10])}\n")
            if len(invalid_inputs) > 10:
                report_lines.append(f"*(... and {len(invalid_inputs) - 10} more)*\n")
        
        # Suggest fix
        fixes = suggest_fix(field, message, first_occ['expected'], occurrences)
        print("\n   Suggested Fixes:")
        report_lines.append(f"\n### Suggested Fixes\n")
        for fix in fixes:
            print(f"   • {fix}")
            report_lines.append(f"- {fix}\n")
        
        # Show example URLs
        unique_urls = list(set(occ['url'] for occ in occurrences if occ['url']))[:3]
        if unique_urls:
            print("\n   Example URLs:")
            report_lines.append(f"\n### Example URLs\n")
            for url in unique_urls:
                print(f"   • {url}")
                report_lines.append(f"- `{url}`\n")
        
        print("-" * 80)
        report_lines.append("\n---\n")
    
    # Save report
    report_file = Path("HTTP_422_ERRORS_ANALYSIS.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.writelines(report_lines)
    
    print("\n" + "=" * 80)
    print(f"✅ Analysis complete! Report saved to: {report_file}")
    print("=" * 80)
    
    # Summary of most common errors
    print("\n📊 Top 5 Most Common Errors:\n")
    sorted_errors = sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True)
    for idx, (error_key, occurrences) in enumerate(sorted_errors[:5], 1):
        field, message = error_key.rsplit(': ', 1)
        print(f"   {idx}. {field}: {len(occurrences)} occurrences")
        print(f"      Message: {message[:60]}...")
    
    print("\n💡 Next Steps:")
    print("   1. Review the report: HTTP_422_ERRORS_ANALYSIS.md")
    print("   2. Update url_list.json to fix parameter values")
    print("   3. Re-run: python main.py")
    print()

if __name__ == "__main__":
    main()
