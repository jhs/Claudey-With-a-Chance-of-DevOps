#!/usr/bin/env python3
"""Example demonstrating Chatfield's new type transformation decorators.

This example shows how to use the expanded decorator family to transform
and validate user responses in various ways, all processed in a single
LLM call for efficiency.
"""

from chatfield import Dialogue
from chatfield.match import match
from chatfield.types import (
    as_int, as_float, as_percent,
    as_list, as_set, as_dict,
    choose, choose_one, choose_many,
    as_date, as_duration, as_timezone
)


class ProjectPlanning(Dialogue):
    """Gather information for project planning with rich type transformations."""
    
    # Numeric transformations
    @as_int
    @match.is_reasonable("between 1 and 50 people")
    def team_size(): return "How many people will be on the team?"
    
    @as_float
    @as_percent  # Get both raw number and percentage of million
    @match.is_enterprise("greater than $100,000")
    def budget(): return "What's your budget? (we'll calculate %% of $1M for reference)"
    
    # Collection transformations
    @as_list(of=str)
    @match.has_frontend("mentions web, mobile, or UI")
    @match.has_backend("mentions server, API, or database")
    def technologies(): return "What technologies will you use?"
    
    @as_set  # Unique skills only
    def required_skills(): return "What skills are needed? (duplicates will be removed)"
    
    @as_dict("name", "role", "experience")
    def team_lead(): return "Who will lead? (provide name, role, and years of experience)"
    
    # Choice selections
    @choose_one("startup", "scaleup", "enterprise", "government")
    def company_type(): return "What type of organization?"
    
    @choose_many("development", "testing", "deployment", "monitoring", "documentation")
    def phases(): return "Which project phases will you need?"
    
    @choose("low", "medium", "high", "critical", mandatory=True)
    def priority(): return "What's the priority level?"
    
    # Time and date transformations
    @as_date(format="ISO")
    @match.is_soon("within next 3 months")
    def start_date(): return "When will the project start?"
    
    @as_duration(unit="days")
    @match.is_agile("less than 30 days")
    def sprint_length(): return "How long are your sprints?"
    
    @as_timezone
    def team_timezone(): return "What timezone is your team in?"


class UserProfile(Dialogue):
    """Example showing combined transformations on single fields."""
    
    @as_int
    @as_percent  # Percentage of 100 years
    @match.is_adult("18 or older")
    @match.is_senior("65 or older")
    def age(): return "What's your age?"
    
    @as_list(of=str)
    @choose_many("reading", "gaming", "sports", "music", "travel", "cooking")
    @match.is_active("includes physical activities")
    def hobbies(): return "What are your hobbies?"
    
    @as_float
    @as_duration(unit="hours")  # Convert to hours if given as duration
    @match.is_fulltime("roughly 40 hours per week")
    def work_hours(): return "How many hours do you work per week?"
    
    @as_dict("street", "city", "state", "zip")
    @match.is_urban("mentions city or urban area")
    def location(): return "Where are you located? (street, city, state, zip)"


class EventPlanning(Dialogue):
    """Example for event planning with various transformations."""
    
    @choose_one("conference", "workshop", "meetup", "webinar", mandatory=True)
    def event_type(): return "What type of event?"
    
    @as_int
    @match.needs_venue("more than 20 people")
    @match.needs_catering("more than 50 people")
    def attendees(): return "Expected number of attendees?"
    
    @as_date(format="US")
    @as_duration(unit="days")  # Days from today
    @match.has_lead_time("at least 30 days from now")
    def event_date(): return "When is the event?"
    
    @as_list(of=str)
    @as_set  # Remove duplicate equipment
    def equipment(): return "What equipment do you need?"
    
    @as_percent
    @match.is_virtual("greater than 0.5")
    def virtual_attendance(): return "What percentage will attend virtually?"


def demonstrate_prompt_building():
    """Show how all transformations create a single LLM prompt."""
    from chatfield.types import build_transformation_prompt, get_field_transformations
    
    # Create a field with multiple transformations
    @as_int
    @as_percent
    @match.is_large("greater than 1000")
    @choose("small", "medium", "large", "enterprise")
    def budget():
        return "Project budget"
    
    # Get all transformations
    transformations = get_field_transformations(budget)
    
    # Build the prompt that would be sent to the LLM
    prompt = build_transformation_prompt(
        field_name="budget",
        field_description="Project budget",
        user_response="about fifty thousand dollars",
        transformations=transformations
    )
    
    print("=" * 60)
    print("EXAMPLE LLM PROMPT FOR PARALLEL PROCESSING:")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    print("\nThe LLM would return all transformations in one response:")
    print("""{
    "as_int": 50000,
    "as_percent": 0.05,  // Assuming out of $1M
    "is_large": true,
    "choose": "large"
}""")


def main():
    """Main example runner."""
    print("Chatfield Type Transformations Example")
    print("=" * 40)
    print("\nThis example demonstrates the new type transformation decorators.")
    print("Each field can have multiple decorators that are all processed")
    print("in a SINGLE LLM call for maximum efficiency.\n")
    
    print("Available decorator families:")
    print("- Numeric: @as_int, @as_float, @as_percent")
    print("- Collections: @as_list, @as_set, @as_dict")
    print("- Choices: @choose, @choose_one, @choose_many")
    print("- Time/Date: @as_date, @as_duration, @as_timezone")
    print("- Matching: @match.condition('criteria')")
    print("\nAll decorators work together in parallel!")
    
    # Demonstrate prompt building
    demonstrate_prompt_building()
    
    print("\n" + "=" * 60)
    print("EXAMPLE DIALOGUES DEFINED:")
    print("=" * 60)
    print("\n1. ProjectPlanning - Complex project setup with all types")
    print("2. UserProfile - User information with combined transformations")
    print("3. EventPlanning - Event details with date/time focus")
    
    print("\nEach dialogue field processes ALL its decorators in one LLM call,")
    print("returning the raw response plus all requested transformations.")
    
    # Note: Actually running the dialogues would require LLM integration
    # This example focuses on showing the decorator structure
    
    print("\n" + "=" * 60)
    print("KEY BENEFITS:")
    print("=" * 60)
    print("✓ Single LLM round-trip for all transformations (fast & efficient)")
    print("✓ Clean decorator syntax (Pythonic and readable)")
    print("✓ Composable decorators (mix and match as needed)")
    print("✓ Type-safe transformations (get ints, floats, lists, etc.)")
    print("✓ Parallel processing (all decorators evaluated together)")


if __name__ == "__main__":
    main()