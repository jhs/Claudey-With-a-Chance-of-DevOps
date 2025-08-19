#!/usr/bin/env python3
"""Test real OpenAI API calls with full logging."""

import os
import sys
import json
from chatfield import Interview, hint, must, reject, alice, bob, as_int, as_float, as_bool
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

@bob('Man on the Street')
@alice.trait('Medieval Knight')
# @alice('Cliche Apple ][ Program')
# @alice('Kindergarten Teacher')
class NotableNumbers(Interview):
    """Numbers important to you"""

    @as_int
    # @as_float(f'pi if the number is 3; otherwise tau')
    @must("a number between 1 and 100")
    # @match.aribitrary_name_here('aribtrary predicate here')
    def favorite():
        "what is your favorite number? your silence implies that you love 3"
    
    @as_int(f'the negation, e.g. given 13 results is -13')
    @as_float(f'the reciprocal')
    def least_favorite():
        "what is your least favorite number?"

def main():
    dotenv.load_dotenv(override=True)
    interview_loop()

def interview_loop():
    # interview = TechWorkRequest()
    interview = NotableNumbers()
    print(f'The main interview object: {interview!r}')

    thread_id = str(os.getpid())
    print(f'Thread ID: {thread_id}')
    trace_url = """https://smith.langchain.com/o/92e94533-dd45-4b1d-bc4f-4fd9476bb1e4/projects/p/1991a1b2-6dad-4d39-8a19-bbc3be33a8b6?searchModel=%7B%22filter%22%3A%22and%28eq%28metadata_key%2C+%5C%22thread_id%5C%22%29%2C+eq%28metadata_value%2C+%5C%22{thread_id}%5C%22%29%29%22%7D&runtab=0&timeModel=%7B%22duration%22%3A%227d%22%7D&peek=0b7068bb-e9c6-4637-b5ca-b7f35d0689a7&peeked_trace=4d1b16a3-171c-4c08-99a9-d54d6a2e17bf"""
    trace_url = trace_url.format(thread_id=thread_id)
    print(f'Trace: {trace_url}')
    interviewer = Interviewer(interview, thread_id=thread_id)

    user_input = None
    while True:
        # print(f'In my loop; request done={interview._done}')
        print(f'Current collection status:\n--------------\n{interview._pretty()}\n-------------')

        result = interviewer.go(user_input) # TODO: It's possible to start the conversation with a user message.
        # print(f'Interviewer returned {type(result)} {result!r}')

        # TODO: Not sure if None should ever return back.
        # latest_message = result['messages'][-1] if result and result.get('messages') else None
        all_messages = (result and result['messages']) or []
        for message in all_messages:
            print(f'=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
            print(f'{message.__class__.__name__:<15}: {message.content}')
            print(f'=-=-=-=-=-=-=-=-=-=-=-=-=-=-')

        print(interview._pretty())
        print(f'=-=-=-=')
        print(f'Favorite number: {interview.favorite}')
        if interview.favorite is not None:
            print(f'Implied favorite float: {interview.favorite.as_float}')
        
        if interview.least_favorite:
            print(f'Least favorite number: {interview.least_favorite!r}')
            print(f'Reciprocal of least favorite: {interview.least_favorite.as_float!r}')

        if interview._done:
            print(f'Hooray! User request is done.')
            break

        try:
            user_input = input(f'Your response> ')
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

    print(f'---------------------------')
    print(f"Dialogue finished:")
    print(interview._pretty())

if __name__ == "__main__":
    main()