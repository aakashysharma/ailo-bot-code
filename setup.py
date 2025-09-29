#!/usr/bin/env python3
"""
Setup and Validation Script for Norwegian Educational Data Pipeline
Ensures proper encoding and environment setup for Norwegian content.
"""

import sys
import locale
import json
import os
from pathlib import Path


def check_python_encoding():
    """Check if Python is properly configured for UTF-8."""
    print("🔍 Checking Python encoding configuration...")
    
    # Check system encoding
    system_encoding = sys.getdefaultencoding()
    print(f"   System default encoding: {system_encoding}")
    
    # Check locale
    try:
        current_locale = locale.getlocale()
        print(f"   Current locale: {current_locale}")
    except Exception as e:
        print(f"   ⚠️  Locale check failed: {e}")
    
    # Test Norwegian characters
    test_text = "Dette er en test med æøå ÆØÅ karakterer."
    try:
        # Test encoding/decoding
        encoded = test_text.encode('utf-8')
        decoded = encoded.decode('utf-8')
        
        if decoded == test_text:
            print("   ✅ Norwegian character handling: OK")
            return True
        else:
            print("   ❌ Norwegian character handling: FAILED")
            return False
            
    except Exception as e:
        print(f"   ❌ Encoding test failed: {e}")
        return False


def check_dependencies():
    """Check if all required packages are available."""
    print("\n🔍 Checking package dependencies...")
    
    required_packages = [
        'requests', 'aiohttp', 'pandas', 'numpy', 'tqdm', 
        'sentence_transformers', 'sklearn', 'pathlib'
    ]
    
    optional_packages = [
        'openai', 'torch', 'transformers'
    ]
    
    missing_required = []
    missing_optional = []
    
    # Check required packages
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"   ❌ {package} (required)")
    
    # Check optional packages
    for package in optional_packages:
        try:
            __import__(package)
            print(f"   ✅ {package} (optional)")
        except ImportError:
            missing_optional.append(package)
            print(f"   ⚠️  {package} (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("These are needed for advanced LLM integration features.")
    
    return True


def validate_url_list():
    """Validate that the URL list exists and is properly formatted."""
    print("\n🔍 Checking URL list file...")
    
    url_file = Path("url_list.json")
    if not url_file.exists():
        print("   ❌ url_list.json not found")
        return False
    
    try:
        with open(url_file, 'r', encoding='utf-8') as f:
            urls = json.load(f)
        
        if not isinstance(urls, list):
            print("   ❌ URL list should be a JSON array")
            return False
        
        if len(urls) == 0:
            print("   ❌ URL list is empty")
            return False
        
        # Check first few URLs for proper format
        for i, url_config in enumerate(urls[:5]):
            if not isinstance(url_config, dict) or 'url' not in url_config:
                print(f"   ❌ Invalid URL configuration at index {i}")
                return False
        
        print(f"   ✅ URL list valid ({len(urls)} endpoints)")
        return True
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON in url_list.json: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error reading url_list.json: {e}")
        return False


def create_output_directories():
    """Create necessary output directories."""
    print("\n🔧 Creating output directories...")
    
    directories = [
        "utdanning_data",
        "utdanning_data/raw",
        "utdanning_data/processed", 
        "utdanning_data/processed/normalized",
        "utdanning_data/processed/text_for_llm",
        "utdanning_data/processed/metadata",
        "utdanning_data/logs",
        "exports"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {dir_path}")
    
    return True


def test_norwegian_json_handling():
    """Test JSON handling with Norwegian characters."""
    print("\n🔍 Testing Norwegian JSON handling...")
    
    test_data = {
        "navn": "Høgskolen i Østfold",
        "beskrivelse": "Utdanning innen økonomi og administrasjon på høgskolenivå",
        "programområder": ["Bygg- og anleggsteknikk", "Helse- og oppvekstfag"],
        "særlige_noter": "Lærer med æøå og spesialtegn –"
    }
    
    try:
        # Test encoding to JSON
        json_str = json.dumps(test_data, ensure_ascii=False, indent=2)
        
        # Test decoding from JSON  
        decoded_data = json.loads(json_str)
        
        # Verify content is preserved
        if decoded_data == test_data:
            print("   ✅ Norwegian JSON handling: OK")
            
            # Save test file
            test_file = Path("test_norwegian.json")
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            # Read back and verify
            with open(test_file, 'r', encoding='utf-8') as f:
                read_back = json.load(f)
            
            if read_back == test_data:
                print("   ✅ File I/O with Norwegian characters: OK")
                test_file.unlink()  # Clean up
                return True
            else:
                print("   ❌ File I/O failed")
                return False
        else:
            print("   ❌ Data corruption in JSON handling")
            return False
            
    except Exception as e:
        print(f"   ❌ Norwegian JSON test failed: {e}")
        return False


def setup_environment_file():
    """Set up environment configuration file."""
    print("\n🔧 Setting up environment configuration...")
    
    env_template = Path(".env.template")
    env_file = Path(".env")
    
    if env_template.exists() and not env_file.exists():
        print("   📝 Creating .env file from template...")
        print("   ⚠️  Remember to add your API keys to .env file")
        
        # Copy template to .env
        with open(env_template, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        
        print("   ✅ .env file created")
    elif env_file.exists():
        print("   ✅ .env file already exists")
    else:
        print("   ⚠️  No .env.template found")
    
    return True


def main():
    """Run all setup and validation checks."""
    print("🇳🇴 Norwegian Educational Data Pipeline Setup")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Core checks
    checks = [
        ("Python encoding", check_python_encoding),
        ("Dependencies", check_dependencies), 
        ("URL list", validate_url_list),
        ("Norwegian JSON", test_norwegian_json_handling),
        ("Output directories", create_output_directories),
        ("Environment setup", setup_environment_file)
    ]
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_checks_passed = False
        except Exception as e:
            print(f"   ❌ {check_name} check failed with error: {e}")
            all_checks_passed = False
    
    print("\n" + "=" * 60)
    
    if all_checks_passed:
        print("🎉 Setup complete! The pipeline is ready to run.")
        print("\nNext steps:")
        print("1. Add OpenAI API key to .env file (optional)")
        print("2. Run the complete pipeline: python main.py")
        print("3. Or test with: python test_pipeline.py")
        print("4. Try LLM integration: python llm_integration_example.py")
    else:
        print("❌ Some setup checks failed. Please resolve issues above.")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)