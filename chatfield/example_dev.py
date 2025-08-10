#!/usr/bin/env python3
"""
Example development script for Chatfield.

This demonstrates that the package is properly installed in editable mode
and can be used for development.
"""

import os
from chatfield import Gatherer, must, hint, __version__

print(f"Chatfield v{__version__} - Development Mode")
print("=" * 50)


class QuickDemo(Gatherer):
    """Quick demonstration of Chatfield capabilities"""
    
    @hint("e.g., building a website, fixing a bug, learning Python")
    @must("specific goal or problem")
    def task(): "What are you working on?"
    
    @hint("beginner, intermediate, advanced")
    def experience(): "Your experience level"


def main():
    """Run the demo"""
    # Check if we have an API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  No OPENAI_API_KEY found in environment")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        print()
        print("For development, you can:")
        print("1. Create a .env file in the project root")
        print("2. Add: OPENAI_API_KEY=your-key-here")
        print("3. pip install python-dotenv")
        return
    
    print("Starting conversational data gathering...")
    print("(This would normally start an interactive session)")
    print()
    
    # In a real scenario, this would start the conversation
    # result = QuickDemo.gather()
    # print(f"Task: {result.task}")
    # print(f"Experience: {result.experience}")
    
    print("✅ Development environment is working correctly!")
    print()
    print("Next steps:")
    print("- Run tests: pytest tests/")
    print("- Format code: black chatfield/")
    print("- Check types: mypy chatfield/")
    print("- Or use Make: make dev")


if __name__ == "__main__":
    main()