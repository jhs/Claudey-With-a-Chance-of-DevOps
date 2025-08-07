#!/usr/bin/env python3
"""Test real OpenAI API calls with full logging."""

import sys
from chatfield import gather, user, agent, hint, must, reject

@gather
@user("Vibe Programmer - a person wanting to build a web application via prompting and chat")
@agent("Implementor of the vibe programmer's vision")
@agent("Asks followup or clarifying questions to the vibe programmer to get enough detail to implement correctly")
@agent("Summarizes key details back to the vibe programmer to ensure mutual understanding")
class Request:
    """Vibe programmer's request for technical work"""
    
    @hint("Functional requirements")
    @must("specific enough to implement by a web developer")
    def what():
        "What is the web app you want to build"
    
    def why():
        "What problem does it solve?"
    
    @hint('Could be a brand personality, a visual or color style, or typography')
    @hint('inspirations to draw from')
    def style():
        "Style"

    @hint("Possibly just one user, or a detailed list of several users")
    def users():
        "Who will use the web app? What are their needs and goals?"
    
    def dream():
        "Your vision for the future success of this web app"

if __name__ == "__main__":
    print("\n=== Testing Real OpenAI API with Product Owner Request Model ===\n", file=sys.stderr)
    
    # Create instance and gather data
    request = Request.gather()
    # request.gather_all() # This will be swallowed into the Agent framework probably
    
    # Display results
    print("\n=== Gathered Information ===\n", file=sys.stderr)
    print(f"Scope: {request.scope}", file=sys.stderr)
    print(f"Current Status: {request.current_status}", file=sys.stderr)
    print(f"Constraints: {request.constraints}", file=sys.stderr)
    print(f"Budget: {request.budget}", file=sys.stderr)
    
    print(f"\n=== Test Complete ===\n", file=sys.stderr)