"""Core decorators for Chatfield."""

from typing import Any, Callable, TypeVar, Union
from functools import wraps
import inspect

from .socrates import process_socrates_class, SocratesInstance
from .conversation import Conversation
from .match import match as match_decorator

T = TypeVar('T')


def gather(cls: T) -> T:
    """Transform a class into a Socratic dialogue interface.
    
    This decorator processes the class annotations to find field descriptions,
    collects metadata from field and class decorators, and adds a gather()
    class method to conduct conversations.
    """
    
    def get_meta():
        """Get metadata, creating it if needed."""
        if not hasattr(cls, '_chatfield_meta_cached'):
            cls._chatfield_meta_cached = process_socrates_class(cls)
        return cls._chatfield_meta_cached
    
    # Add the gather class method
    @classmethod
    def gather_method(cls_inner, **kwargs) -> SocratesInstance:
        """Conduct a Socratic dialogue to gather data.
        
        Args:
            **kwargs: Additional arguments passed to the conversation handler.
        """
        meta = get_meta()
        conversation = Conversation(meta, **kwargs)
        collected_data = conversation.conduct_conversation()
        # Use create_instance to properly include match evaluations
        return conversation.create_instance()
    
    # Add the method to the class
    setattr(cls, 'gather', gather_method)
    
    # Create a property-like access that always gets fresh metadata
    # This ensures it works regardless of decorator order
    class MetaDescriptor:
        def __get__(self, obj, objtype):
            return get_meta()
    
    cls._chatfield_meta = MetaDescriptor()
    
    return cls


def must(rule: str) -> Callable:
    """Mark what an answer must include.
    
    This is now implemented as a wrapper around the @match system,
    where the rule is evaluated and expected to match (True).
    
    Args:
        rule: Description of what the answer must include
    """
    def decorator(func: Callable) -> Callable:
        # Generate unique internal match name
        match_id = f"_must_{hash(rule) & 0xFFFFFF:06x}"
        
        # Initialize match rules dict if needed
        if not hasattr(func, '_chatfield_match_rules'):
            func._chatfield_match_rules = {}
        
        # Check for hash collision (extremely rare but possible)
        if match_id in func._chatfield_match_rules:
            # If same rule text, it's a duplicate - error
            if func._chatfield_match_rules[match_id]['criteria'] == rule:
                raise ValueError(f"Duplicate @must rule: '{rule}'")
            # If different rule text, it's a hash collision - regenerate
            counter = 0
            new_match_id = match_id
            while new_match_id in func._chatfield_match_rules:
                counter += 1
                new_match_id = f"{match_id}_{counter}"
            match_id = new_match_id
        
        # Store as a match rule with expected=True
        func._chatfield_match_rules[match_id] = {
            'criteria': rule,
            'expected': True,  # Must rules expect True
            'type': 'must'
        }
        
        # Also keep backward compatibility
        if not hasattr(func, '_chatfield_must_rules'):
            func._chatfield_must_rules = []
        func._chatfield_must_rules.append(rule)
        
        return func
    
    return decorator


def reject(rule: str) -> Callable:
    """Mark what to avoid in answers.
    
    This is now implemented as a wrapper around the @match system,
    where the rule is evaluated and expected NOT to match (False).
    
    Args:
        rule: Description of what the answer should avoid
    """
    def decorator(func: Callable) -> Callable:
        # Generate unique internal match name
        match_id = f"_reject_{hash(rule) & 0xFFFFFF:06x}"
        
        # Initialize match rules dict if needed
        if not hasattr(func, '_chatfield_match_rules'):
            func._chatfield_match_rules = {}
        
        # Check for hash collision
        if match_id in func._chatfield_match_rules:
            # If same rule text, it's a duplicate - error
            if func._chatfield_match_rules[match_id]['criteria'] == rule:
                raise ValueError(f"Duplicate @reject rule: '{rule}'")
            # If different rule text, it's a hash collision - regenerate
            counter = 0
            new_match_id = match_id
            while new_match_id in func._chatfield_match_rules:
                counter += 1
                new_match_id = f"{match_id}_{counter}"
            match_id = new_match_id
        
        # Store as a match rule with expected=False
        func._chatfield_match_rules[match_id] = {
            'criteria': rule,
            'expected': False,  # Reject rules expect False
            'type': 'reject'
        }
        
        # Also keep backward compatibility
        if not hasattr(func, '_chatfield_reject_rules'):
            func._chatfield_reject_rules = []
        func._chatfield_reject_rules.append(rule)
        
        return func
    
    return decorator


def hint(tooltip: str) -> Callable:
    """Provide helpful context for users.
    
    Args:
        tooltip: Helpful explanation or example for the field
    """
    def decorator(func: Callable) -> Callable:
        if not hasattr(func, '_chatfield_hints'):
            func._chatfield_hints = []
        func._chatfield_hints.append(tooltip)
        return func
    
    return decorator


def user(context: str) -> Callable:
    """Add information about the user.
    
    Args:
        context: Information about who you're talking to
    """
    def decorator(cls: T) -> T:
        if not hasattr(cls, '_chatfield_user_context'):
            cls._chatfield_user_context = []
        cls._chatfield_user_context.append(context)
        return cls
    
    return decorator


def agent(behavior: str) -> Callable:
    """Define how the agent should behave.
    
    Args:
        behavior: Description of how the agent should act
    """
    def decorator(cls: T) -> T:
        if not hasattr(cls, '_chatfield_agent_context'):
            cls._chatfield_agent_context = []
        cls._chatfield_agent_context.append(behavior)
        return cls
    
    return decorator


# Function-based field definitions are now handled directly by the decorators above