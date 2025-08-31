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
            .desc("Level of politeness from the Diner")
            .conclude()
            .as_percent()
        
        .build())


def main():
    dotenv.load_dotenv(override=True)
    
    order = create_restaurant_order()
    print(f'Order: {hex(id(order))}')
    
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
    print(f'LangSmith trace: https://smith.langchain.com/o/92e94533-dd45-4b1d-bc4f-4fd9476bb1e4/projects/p/1991a1b2-6dad-4d39-8a19-bbc3be33a8b6/t/{thread_id}\n')
    interviewer = Interviewer(food_order, thread_id=thread_id)
    
    user_input = 'I am vegan.'
    while True:
        message = interviewer.go(user_input)
        print(f'---------------------------')
        print(f"{message}")
        print(f'---------------------------')

        if food_order._done:
            break
        
        if 'Perfect' in user_input:
            raise Exception(f'Detected infinite loop in interview. Aborting.')

        try:
            # user_input = input("You: ").strip()
            user_input = 'Perfect, that is exactly what I want.'
        except (KeyboardInterrupt, EOFError):
            print("\n[Leaving restaurant]")
            break


if __name__ == "__main__":
    main()