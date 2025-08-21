#!/usr/bin/env python3
"""Test real OpenAI API calls with full logging."""

import os
import sys
import json

from regex import R
from chatfield import Interview, hint, must, reject, alice, bob, as_int, as_str, as_lang, as_float, as_set, as_list, as_dict, as_percent, as_bool
from chatfield import as_one, as_maybe, as_multi, as_any
from chatfield import Interviewer

import dotenv

# @bob("Product Owner")
# @bob.trait("Not deep technical, but has a clear vision of what they want")
# @alice("Expert Technology Consultant")
# @alice.trait("Technology partner for the Product Owner")
# @alice.trait("Needs to understand the request in detail to implement correctly")
# @alice.trait("Keeps things simple and focused without overwhelming the Product Owner")
# class TechWorkRequest(Interview):
#     """Product Owner's request for technical work"""
    
#     @hint("A specific thing you want to build")
#     @must("specific enough to implement by a tech team")
#     @reject("data regulation environments HIPAA or SOC2")
#     def scope():
#         "Scope of Work"
    
#     def optional_notes():
#         """Optional extra notes or context for the request."""

#     @as_bool
#     def enthusiasm():
#         "What is your enthusiasm level for this project"

#     @hint("What assets you have to work with, or what you already built, if any")
#     def current_status():
#         "Current status of the project"

#     @reject("budget details or constraints")
#     def constraints():
#         "Project constraints, e.g. timeline, resources (excluding budget)"

#     @as_int
#     def number_of_users():
#         "Estimated number of users for the project"

#     @must("specific amount of money")
#     @must("a specific time frequency, e.g. monthly, yearly")
#     @as_int("USD of project budget or -1 if unlimited budget")
#     def budget():
#         "Project budget"

# @bob('Man on the Street')
# @bob('Man awaking from a coma')
# @alice.trait('Talks like Medieval Knight')
# @alice('Cliche Apple ][ Program')
# @alice("The Man's old Kindergarten Teacher")
# @alice("Estranged Ex-Wife")
# @alice('Circus Clown')
@alice('Abraham Lincoln')
@bob('John Wilkes Booth')
# @alice.trait('talks in Cockney rhyming slang')
# @alice.trait("writes in alternating limericks and haiku")
class NotableNumbers(Interview):
    """Numbers important to you"""

    @as_int
    # @as_percent
    # @as_float(f'pi if the number is 3; otherwise tau')
    @must("a number between 1 and 100")
    # @match.aribitrary_name_here('aribtrary predicate here')
    # @as_set('The set of numbers from 1 to the favorite, spelled out as words: odds are English, evens are Spanish')
    # @as_list('A range of numbers from 1 to the favorite, spelled out in English for odds and Thai for evens')
    # @as_dict
    @as_lang.fr
    # @as_lang.de
    # @as_lang.erlang_expression
    # @as_lang.pig_latin(f'pig latin and in all upper-case')
    @as_lang.th
    # @as_lang.greek
    @as_lang.traditionalChinese
    # @as_bool.even('True if the number is even, False if odd')
    @as_bool.odd('True if the number is odd, False if even')
    @as_bool.power_of_two('True if the number is a power of two, False otherwise')

    @as_str('Timestamp in ISO format, representing this value number of minutes since Jan 1 2025 Zulu time')
    @as_set.factors('The set of all factors the number, excluding 1 and the number itself')
    @as_one.parity('even', 'odd')
    @as_maybe.speaking('One syllable when spoken in English', 'Two syllables when spoken in English')
    @as_multi.math_facts('even', 'odd', 'prime', 'composite', 'fibonacci', 'perfect square', 'power of two')
    @as_any.other_facts('prime', 'mersenne prime', 'first digit is 3')
    def favorite():
        "what is your favorite number?"
    
    # @as_int
    # @as_maybe.dimension('shoe', 'beverage', 'shirt', 'car')
    # def size():
    #     """What is your favorite size, and what thing does your size measure?"""
    
    # @as_int
    # @as_int.negative('Negative of the favorite number')
    # @as_int.random('Just any random in from 50 - 59')
    # @as_percent('Fraction of 100 except negative, e.g. disliking 13 implies -0.13')
    # @as_lang.fr('In a long form French paragraph expounding on the number')
    # def least_favorite():
    #     "what is your least favorite number?"

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
    interviewer = Interviewer(interview, thread_id=thread_id)

    user_input = None
    while True:
        # print(f'In my loop; request done={interview._done}')
        # print(f'Current collection status:\n--------------\n{interview._pretty()}\n-------------')

        # TODO: It should be possible to start the conversation with a user message.
        message = interviewer.go(user_input)
        # print(f'Interviewer returned {type(ai_message)} {ai_message!r}')

        # TODO: Not sure if None should ever return back.
        if message:
            print(f'=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
            print(f'{message}')
            print(f'=-=-=-=-=-=-=-=-=-=-=-=-=-=-')

        # print(f'=-=-=-=')
        # print(f'Favorite number: {interview.favorite}')
        # if interview.favorite is not None:
        #     print(f'Implied favorite float: {interview.favorite.as_float}')
        
        # if interview.size:
        #     print(f'Favorite size: {interview.size}')

        # if interview.least_favorite:
        #     print(f'Least favorite number: {interview.least_favorite!r}')
        #     print(f'Reciprocal of least favorite: {interview.least_favorite.as_float!r}')

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

    print(f'')
    print(f'Trace:\n{trace_url}')

if __name__ == "__main__":
    main()