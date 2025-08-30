#!/usr/bin/env python3
"""Restaurant order collection with dynamic vegan adaptation."""

import os
import sys
import dotenv
from sqlalchemy import result_tuple
from chatfield.builder import chatfield
from chatfield import Interviewer


def create_restaurant_order():
    """Create a restaurant order interview instance."""
    return (chatfield()
        .type("RestaurantOrder")
        .desc("Taking your order for tonight")
        
        .alice()
            .type("Server")
        
        .bob()
            .type("Diner")
            .trait("Hungry")
            .trait.possible("Vegan", "mentions vegan, plant-based, no meat/dairy")
            .trait.possible("Budget-conscious", "asks about prices, deals, specials")

        .field("restrictions")
            .desc("Any dietary restrictions or preferences")
            .confidential()
            .as_bool.vegan('Vegan dietary restrictions')
        
        .field("starter")
            .desc("What would you like to start with?")
            .as_one.selection("Sir Digby Chicken Caesar", "Shrimp cocktail", "Garden salad")
        
        .field("main_course")
            .desc("Main course; choose from: Grilled salmon, Veggie pasta, Beef tenderloin, Chicken parmesan")
            .as_one.selection("Grilled salmon", "Veggie pasta", "Beef tenderloin", "Chicken parmesan")
        
        .field("dessert")
            .desc("Dessert; choices: Cheesecake, Creamy Chocolate mousse, Fruit sorbet")
            .as_one.selection("Cheesecake", "Creamy Chocolate mousse", "Fruit sorbet")
        
        .build())


def main():
    dotenv.load_dotenv(override=True)
    
    restaurant_order = create_restaurant_order()
    
    print("Welcome to our restaurant!")

    print("=" * 40)
    interview_loop(restaurant_order)
    print("=" * 40)
    
    print(restaurant_order._pretty())
    print("\nThank you for dining with us!")
    
    # Check if vegan trait was activated
    if 'Vegan' in restaurant_order._bob.traits:
        print("\n[Note: Guest is vegan - all selections must be plant-based]")

def interview_loop(food_order):
    thread_id = str(os.getpid())
    interviewer = Interviewer(food_order, thread_id=thread_id)
    
    user_input = None
    while not food_order._done:
        message = interviewer.go(user_input)
        print(f"\nServer: {message}")

        if food_order._done:
            break
        
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[Leaving restaurant]")
            break


if __name__ == "__main__":
    main()