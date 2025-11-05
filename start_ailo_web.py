#!/usr/bin/env python3
"""
AILO Web Interface Launcher
Simple script to start the Flask web server for AILO chatbot.
"""

import os
import sys
from pathlib import Path

def main():
    """Launch the AILO web interface."""
    
    # Add current directory to path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Import and run the web app
    try:
        from ailo_web import app
        
        print("=" * 70)
        print("🔮 AILO - AI-powered Learning Oracle")
        print("=" * 70)
        print("\n🚀 Starting web server...\n")
        print("📍 Open your browser and navigate to:")
        print("   → http://localhost:8080")
        print("   → http://127.0.0.1:8080")
        print("\n⏱️  Please wait while AILO loads the knowledge base...")
        print("   (This may take 1-2 minutes on first startup)\n")
        print("Press Ctrl+C to stop the server\n")
        print("=" * 70)
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down AILO web server...")
        print("Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error starting AILO: {e}")
        print("\nPlease check:")
        print("  1. All dependencies are installed (requirements.txt)")
        print("  2. LM Studio is running with the Gemma model")
        print("  3. Port 8080 is not already in use")
        sys.exit(1)

if __name__ == "__main__":
    main()
