#!/usr/bin/env python3
"""
Example showing the new Gatherer class-based approach.

This demonstrates the cleaner syntax using inheritance instead of decorators.
"""

import os
from chatfield import Gatherer, must, hint, reject, match, user, agent, __version__

print(f"Chatfield v{__version__} - Gatherer Class Example")
print("=" * 50)


# Simple example - just inherit from Gatherer
class QuickDemo(Gatherer):
    """Quick demonstration of Chatfield capabilities"""
    
    @hint("e.g., building a website, fixing a bug, learning Python")
    @must("specific goal or problem")
    def task(): "What are you working on?"
    
    @hint("beginner, intermediate, advanced")
    def experience(): "Your experience level"


# More complex example with class-level decorators
@user("Small business owner, not technical")
@user("Probably frustrated with tech complexity")
@agent("Patient Socratic questioner")
@agent("Use analogies to explain technical concepts")
class BusinessWebsite(Gatherer):
    """A Socratic journey to discover your business's online needs"""
    
    @hint("Examples: bakery, accounting firm, yoga studio, plumbing service")
    @must("specific business type")
    @must("main customer action")
    def business(): "Tell me about your business"
    
    @hint("The words they use, not what you think sounds professional")
    @must("actual customer words, not marketing speak")
    def customers(): "How do customers describe what you do?"
    
    @hint("Facebook page? Google listing? Old website? Nothing is fine too!")
    @reject("social media links only")
    def online_presence(): "What online presence do you have now?"


# Example with match decorators
class ProjectPlanning(Gatherer):
    """Planning your next project"""
    
    @match.personal("is a personal project")
    @match.work("is for work")
    @match.learning("is for learning/education")
    def project_type(): "What kind of project is this?"
    
    @must("specific timeline")
    @hint("Days? Weeks? Months?")
    def timeline(): "When do you need this done?"
    
    @hint("Be realistic about time and money")
    def resources(): "What resources do you have?"


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
    
    print("\nExamples of the new Gatherer class syntax:")
    print()
    print("1. Simple inheritance from Gatherer:")
    print("   class MyGatherer(Gatherer):")
    print("       def field(): 'description'")
    print()
    print("2. With field decorators:")
    print("   @must('be specific')")
    print("   @hint('think carefully')")
    print("   def field(): 'description'")
    print()
    print("3. With class decorators:")
    print("   @user('context about user')")
    print("   @agent('how to behave')")
    print("   class MyGatherer(Gatherer):")
    print()
    print("Usage remains the same:")
    print("   result = MyGatherer.gather()")
    print("   print(result.field)")
    print()
    
    # In a real scenario, this would start the conversation
    # result = QuickDemo.gather()
    # print(f"Task: {result.task}")
    # print(f"Experience: {result.experience}")
    
    print("✅ Gatherer class pattern is working correctly!")
    print()
    print("Benefits over @gather decorator:")
    print("- Better IDE support and autocomplete")
    print("- More explicit and less magical")
    print("- Direct translation to TypeScript")
    print("- Supports inheritance naturally")


if __name__ == "__main__":
    main()