#!/usr/bin/env python3
"""
Quick Evaluation Runner for AILO
Run quick tests with different configurations
"""

import subprocess
import sys
from pathlib import Path


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_evaluation(max_questions=None, description=""):
    """Run evaluation with specified parameters."""
    cmd = [sys.executable, "ailo_evaluation_framework.py"]
    
    if max_questions:
        cmd.extend(["--max-questions", str(max_questions)])
        cmd.append("--sample-categories")
    
    print_header(description)
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    """Run different evaluation modes."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "AILO QUICK EVALUATION RUNNER" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("Choose evaluation mode:")
    print()
    print("  1. Quick Test (10 questions)")
    print("  2. Medium Test (30 questions)")
    print("  3. Comprehensive Test (50 questions)")
    print("  4. Full Test (ALL questions)")
    print("  5. Custom")
    print()
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        run_evaluation(10, "Quick Test - 10 Questions")
    elif choice == "2":
        run_evaluation(30, "Medium Test - 30 Questions")
    elif choice == "3":
        run_evaluation(50, "Comprehensive Test - 50 Questions")
    elif choice == "4":
        run_evaluation(None, "Full Test - All Questions")
    elif choice == "5":
        try:
            num = int(input("Enter number of questions: ").strip())
            run_evaluation(num, f"Custom Test - {num} Questions")
        except ValueError:
            print("❌ Invalid number")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
