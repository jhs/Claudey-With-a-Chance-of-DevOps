"""Match decorator system for Chatfield.

The @match decorator is part of the larger family of transformation decorators.
It evaluates field values to boolean results based on custom criteria.
"""

from typing import Callable, Dict, Any


class MatchDecorator:
    """Dynamic match decorator that creates custom matchers via attribute access.
    
    The @match decorator works alongside other transformation decorators like
    @as_int, @as_list, @choose, etc. All decorators on a field are processed
    in a single LLM call for efficiency.
    
    Usage:
        @match.is_personal("mentions personal use")
        @match.is_commercial("for business purposes")
        @as_list  # Can combine with type transformations
        def purpose(): "What's your project for?"
    """
    
    def __getattr__(self, match_name: str) -> Callable:
        """Create a decorator factory for any attribute access.
        
        Args:
            match_name: The name of the match rule (e.g., 'is_personal')
            
        Returns:
            A decorator factory that takes criteria and returns a decorator
        """
        def decorator_factory(criteria: str) -> Callable:
            """Factory that creates the actual decorator.
            
            Args:
                criteria: Description of what this match rule checks for
                
            Returns:
                Decorator that adds the match rule to the function
            """
            def decorator(func: Callable) -> Callable:
                # Initialize transformations dict if needed (shared with types.py)
                if not hasattr(func, '_chatfield_transformations'):
                    func._chatfield_transformations = {}
                
                # Also keep match_rules for backwards compatibility
                if not hasattr(func, '_chatfield_match_rules'):
                    func._chatfield_match_rules = {}
                
                # Check for duplicate match name
                if match_name in func._chatfield_transformations:
                    raise ValueError(
                        f"Duplicate transformation '{match_name}' on field. "
                        f"Each transformation name must be unique per field."
                    )
                
                # Store in both locations for compatibility
                transformation_data = {
                    'description': f'Evaluate: {criteria} (return true/false)',
                    'criteria': criteria,
                    'type': 'match'
                }
                
                func._chatfield_transformations[match_name] = transformation_data
                func._chatfield_match_rules[match_name] = {
                    'criteria': criteria,
                    'expected': None,  # Will be evaluated by LLM during conversation
                    'type': 'custom'
                }
                
                return func
            
            return decorator
        
        return decorator_factory


# Helper function to get all match rules from a field
def get_field_matches(field_func: Callable) -> dict:
    """Get all match rules from a field.
    
    Args:
        field_func: The field function with match decorators applied
        
    Returns:
        Dictionary of match names to their criteria
    """
    return getattr(field_func, '_chatfield_match_rules', {})


# Create the singleton instance that will be imported
match = MatchDecorator()