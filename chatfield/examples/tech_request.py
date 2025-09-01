#!/usr/bin/env python3
"""
Tech Work Request Example
=========================

This example demonstrates:
- Product Owner and Technology Consultant roles
- Multiple validation rules (@must, @reject, @hint)
- Integer transformations for numeric fields
- Real-world business conversation flow

Run with:
    python examples/tech_request.py

For automated demo:
    python examples/tech_request.py --auto
"""

import os
import sys
import argparse
from pathlib import Path
import dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatfield import chatfield
from chatfield import Interviewer
from chatfield import alice, bob, must, reject, hint
from chatfield import as_int, as_bool


def create_tech_request():
    """Create a tech work request interview."""
    return (chatfield()
        .type("TechWorkRequest")
        .desc("Product Owner's request for technical work")
        
        .alice()
            .type("Expert Technology Consultant")
            .trait("Technology partner for the Product Owner")
            .trait("Needs to understand the request in detail to implement correctly")
            .trait("Keeps things simple and focused without overwhelming the Product Owner")
        
        .bob()
            .type("Product Owner")
            .trait("Not deeply technical, but has a clear vision of what they want")
        
        .field("project_name")
            .desc("What should we call this project?")
            .hint("A short, memorable name for the project")
        
        .field("scope")
            .desc("What would you like to build?")
            .hint("A specific thing you want to build")
            .must("specific enough to implement by a tech team")
            .reject("anything requiring HIPAA or SOC2 compliance")
        
        .field("current_status")
            .desc("What's the current state of this project?")
            .hint("What assets you have to work with, or what you already built, if any")
        
        .field("target_users")
            .desc("Who will use this?")
            .must("specific user groups or roles")
        
        .field("number_of_users")
            .desc("How many users do you expect?")
            .hint("Rough estimate is fine")
            .as_int()
        
        .field("timeline")
            .desc("When do you need this completed?")
            .must("specific timeframe or deadline")
            .reject("ASAP or urgent without specific dates")
        
        .field("budget")
            .desc("What's your budget for this project?")
            .must("specific amount of money")
            .must("a specific time frequency, e.g. monthly, yearly")
            .as_int("USD amount, or -1 if unlimited")
        
        .field("success_metrics")
            .desc("How will we know if this is successful?")
            .hint("Measurable outcomes or KPIs")
        
        .field("enthusiasm")
            .desc("What's your enthusiasm level for this project?")
            .as_bool("True if highly enthusiastic")
        
        .build())


def run_interactive(request):
    """Run the interview interactively."""
    thread_id = f"tech-request-{os.getpid()}"
    print(f'Starting tech work request conversation (thread: {thread_id})')
    print("=" * 60)
    
    interviewer = Interviewer(request, thread_id=thread_id)
    
    user_input = None
    while not request._done:
        message = interviewer.go(user_input)
        
        if message:
            print(f"\nConsultant: {message}")
        
        if not request._done:
            try:
                user_input = input("\nProduct Owner: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[Conversation ended]")
                break
    
    return request._done


def run_automated(request):
    """Run with prefab inputs for demonstration."""
    prefab_inputs = [
        "CustomerConnect Portal",
        
        "We need a customer self-service portal where they can view their orders, "
        "download invoices, and submit support tickets. It should integrate with our "
        "existing Salesforce CRM and Stripe billing system.",
        
        "We have mockups from our design team and API documentation for both Salesforce "
        "and Stripe. Our backend team has already built authentication endpoints.",
        
        "Our B2B customers, primarily procurement teams and account managers at "
        "mid-size companies",
        
        "About 500 active users initially, potentially growing to 2000",
        
        "We need a beta version by end of Q1 2025, with full launch in Q2",
        
        "$75,000 one-time for development, then $5,000 monthly for maintenance",
        
        "Success means 80% of customers use the portal at least monthly, and we "
        "reduce support ticket volume by 30%",
        
        "Extremely enthusiastic! This will transform our customer experience and "
        "free up our support team to handle more complex issues."
    ]
    
    thread_id = f"tech-demo-{os.getpid()}"
    print(f'Running automated demo (thread: {thread_id})')
    print("=" * 60)
    
    interviewer = Interviewer(request, thread_id=thread_id)
    
    input_iter = iter(prefab_inputs)
    user_input = None
    
    while not request._done:
        message = interviewer.go(user_input)
        
        if message:
            print(f"\nConsultant: {message}")
        
        if not request._done:
            try:
                user_input = next(input_iter)
                print(f"\nProduct Owner: {user_input}")
            except StopIteration:
                print("\n[Demo inputs exhausted]")
                break
    
    return request._done


def display_results(request):
    """Display the collected project requirements."""
    print("\n" + "=" * 60)
    print("PROJECT REQUIREMENTS SUMMARY")
    print("-" * 60)
    
    if request.project_name:
        print(f"\nProject Name: {request.project_name}")
    
    if request.scope:
        print(f"\nScope of Work:")
        print(f"  {request.scope}")
    
    if request.current_status:
        print(f"\nCurrent Status:")
        print(f"  {request.current_status}")
    
    if request.target_users:
        print(f"\nTarget Users: {request.target_users}")
    
    if request.number_of_users:
        print(f"Expected Users: {request.number_of_users.as_int:,}")
    
    if request.timeline:
        print(f"Timeline: {request.timeline}")
    
    if request.budget:
        budget_amount = request.budget.as_int
        if budget_amount == -1:
            print(f"Budget: Unlimited")
        else:
            print(f"Budget: ${budget_amount:,}")
    
    if request.success_metrics:
        print(f"\nSuccess Metrics:")
        print(f"  {request.success_metrics}")
    
    if hasattr(request, 'enthusiasm') and request.enthusiasm is not None:
        enthusiasm = "High" if request.enthusiasm.as_bool else "Moderate"
        print(f"\nClient Enthusiasm: {enthusiasm}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("-" * 60)
    print("1. Review requirements with technical team")
    print("2. Create detailed project plan and architecture")
    print("3. Prepare statement of work for approval")
    print("4. Schedule kickoff meeting with stakeholders")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Tech Work Request Example')
    parser.add_argument('--auto', action='store_true',
                        help='Run with automated demo inputs')
    args = parser.parse_args()
    
    # Load environment variables
    dotenv.load_dotenv(override=True)
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key in .env file")
        sys.exit(1)
    
    # Create and run the interview
    request = create_tech_request()
    
    if args.auto:
        completed = run_automated(request)
    else:
        completed = run_interactive(request)
    
    # Display results if completed
    if completed:
        display_results(request)
    else:
        print("\n[Request not completed]")


if __name__ == "__main__":
    main()