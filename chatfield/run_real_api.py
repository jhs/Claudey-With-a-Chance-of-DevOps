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
class UserRequest(Interview):
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

def main():
    dotenv.load_dotenv(override=True)
    # print("Test Real OpenAI API with Product Owner Request Model ===")

    user_request = UserRequest()
    print(json.dumps(user_request._asdict(), indent=2))
    evaluator = Interviewer(user_request)
    while True:
        print(f'In my loop; request done={user_request.done}')
        request = evaluator.go()
        print(f'Interviewer.go returned {type(request)} {request!r}')

        if user_request.done:
            print(f'Hooray! User request is done.')
            break

        # This would be really cool: change the data model and/or change the evaluator easily.
        # different_request = some_dynamic_build_of_a_different_request(user_request)
        # new_evaluator = Interviewer(different_request) # Or somehow "fork" off
        # user_request, evaluator = different_request, new_evaluator
        # continue

        # print(f'Checkpointer: {evaluator.checkpointer}')
        # print(len(list(evaluator.checkpointer.list(evaluator.config))))

        # Get the messages to render them in the "UI"
        # print(f'---------------------------')
        # print(f'Messages: {len(evaluator.state["messages"])}')
        # for i, msg in enumerate(evaluator.state["messages"]):
        #     print(f'  {i:>3}: {msg!r}')
        # print(f'---------------------------')
    
        print(f"I'm bored")
        break

    print(f"Dialogue finished. Final Request object is done={user_request.done}:")
    print(f"Scope of work: {user_request.scope}")
    print(f"Current status: {user_request.current_status}")
    print(f"Constraints: {user_request.constraints}")
    print(f"Budget: {user_request.budget}")

if __name__ == "__main__":
    main()