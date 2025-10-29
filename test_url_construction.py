#!/usr/bin/env python3
"""
Test URL construction from API endpoints
"""

def construct_url_from_endpoint(endpoint: str) -> str:
    """
    Construct a web URL from an API endpoint.
    Maps API endpoints to appropriate web URLs.
    """
    # Remove 'param/' prefix if present
    endpoint = endpoint.replace('param/', '')
    
    # Map API endpoints to web URLs
    if 'sammenligning' in endpoint:
        # sammenligning/lonn/... -> /sammenligning or specific page
        if '/uno/id-' in endpoint:
            # Extract the ID (e.g., id-y/sykepleier)
            parts = endpoint.split('/uno/id-')
            if len(parts) > 1:
                id_part = parts[1].split('/')[0] + '/' + parts[1].split('/')[1] if '/' in parts[1] else parts[1]
                return f"https://utdanning.no/sammenligning/{id_part}"
        return "https://utdanning.no/sammenligning"
    
    elif 'yrker' in endpoint or 'yrkesvalg' in endpoint:
        # Extract occupation name if present
        if '/beskrivelse/' in endpoint:
            return f"https://utdanning.no/{endpoint}"
        return "https://utdanning.no/yrker"
    
    elif 'utdanning' in endpoint or 'studievelgeren' in endpoint:
        return "https://utdanning.no/utdanning"
    
    elif 'finnlarebedrift' in endpoint or 'lærebedrift' in endpoint:
        return "https://utdanning.no/nb/finn-larebedrift"
    
    elif 'veientilfagbrev' in endpoint:
        return "https://utdanning.no/nb/vei-til-fagbrev"
    
    elif 'arbeidsmarkedskart' in endpoint or 'jobbkompasset' in endpoint:
        return "https://utdanning.no/arbeidsmarked"
    
    elif 'regionalkompetanse' in endpoint:
        return "https://utdanning.no/regionalkompetanse"
    
    elif 'onet' in endpoint:
        return "https://utdanning.no/yrker"
    
    elif 'search' in endpoint or 'søk' in endpoint:
        return "https://utdanning.no/sok"
    
    else:
        # Generic fallback
        clean_endpoint = endpoint.strip('/').replace('//', '/')
        return f"https://utdanning.no/{clean_endpoint}"


# Test cases
test_endpoints = [
    "sammenligning/lonn/arbeidstid-H/historie-true/sektor-A/uno/id-y/gravor",
    "sammenligning/arbeidsmarked/uno/id-y/sykepleier",
    "sammenligning/main",
    "yrker/beskrivelse/laerer",
    "utdanning/beskrivelse/sykepleie",
    "finnlarebedrift/naringskodevelger",
    "veientilfagbrev/veier",
    "arbeidsmarkedskart/endring_arbeidsmarked",
    "onet/yrker",
    "search/result",
    "param/sammenligning/yrke/y/informatiker",
]

print("Testing URL Construction")
print("=" * 80)

for endpoint in test_endpoints:
    url = construct_url_from_endpoint(endpoint)
    print(f"\nEndpoint: {endpoint}")
    print(f"URL:      {url}")

print("\n" + "=" * 80)
