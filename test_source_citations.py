#!/usr/bin/env python3
"""
Test script to verify AILO's source citation and data-only mode
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import ailo_chatbot
sys.path.insert(0, str(Path(__file__).parent))

from ailo_chatbot import AILOChatbot


async def test_source_citations():
    """Test that AILO properly cites sources."""
    
    print("=" * 70)
    print("🧪 AILO Source Citation Test")
    print("=" * 70)
    print()
    
    # Initialize AILO
    print("Initializing AILO...")
    ailo = AILOChatbot()
    
    # Test connection
    print("Testing LM Studio connection...")
    if not await ailo.test_connection():
        print("❌ FAILED: Could not connect to LM Studio")
        print("   Please start LM Studio and try again.")
        return False
    print("✅ PASSED: Connected to LM Studio\n")
    
    # Load knowledge base
    print("Loading knowledge base...")
    ailo.load_knowledge_base()
    
    if not ailo.knowledge_base:
        print("❌ FAILED: No knowledge base loaded")
        print("   Please run: python main.py")
        return False
    print(f"✅ PASSED: Loaded {len(ailo.knowledge_base)} documents\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Career Information with Expected Source",
            "query": "Hva er lønnen for en sykepleier?",
            "should_have_source": True,
            "expected_keywords": ["lønn", "sykepleier", "kr"]
        },
        {
            "name": "Education Information with Expected Source",
            "query": "Hvordan bli lærer?",
            "should_have_source": True,
            "expected_keywords": ["utdanning", "lærer"]
        },
        {
            "name": "Unknown Information (Should Admit Limitation)",
            "query": "Hva er fremtidsutsiktene for astronauter i Norge?",
            "should_have_source": False,
            "expected_keywords": ["ikke", "informasjon", "databasen"]
        }
    ]
    
    print("=" * 70)
    print("Running Test Cases")
    print("=" * 70)
    print()
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print()
        
        # Get response
        response = await ailo.chat(test_case['query'])
        print(f"Response:\n{response}\n")
        
        # Check for source citation
        has_source = "kilde:" in response.lower() or "https://utdanning.no" in response.lower()
        
        # Check for expected keywords
        has_keywords = any(keyword.lower() in response.lower() for keyword in test_case['expected_keywords'])
        
        # Evaluate test
        if test_case['should_have_source']:
            source_test = has_source
            source_message = "✅ PASSED: Source citation found" if source_test else "❌ FAILED: No source citation"
        else:
            source_test = not has_source or ("ikke" in response.lower() and "informasjon" in response.lower())
            source_message = "✅ PASSED: Honest about limitation" if source_test else "❌ FAILED: Should admit limitation"
        
        keyword_test = has_keywords
        keyword_message = "✅ PASSED: Relevant content" if keyword_test else "❌ FAILED: Missing expected keywords"
        
        print(source_message)
        print(keyword_message)
        
        results.append({
            "name": test_case['name'],
            "source_test": source_test,
            "keyword_test": keyword_test,
            "passed": source_test and keyword_test
        })
        
        print("-" * 70)
        print()
    
    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print()
    
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status}: {result['name']}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 All tests passed! AILO is properly citing sources.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the configuration.")
        print("   Check SOURCE_CITATION_GUIDE.md for troubleshooting.")
        return False


async def test_data_only_mode():
    """Test that AILO only uses data from knowledge base."""
    
    print("\n")
    print("=" * 70)
    print("🧪 AILO Data-Only Mode Test")
    print("=" * 70)
    print()
    
    ailo = AILOChatbot()
    ailo.load_knowledge_base()
    
    print("Testing that AILO doesn't use external knowledge...")
    print()
    
    # Ask about something definitely not in Norwegian education data
    test_queries = [
        "Hva er hovedstaden i Frankrike?",  # General knowledge
        "Hvordan lage sjokoladekake?",       # Cooking recipe
        "Hvem vant fotball-VM i 2018?"      # Sports trivia
    ]
    
    all_passed = True
    
    for query in test_queries:
        print(f"Query: {query}")
        response = await ailo.chat(query)
        print(f"Response: {response[:200]}...")
        print()
        
        # Check if AILO admits limitation
        admits_limitation = any(phrase in response.lower() for phrase in [
            "ikke", "informasjon", "databasen", "begrenset", "utdanning.no"
        ])
        
        if admits_limitation:
            print("✅ PASSED: AILO correctly identified lack of relevant data")
        else:
            print("❌ FAILED: AILO should admit it doesn't have this information")
            all_passed = False
        
        print("-" * 70)
        print()
    
    return all_passed


async def main():
    """Run all tests."""
    
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "AILO SOURCE CITATION TEST SUITE" + " " * 18 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Run tests
    test1_passed = await test_source_citations()
    test2_passed = await test_data_only_mode()
    
    # Final summary
    print()
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print()
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("AILO is properly configured to:")
        print("  ✅ Cite sources from utdanning.no")
        print("  ✅ Only use data from knowledge base")
        print("  ✅ Admit limitations when data is missing")
        print()
        print("Your AILO chatbot is ready for production use!")
    else:
        print("⚠️  SOME TESTS FAILED")
        print()
        print("Please review:")
        print("  1. SOURCE_CITATION_GUIDE.md for configuration help")
        print("  2. ailo_config.json for settings")
        print("  3. LM Studio model selection")
        print()
        print("Suggestions:")
        print("  • Lower temperature to 0.3-0.5")
        print("  • Increase max_context_docs to 8-10")
        print("  • Try a different model in LM Studio")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
