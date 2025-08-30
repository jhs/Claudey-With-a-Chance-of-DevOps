#!/usr/bin/env python3
"""Job interview with confidential assessments and conclusion fields."""

import os
import sys
import dotenv
from chatfield.builder import chatfield
from chatfield import Interviewer


def main():
    dotenv.load_dotenv(override=True)
    
    job_interview = (chatfield()
        .type("JobInterview")
        .desc("Software Engineer position interview")
        
        .alice()
            .type("Hiring Manager")
        
        .bob()
            .type("Candidate")
            .trait.possible("career-changer", "mentions different industry or transferable skills")
        
        .field("experience")
            .desc("Tell me about your relevant experience")
            .must("specific examples")
        
        # Confidential field (tracked during conversation, never mentioned)
        .field("has_mentored")
            .desc("Gives specific evidence of professionally mentoring junior colleagues")
            .confidential()
            .as_bool()
        
        # Conclusion field (evaluated only at end, automatically confidential)
        .field("preparedness")
            .desc("Evaluate candidate's preparation: research, questions, examples")
            .conclude()
            .as_one.assessment("unprepared", "somewhat prepared", "well prepared", "exceptionally prepared")
        
        .build())
    
    print("Job Interview - Software Engineer Position")
    print("=" * 50)
    
    interview_loop(job_interview)
    
    # Print assessment summary
    print("\n" + "=" * 50)
    print("ASSESSMENT SUMMARY")
    print("-" * 50)
    
    # Show regular field
    if job_interview.experience:
        print(f"Experience shared: Yes")
    
    # Show confidential field
    if job_interview.has_mentored is not None:
        print(f"Has mentored others: {'Yes' if job_interview.has_mentored else 'No'}")
    
    # Show conclusion field
    if job_interview.preparedness:
        print(f"Preparation level: {job_interview.preparedness}")
    
    # Check activated traits
    if job_interview._chatfield['roles']['bob'].get('possible_traits', {}).get('career-changer', {}).get('active'):
        print("Note: Candidate is changing careers")
    
    print("=" * 50)


def interview_loop(interview):
    thread_id = str(os.getpid())
    interviewer = Interviewer(interview, thread_id=thread_id)
    
    user_input = None
    print("\n[Interview begins]\n")
    
    while not interview._done:
        message = interviewer.go(user_input)
        
        if message:
            print(f"Interviewer: {message}")
        
        if not interview._done:
            try:
                user_input = input("\nCandidate: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[Interview ended by user]")
                break
    
    if interview._done:
        print("\n[Interview complete - Thank you for your time]")


if __name__ == "__main__":
    main()