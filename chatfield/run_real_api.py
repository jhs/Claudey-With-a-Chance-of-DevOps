#!/usr/bin/env python3
"""Test real OpenAI API calls with full logging."""

import sys
from chatfield import gather, user, agent, hint, must, reject

@gather
@user("Product Owner")
@user("Not deep technical, but has a clear vision of what they want")
@agent("Technology partner for the Product Owner")
@agent("Needs to understand the request in detail to implement correctly")
class Request:
    """Product Owner's request for technical work"""
    
    @hint("A specific thing you want to build")
    @must("specific enough to implement by a tech team")
    @reject("data regulation environments HIPAA or SOC2")
    def scope():
        "Scope of Work"

    @hint("What assets you have to work with, or what you already built, if any")
    def current_status():
        "Current status of the project"

    @reject("budget details or constraints")
    def constraints():
        "Project constraints, e.g. timeline, resources (excluding budget)"

    @must("specific amount of money")
    @must("a specific time frequency, e.g. monthly, yearly")
    def budget():
        "Project budget"

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