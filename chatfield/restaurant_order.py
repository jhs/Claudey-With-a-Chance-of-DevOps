#!/usr/bin/env python3
"""Restaurant order collection with dynamic vegan adaptation."""

import os
import sys
import dotenv
from sqlalchemy import result_tuple

from chatfield import chatfield
from chatfield import Interviewer


def create_restaurant_order():
    """Create a restaurant order interview instance."""
    return (chatfield()
        .type("Restaurant Order")
        .desc("Taking your order for tonight")
        
        .alice()
            .type("Server")
        
        .bob()
            .type("Diner")
            .trait("First-time visitor")
            .trait.possible("Vegan", "needs vegan, plant-based, non animal product")

        # .field("hurry")
        #     .desc("wishes to be served quickly")
        #     .confidential()
        #     .as_bool()
        
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
        
        .build())


def main():
    dotenv.load_dotenv(override=True)
    
    order = create_restaurant_order()
    print(f'Order: {hex(id(order))}')
    
    print("Welcome to our restaurant")
    print("=" * 40)
    interview_loop(order)
    print("=" * 40)
    
    print(order._pretty())
    print("\nThank you for dining with us!")
    
    # Examples of accessing a confidential field.
    if order.hurry.as_bool:
        print("\n[Note: Expedited request]")
    else:
        print("\n[Note: Normal request]")
    
    # Check if vegan trait was activated
    if 'Vegan' in order._bob.traits:
        print("\n[Note: Guest is vegan - all selections must be plant-based]")

def interview_loop(food_order):
    thread_id = str(os.getpid())
    interviewer = Interviewer(food_order, thread_id=thread_id)
    
    user_input = None
    while True:
        message = interviewer.go(user_input)
        print(f'---------------------------')
        print(f"{message}")

        if food_order._done:
            break
        
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[Leaving restaurant]")
            break


if __name__ == "__main__":
    main()