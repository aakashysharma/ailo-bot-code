#!/usr/bin/env python3
"""
AILO Quick Start Script
One command to rule them all
"""

import asyncio
import sys
import subprocess
from pathlib import Path


async def main():
    """Quick start AILO system."""
    print("=" * 60)
    print("🤖 AILO - Quick Start")
    print("=" * 60)
    print()
    
    # Check if data exists
    data_dir = Path("utdanning_data/processed/text_for_llm/vectorization_dataset.json")
    
    if not data_dir.exists():
        print("📥 No data found. Running data pipeline first...")
        print("This will take a few minutes...\n")
        
        result = subprocess.run([sys.executable, "main.py"], capture_output=False)
        
        if result.returncode != 0:
            print("\n❌ Data pipeline failed. Please check the logs.")
            sys.exit(1)
        
        print("\n✅ Data pipeline completed!\n")
    else:
        print("✅ Data already exists\n")
    
    # Check LM Studio
    print("🔍 Checking LM Studio connection...")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:1234/v1/models", timeout=5) as response:
                if response.status == 200:
                    print("✅ LM Studio is running\n")
                else:
                    print("⚠️  LM Studio responded but with unexpected status\n")
    except:
        print("❌ Cannot connect to LM Studio!")
        print("   Please:")
        print("   1. Open LM Studio")
        print("   2. Load model: gemma-3n-E4B-it-MLX-bf16")
        print("   3. Start Local Server")
        print("   4. Try again\n")
        sys.exit(1)
    
    # Start chatbot
    print("🚀 Starting AILO chatbot...\n")
    subprocess.run([sys.executable, "ailo_chatbot.py"])


if __name__ == "__main__":
    asyncio.run(main())
