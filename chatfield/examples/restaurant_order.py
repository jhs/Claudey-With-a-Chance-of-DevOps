#!/usr/bin/env python3
"""
Restaurant Order Example
========================

This example demonstrates:
- Dynamic trait activation (vegan adaptation)
- Selection fields with choices
- Confidential fields (hurry)
- Conclusion fields (politeness)
- Alice with personality traits (limmericks)

Run with:
    python examples/restaurant_order.py

For automated demo:
    python examples/restaurant_order.py --auto
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


def create_restaurant_order():
    """Create a restaurant order interview instance."""
    return (chatfield()
        .type("Restaurant Order")
        .desc("Taking your order for tonight")
        
        .alice()
            .type("Server")
            .trait("Speaks in limmericks")
        
        .bob()
            .type("Diner")
            .trait("First-time visitor")
            .trait.possible("Vegan", "needs vegan, plant-based, non animal product")
        
        .field("starter")
            .desc("starter or appetizer")
            .as_one.selection("Sir Digby Chicken Caesar", "Shrimp cocktail", "Garden salad")
        
        .field("main_course")
            .desc("Main course")
            .hint("Choose from: Grilled salmon, Veggie pasta, Beef tenderloin, Chicken parmesan")
            .as_one.selection("Grilled salmon", "Veggie pasta", "Beef tenderloin", "Chicken parmesan")
        
        .field("dessert")
            .desc("Mandatory dessert; choices: Cheesecake, Creamy Chocolate mousse, Fruit sorbet")
            .as_one.selection("Cheesecake", "Creamy Chocolate mousse", "Fruit sorbet")

        .field("hurry")
            .desc("wishes to be served quickly")
            .confidential()
            .as_bool()

        .field("politeness")
            .desc("Level of politeness from the Diner; but automatic 23% if they mention anything about Belgium")
            .conclude()
            .as_percent()
        
        .build())


def run_interactive(order):
    """Run the interview interactively."""
    thread_id = f"restaurant-{os.getpid()}"
    print(f'Starting restaurant order conversation (thread: {thread_id})')
    print("=" * 60)
    
    interviewer = Interviewer(order, thread_id=thread_id)
    
    user_input = None
    while not order._done:
        message = interviewer.go(user_input)
        
        if message:
            print(f"\nServer: {message}")
        
        if not order._done:
            try:
                user_input = input("\nYou: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[Leaving restaurant]")
                break
    
    return order._done


def run_automated(order):
    """Run with prefab inputs for demonstration."""
    prefab_inputs = [
        'I am vegan.',
        'Garden salad please',
        'Veggie pasta sounds great',
        'Fruit sorbet',
        'Thank you so much, that is perfect!'
    ]
    
    thread_id = f"restaurant-demo-{os.getpid()}"
    print(f'Running automated demo (thread: {thread_id})')
    print("=" * 60)
    
    interviewer = Interviewer(order, thread_id=thread_id)
    
    input_iter = iter(prefab_inputs)
    user_input = None
    
    while not order._done:
        message = interviewer.go(user_input)
        
        if message:
            print(f"\nServer: {message}")
        
        if not order._done:
            try:
                user_input = next(input_iter)
                print(f"\nYou: {user_input}")
            except StopIteration:
                print("\n[Demo inputs exhausted]")
                break
    
    return order._done


def display_results(order):
    """Display the collected order information."""
    print("\n" + "=" * 60)
    print("ORDER SUMMARY")
    print("-" * 60)
    
    if order.starter:
        print(f"Starter: {order.starter}")
    
    if order.main_course:
        print(f"Main Course: {order.main_course}")
    
    if order.dessert:
        print(f"Dessert: {order.dessert}")
    
    # Confidential field (for internal use)
    if hasattr(order, 'hurry') and order.hurry is not None:
        if order.hurry.as_bool:
            print("\n[Internal Note: Rush order requested]")
        else:
            print("\n[Internal Note: Normal service pace]")
    
    # Conclusion field
    if hasattr(order, 'politeness') and order.politeness is not None:
        politeness_pct = order.politeness.as_percent * 100
        print(f"[Internal Note: Guest politeness: {politeness_pct:.0f}%]")
    
    # Check if vegan trait was activated
    if order._chatfield['roles']['bob'].get('possible_traits', {}).get('Vegan', {}).get('active'):
        print("\n[Note: Guest is vegan - all selections are plant-based]")
    
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Restaurant Order Example')
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
    order = create_restaurant_order()
    
    if args.auto:
        completed = run_automated(order)
    else:
        completed = run_interactive(order)
    
    # Display results if completed
    if completed:
        display_results(order)
    else:
        print("\n[Order not completed]")


if __name__ == "__main__":
    main()