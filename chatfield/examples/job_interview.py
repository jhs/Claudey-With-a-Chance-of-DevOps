#!/usr/bin/env python3
"""
Job Interview Example
=====================

This example demonstrates:
- Possible traits that activate based on conversation
- Confidential fields (has_mentored)
- Conclusion fields (preparedness assessment)
- Regular fields with validation (@must)

Run with:
    python examples/job_interview.py

For automated demo:
    python examples/job_interview.py --auto
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


def create_job_interview():
    """Create a job interview for a software engineer position."""
    return (chatfield()
        .type("JobInterview")
        .desc("Software Engineer position interview")
        
        .alice()
            .type("Hiring Manager")
            .trait("Professional and encouraging")
        
        .bob()
            .type("Candidate")
            .trait.possible("career-changer", "mentions different industry or transferable skills")
            .trait.possible("senior-level", "10+ years of experience or leadership roles")
        
        .field("experience")
            .desc("Tell me about your relevant experience")
            .must("specific examples or projects")
        
        .field("technical_skills")
            .desc("What programming languages and technologies are you proficient in?")
            .hint("Please mention specific languages, frameworks, and tools")
        
        # Confidential field - tracked but never mentioned
        .field("has_mentored")
            .desc("Gives specific evidence of professionally mentoring junior colleagues")
            .confidential()
            .as_bool()
        
        # Another confidential field
        .field("shows_leadership")
            .desc("Demonstrates leadership qualities or initiatives")
            .confidential()
            .as_bool()
        
        # Conclusion field - assessed at the end
        .field("preparedness")
            .desc("Evaluate candidate's preparation: research, questions, examples")
            .conclude()
            .as_one.assessment("unprepared", "somewhat prepared", "well prepared", "exceptionally prepared")
        
        .field("cultural_fit")
            .desc("Assessment of cultural fit based on values and communication style")
            .conclude()
            .as_one.assessment("poor fit", "potential fit", "good fit", "excellent fit")
        
        .build())


def run_interactive(interview):
    """Run the interview interactively."""
    thread_id = f"job-interview-{os.getpid()}"
    print(f'Starting job interview (thread: {thread_id})')
    print("=" * 60)
    print("Software Engineer Position Interview")
    print("=" * 60)
    
    interviewer = Interviewer(interview, thread_id=thread_id)
    
    user_input = None
    print("\n[Interview begins]\n")
    
    while not interview._done:
        message = interviewer.go(user_input)
        
        if message:
            print(f"\nInterviewer: {message}")
        
        if not interview._done:
            try:
                user_input = input("\nCandidate: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[Interview ended by user]")
                break
    
    if interview._done:
        print("\n[Interview complete - Thank you for your time]")
    
    return interview._done


def run_automated(interview):
    """Run with prefab inputs for demonstration."""
    prefab_inputs = [
        "I've spent 5 years in finance, but I've been passionate about programming since college. "
        "I built an automated trading system in Python that saved our team 20 hours per week. "
        "I also created a risk analysis dashboard using React and D3.js.",
        
        "I'm proficient in Python, JavaScript, and SQL. I've worked extensively with React, Node.js, "
        "and Django. I also have experience with Docker, AWS, and CI/CD pipelines using GitHub Actions.",
        
        "In my previous role, I regularly mentored junior analysts on Python programming and data analysis. "
        "I also led a cross-functional team to implement our new reporting system.",
        
        "I've researched your company's focus on fintech innovation and your recent Series B funding. "
        "I'm particularly excited about your API-first approach and how my background in both finance "
        "and engineering could contribute to bridging technical and business requirements. "
        "What are the biggest technical challenges your team is currently facing?"
    ]
    
    thread_id = f"job-demo-{os.getpid()}"
    print(f'Running automated demo (thread: {thread_id})')
    print("=" * 60)
    print("Software Engineer Position Interview (Demo)")
    print("=" * 60)
    
    interviewer = Interviewer(interview, thread_id=thread_id)
    
    input_iter = iter(prefab_inputs)
    user_input = None
    
    print("\n[Interview begins]\n")
    
    while not interview._done:
        message = interviewer.go(user_input)
        
        if message:
            print(f"\nInterviewer: {message}")
        
        if not interview._done:
            try:
                user_input = next(input_iter)
                print(f"\nCandidate: {user_input}")
            except StopIteration:
                print("\n[Demo inputs exhausted]")
                break
    
    if interview._done:
        print("\n[Interview complete - Thank you for your time]")
    
    return interview._done


def display_results(interview):
    """Display the interview assessment."""
    print("\n" + "=" * 60)
    print("INTERVIEW ASSESSMENT SUMMARY")
    print("-" * 60)
    
    # Regular fields
    if interview.experience:
        print("✓ Experience shared: Yes")
    
    if interview.technical_skills:
        print("✓ Technical skills discussed: Yes")
    
    # Confidential fields (for internal assessment)
    print("\n--- Confidential Assessment ---")
    
    if hasattr(interview, 'has_mentored') and interview.has_mentored is not None:
        mentoring = "Yes" if interview.has_mentored.as_bool else "No"
        print(f"Has mentored others: {mentoring}")
    
    if hasattr(interview, 'shows_leadership') and interview.shows_leadership is not None:
        leadership = "Yes" if interview.shows_leadership.as_bool else "No"
        print(f"Shows leadership qualities: {leadership}")
    
    # Conclusion fields
    print("\n--- Final Evaluation ---")
    
    if interview.preparedness:
        print(f"Preparation level: {interview.preparedness}")
    
    if interview.cultural_fit:
        print(f"Cultural fit: {interview.cultural_fit}")
    
    # Check activated traits
    print("\n--- Candidate Profile ---")
    
    traits = interview._chatfield['roles']['bob'].get('possible_traits', {})
    if traits.get('career-changer', {}).get('active'):
        print("• Career changer: Yes")
    
    if traits.get('senior-level', {}).get('active'):
        print("• Senior level: Yes")
    
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Job Interview Example')
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
    interview = create_job_interview()
    
    if args.auto:
        completed = run_automated(interview)
    else:
        completed = run_interactive(interview)
    
    # Display results if completed
    if completed:
        display_results(interview)
    else:
        print("\n[Interview not completed]")


if __name__ == "__main__":
    main()