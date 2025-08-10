"""Match decorator system for Chatfield."""

from typing import Callable, Dict, Any


class MatchDecorator:
    """Dynamic match decorator that creates custom matchers via attribute access.
    
    Usage:
        @match.is_personal("mentions personal use")
        @match.is_commercial("for business purposes")
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
                # Initialize match rules dict if needed
                if not hasattr(func, '_chatfield_match_rules'):
                    func._chatfield_match_rules = {}
                
                # Check for duplicate match name
                if match_name in func._chatfield_match_rules:
                    raise ValueError(
                        f"Duplicate match name '{match_name}' on field. "
                        f"Each match name must be unique per field."
                    )
                
                # Store the match rule
                func._chatfield_match_rules[match_name] = {
                    'criteria': criteria,
                    'expected': None,  # Will be evaluated by LLM during conversation
                    'type': 'custom'
                }
                
                return func
            
            return decorator
        
        return decorator_factory


# Create the singleton instance that will be imported
match = MatchDecorator()