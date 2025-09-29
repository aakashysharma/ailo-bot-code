#!/usr/bin/env python3
"""
Test script for the Utdanning.no API Data Pipeline
Runs basic tests and demonstrates usage.
"""

import asyncio
import json
import sys
from pathlib import Path
import tempfile
import shutil

# Test imports
try:
    from api_downloader import UtdanningAPIDownloader
    from url_processor import URLProcessor
    from data_parser import UtdanningDataParser
    from text_extractor import TextExtractor
    from main import UtdanningDataPipeline
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_basic_functionality():
    """Test basic functionality with a small subset of URLs."""
    print("\n🧪 Testing basic functionality...")
    
    # Create temporary test directory
    test_dir = Path(tempfile.mkdtemp(prefix="utdanning_test_"))
    print(f"Test directory: {test_dir}")
    
    try:
        # Create a minimal URL list for testing
        test_urls = [
            {"url": "https://api.utdanning.no/sammenligning/main", "method": "GET"},
            {"url": "https://api.utdanning.no/personalisering/malgruppe", "method": "GET"},
            {"url": "https://api.utdanning.no/kategorisystemer/nus", "method": "GET"}
        ]
        
        test_url_file = test_dir / "test_urls.json"
        with open(test_url_file, 'w', encoding='utf-8') as f:
            json.dump(test_urls, f, indent=2)
        
        # Initialize pipeline with test configuration
        config = {
            "downloader": {
                "max_concurrent": 2,
                "rate_limit": 0.5,  # Be gentle on the API
                "retry_attempts": 2,
                "timeout": 15
            }
        }
        
        pipeline = UtdanningDataPipeline(
            output_dir=str(test_dir),
            config=config
        )
        
        # Test download phase only (to avoid overwhelming the API)
        print("Testing download phase...")
        download_summary = await pipeline.run_download_phase(str(test_url_file))
        
        # Check results
        raw_files = list((test_dir / "raw").glob("*.json"))
        print(f"Downloaded files: {len(raw_files)}")
        
        if len(raw_files) > 0:
            print("✅ Download test successful")
            
            # Test processing phase
            print("Testing processing phase...")
            process_summary = pipeline.run_processing_phase()
            
            processed_files = list((test_dir / "processed").glob("*.json"))
            print(f"Processed files: {len(processed_files)}")
            
            if len(processed_files) > 0:
                print("✅ Processing test successful")
                
                # Test extraction phase
                print("Testing extraction phase...")
                extract_summary = pipeline.run_extraction_phase()
                
                vector_files = list((test_dir / "processed" / "text_for_llm").glob("*"))
                print(f"Vectorization files: {len(vector_files)}")
                
                if len(vector_files) > 0:
                    print("✅ Extraction test successful")
                    print("🎉 All basic tests passed!")
                    return True
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Cleanup test directory
        try:
            shutil.rmtree(test_dir)
            print(f"🧹 Cleaned up test directory")
        except:
            pass


def test_data_structures():
    """Test data structure processing."""
    print("\n🧪 Testing data structure processing...")
    
    # Test JSON parsing
    sample_data = {
        "hydra:member": [
            {
                "id": "123",
                "title": "Test Education Program", 
                "beskrivelse": "This is a test description of an education program.",
                "metadata": {"type": "program", "level": "bachelor"}
            }
        ],
        "hydra:totalItems": 1
    }
    
    # Test text extraction
    from data_parser import UtdanningDataParser
    
    # Create temporary parser (without files)
    temp_dir = Path(tempfile.mkdtemp())
    try:
        parser = UtdanningDataParser(
            raw_data_dir=str(temp_dir),
            processed_data_dir=str(temp_dir)
        )
        
        # Test text extraction
        text_chunks = parser.extract_text_content(sample_data)
        print(f"Extracted {len(text_chunks)} text chunks")
        
        # Test metadata extraction  
        metadata = parser.extract_metadata(sample_data)
        print(f"Extracted {len(metadata)} metadata fields")
        
        if len(text_chunks) > 0 and len(metadata) > 0:
            print("✅ Data structure processing test successful")
            return True
        else:
            print("❌ Data structure processing test failed")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def test_text_extraction():
    """Test text extraction and enhancement."""
    print("\n🧪 Testing text extraction...")
    
    try:
        from text_extractor import TextExtractor
        
        temp_dir = Path(tempfile.mkdtemp())
        extractor = TextExtractor(str(temp_dir))
        
        # Test text enhancement
        test_text = "Dette er informasjon om utdanning og yrker i Norge."
        test_metadata = {"type": "utdanning", "kategori": "høyere utdanning"}
        
        enhanced = extractor.enhance_text_with_context(
            test_text, test_metadata, "sammenligning/utdanning"
        )
        
        print(f"Original length: {len(test_text)}")
        print(f"Enhanced length: {len(enhanced)}")
        
        # Test keyword extraction
        keywords = extractor._extract_keywords(enhanced)
        print(f"Extracted keywords: {keywords}")
        
        # Test relevance scoring
        relevance = extractor._calculate_educational_relevance(enhanced)
        print(f"Educational relevance: {relevance}")
        
        if len(enhanced) > len(test_text) and relevance > 0:
            print("✅ Text extraction test successful")
            return True
        else:
            print("❌ Text extraction test failed")
            return False
            
    except Exception as e:
        print(f"❌ Text extraction test error: {e}")
        return False
    
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


async def run_all_tests():
    """Run all tests."""
    print("🧪 Starting Utdanning.no API Pipeline Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Data structures
    if test_data_structures():
        tests_passed += 1
    
    # Test 2: Text extraction
    if test_text_extraction():
        tests_passed += 1
    
    # Test 3: Basic functionality (with API calls)
    print(f"\n⚠️  The next test will make actual API calls to utdanning.no")
    print("This may take a few seconds and requires internet connection.")
    
    user_input = input("Continue with API test? (y/N): ").lower().strip()
    if user_input in ['y', 'yes']:
        if await test_basic_functionality():
            tests_passed += 1
    else:
        print("⏭️  Skipping API test")
        total_tests -= 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🏁 Test Summary: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The pipeline is ready to use.")
        print("\nTo run the full pipeline:")
        print("python main.py")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return False
    
    return True


def show_usage_example():
    """Show usage examples."""
    print("\n📖 Usage Examples:")
    print("=" * 30)
    
    examples = [
        ("Complete pipeline", "python main.py"),
        ("Custom output directory", "python main.py --output-dir my_data"),
        ("Download only", "python main.py --download-only"),
        ("Process existing data", "python main.py --process-only"),
        ("Extract from processed data", "python main.py --extract-only"),
        ("Use custom config", "python main.py --config my_config.json"),
    ]
    
    for description, command in examples:
        print(f"  {description}:")
        print(f"    {command}\n")


def main():
    """Main test function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--usage":
        show_usage_example()
        return
    
    try:
        # Run tests
        success = asyncio.run(run_all_tests())
        
        if success:
            show_usage_example()
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")


if __name__ == "__main__":
    main()