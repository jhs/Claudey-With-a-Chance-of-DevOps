#!/usr/bin/env python3
"""Example demonstrating the enhanced field proxy with transformation access.

This example shows how fields now:
1. Evaluate to None when not collected (invalid)
2. Evaluate to their raw string value when accessed directly
3. Provide access to transformations via .as_* attributes
"""

from chatfield import Dialogue
from chatfield.socrates import process_socrates_class, SocratesInstance
from chatfield.types import as_int, as_float, as_percent, as_list, as_dict
from chatfield.match import match


class ProjectBudget(Dialogue):
    """Example dialogue with transformations."""
    
    @as_int
    @as_float
    @as_percent  # As percentage of million dollar budget
    @match.is_large("greater than 100000")
    def budget():
        """What's your project budget?"""
    
    @as_list()
    @match.has_frontend("mentions web or UI")
    def technologies():
        """What technologies will you use?"""
    
    @as_dict("name", "role", "experience")
    def team_lead():
        """Who will lead the project?"""


def demonstrate_field_proxy():
    """Demonstrate the enhanced field proxy behavior."""
    
    print("=" * 60)
    print("ENHANCED FIELD PROXY DEMONSTRATION")
    print("=" * 60)
    
    # Process the dialogue class to extract metadata
    meta = process_socrates_class(ProjectBudget)
    
    # Show extracted metadata
    print("\n1. METADATA EXTRACTION:")
    print("-" * 40)
    for field_name, field_meta in meta.fields.items():
        print(f"\nField: {field_name}")
        print(f"  Description: {field_meta.description}")
        if field_meta.transformations:
            print(f"  Transformations: {list(field_meta.transformations.keys())}")
        if field_meta.match_rules:
            print(f"  Match rules: {list(field_meta.match_rules.keys())}")
    
    # Create instance with some collected data
    collected_data = {
        "budget": "One hundred thousand dollars",
        "technologies": "React, Node.js, and PostgreSQL"
        # Note: team_lead is not collected
    }
    
    # Simulate transformation results (normally from LLM)
    transformations = {
        "budget": {
            "as_int": 100000,
            "as_float": 100000.0,
            "as_percent": 0.1  # 10% of million
        },
        "technologies": {
            "as_list": ["React", "Node.js", "PostgreSQL"]
        }
    }
    
    # Simulate match evaluations (normally from LLM)
    match_evaluations = {
        "budget": {
            "is_large": True  # It's >= 100k
        },
        "technologies": {
            "has_frontend": True  # Has React
        }
    }
    
    # Create the instance
    instance = SocratesInstance(meta, collected_data, match_evaluations, transformations)
    print(f"---- type of instance.budget: {type(instance.budget)}")
    
    print("\n2. FIELD ACCESS DEMONSTRATION:")
    print("-" * 40)
    
    # Budget field (collected)
    print("\nBudget field (collected):")
    print(f"  instance.budget is None: {instance.budget is None}")
    print(f"  str(instance.budget): '{str(instance.budget)}'")
    print(f"  instance.budget.as_int: {instance.budget.as_int}")
    print(f"  instance.budget.as_float: {instance.budget.as_float}")
    print(f"  instance.budget.as_percent: {instance.budget.as_percent}")
    print(f"  instance.budget.is_large: {instance.budget.is_large}")
    
    # Technologies field (collected)
    print("\nTechnologies field (collected):")
    print(f"  instance.technologies is None: {instance.technologies is None}")
    print(f"  str(instance.technologies): '{str(instance.technologies)}'")
    print(f"  instance.technologies.as_list: {instance.technologies.as_list}")
    print(f"  instance.technologies.has_frontend: {instance.technologies.has_frontend}")
    
    # Team lead field (NOT collected)
    print("\nTeam lead field (NOT collected):")
    print(f"  instance.team_lead is None: {instance.team_lead is None}")
    
    print("\n3. KEY BEHAVIORS:")
    print("-" * 40)
    print("✓ Fields evaluate to None when not collected (invalid)")
    print("✓ Fields evaluate to raw string when accessed directly")
    print("✓ Transformations accessible via .as_* attributes")
    print("✓ Match rules still work via their named attributes")
    
    # Demonstrate the direct string behavior
    print("\n4. DIRECT STRING BEHAVIOR:")
    print("-" * 40)
    budget = instance.budget
    print(f"  budget == 'One hundred thousand dollars': {budget == 'One hundred thousand dollars'}")
    print(f"  len(budget): {len(budget)}")
    print(f"  budget.value: '{budget.value}'")
    
    # Show error handling
    print("\n5. ERROR HANDLING:")
    print("-" * 40)
    try:
        # Try to access undefined transformation
        _ = instance.budget.as_json
    except AttributeError as e:
        print(f"  Accessing undefined transformation: {e}")
    
    # Show that we can check for field validity
    print("\n6. VALIDITY CHECKING PATTERN:")
    print("-" * 40)
    print("if instance.team_lead is not None:")
    print("    # Field is valid, use it")
    print("else:")
    print("    # Field was not collected or invalid")
    
    if instance.team_lead is not None:
        print(f"  Team lead: {instance.team_lead}")
    else:
        print("  Team lead was not collected")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("The enhanced field proxy provides a clean API where:")
    print("1. Fields are None when invalid/uncollected")
    print("2. Fields evaluate as their raw string value when valid")
    print("3. All transformations are accessible as properties")
    print("4. Match rules continue to work as before")
    print("\nThis allows natural code like:")
    print("  user_request.budget       # 'One hundred US Dollars'")
    print("  user_request.budget.as_int # 100")
    print("  user_request.budget.as_float # 100.0")


if __name__ == "__main__":
    demonstrate_field_proxy()