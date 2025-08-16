#!/usr/bin/env python3
"""Test real OpenAI API calls with full logging."""

import os
import sys
import json
from chatfield import Interview, hint, must, reject, alice, bob, as_int, as_bool
from chatfield import Interviewer

import dotenv

@bob("Product Owner")
@bob.trait("Not deep technical, but has a clear vision of what they want")
@alice("Expert Technology Consultant")
@alice.trait("Technology partner for the Product Owner")
@alice.trait("Needs to understand the request in detail to implement correctly")
@alice.trait("Keeps things simple and focused without overwhelming the Product Owner")
class TechWorkRequest(Interview):
    """Product Owner's request for technical work"""
    
    @hint("A specific thing you want to build")
    @must("specific enough to implement by a tech team")
    @reject("data regulation environments HIPAA or SOC2")
    def scope():
        "Scope of Work"
    
    def optional_notes():
        """Optional extra notes or context for the request."""

    @as_bool
    def enthusiasm():
        "What is your enthusiasm level for this project"

    @hint("What assets you have to work with, or what you already built, if any")
    def current_status():
        "Current status of the project"

    @reject("budget details or constraints")
    def constraints():
        "Project constraints, e.g. timeline, resources (excluding budget)"

    @as_int
    def number_of_users():
        "Estimated number of users for the project"

    @must("specific amount of money")
    @must("a specific time frequency, e.g. monthly, yearly")
    @as_int("USD of project budget or -1 if unlimited budget")
    def budget():
        "Project budget"

@alice('Kindergarten Teacher')
class FavoriteNumber(Interview):
    """Your favorite number interview."""

    @must("a number between 1 and 100")
    @as_int("favorite number")
    def favorite_number():
        "What is your favorite number?"

def main():
    dotenv.load_dotenv(override=True)
    interview_loop()

def interview_loop():
    # interview = TechWorkRequest()
    interview = FavoriteNumber()

    thread_id = str(os.getpid())
    print(f'Thread ID: {thread_id}')
    interviewer = Interviewer(interview, thread_id=thread_id)

    user_input = None
    while True:
        print(f'In my loop; request done={interview.done}')
        result = interviewer.go(user_input) # TODO: It's possible to start the conversation with a user message.
        print(f'Interviewer returned {type(result)} {result!r}')

        print(f'=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
        for msg in result['messages']:
            # print(f'{msg["role"]:>20}: {msg["content"]}')
            print(f'{msg.__class__.__name__:>30}: {msg.content}')
            # print(f'{msg!r}')
            print(f'=-=-=-=-=-=-=-=-=-=-=-=-=-=-')

        if interview.done:
            print(f'Hooray! User request is done.')
            break

        try:
            user_input = input(f'> ')
        except (KeyboardInterrupt, EOFError):
            print(f'Exit')
            break
    
        user_input = user_input.strip()

        # Get the messages to render them in the "UI"
        # print(f'---------------------------')
        # print(f'Messages: {len(evaluator.state["messages"])}')
        # for i, msg in enumerate(evaluator.state["messages"]):
        #     print(f'  {i:>3}: {msg!r}')
        # print(f'---------------------------')

    print(f"Dialogue finished. Final Request object is done={interview.done}:")
    # print(f"Scope of work: {interview.scope}")
    # print(f"Current status: {interview.current_status}")
    # print(f"Constraints: {interview.constraints}")
    # print(f"Budget: {interview.budget}")

if __name__ == "__main__":
    main()