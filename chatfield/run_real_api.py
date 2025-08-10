#!/usr/bin/env python3
"""Test real OpenAI API calls with full logging."""

import os
import sys
from chatfield import Dialogue, user, agent, hint, must, reject
from chatfield import Evaluator

import dotenv

@user("Product Owner")
@user("Not deep technical, but has a clear vision of what they want")
@agent("Technology partner for the Product Owner")
@agent("Needs to understand the request in detail to implement correctly")
class UserRequest(Dialogue):
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

def main():
    dotenv.load_dotenv(override=True)
    print("Test Real OpenAI API with Product Owner Request Model ===")

    user_request = UserRequest()

    evaluator = Evaluator(user_request)
    while True:
        print(f'In my loop; request done={user_request.done}')
        res = evaluator.go()
        print(f'Evaluator.go returned {res!r}. User request is done={user_request.done}')

        if user_request.done:
            break
    
        print(f"I'm bored")
        break

    print(f"Dialogue finished. Final Request object is done={user_request.done}:")
    print(f"Scope of work: {user_request.scope}")
    print(f"Current status: {user_request.current_status}")
    print(f"Constraints: {user_request.constraints}")
    print(f"Budget: {user_request.budget}")

if __name__ == "__main__":
    main()