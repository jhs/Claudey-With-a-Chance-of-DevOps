"""Core decorators for Chatfield."""

import sys

from typing import Any, Callable, TypeVar, Type, Optional, Union

T = TypeVar('T')


# def must(rule: str) -> Callable:
#     """Mark what an answer must include.
    
#     This is now implemented as a wrapper around the @match system,
#     where the rule is evaluated and expected to match (True).
    
#     Args:
#         rule: Description of what the answer must include
#     """
#     def decorator(func: Callable) -> Callable:
#         # Generate unique internal match name
#         match_id = f"_must_{hash(rule) & 0xFFFFFF:06x}"
        
#         # Initialize match rules dict if needed
#         if not hasattr(func, '_chatfield_match_rules'):
#             func._chatfield_match_rules = {}
        
#         # Check for hash collision (extremely rare but possible)
#         if match_id in func._chatfield_match_rules:
#             # If same rule text, it's a duplicate - error
#             if func._chatfield_match_rules[match_id]['criteria'] == rule:
#                 raise ValueError(f"Duplicate @must rule: '{rule}'")
#             # If different rule text, it's a hash collision - regenerate
#             counter = 0
#             new_match_id = match_id
#             while new_match_id in func._chatfield_match_rules:
#                 counter += 1
#                 new_match_id = f"{match_id}_{counter}"
#             match_id = new_match_id
        
#         # Store as a match rule with expected=True
#         func._chatfield_match_rules[match_id] = {
#             'criteria': rule,
#             'expected': True,  # Must rules expect True
#             'type': 'must'
#         }
        
#         # Store in must_rules for compatibility with existing code
#         if not hasattr(func, '_chatfield_must_rules'):
#             func._chatfield_must_rules = []
#         func._chatfield_must_rules.append(rule)
        
#         return func
    
#     return decorator


# def reject(rule: str) -> Callable:
#     """Mark what to avoid in answers.
    
#     This is now implemented as a wrapper around the @match system,
#     where the rule is evaluated and expected NOT to match (False).
    
#     Args:
#         rule: Description of what the answer should avoid
#     """
#     def decorator(func: Callable) -> Callable:
#         # Generate unique internal match name
#         match_id = f"_reject_{hash(rule) & 0xFFFFFF:06x}"
        
#         # Initialize match rules dict if needed
#         if not hasattr(func, '_chatfield_match_rules'):
#             func._chatfield_match_rules = {}
        
#         # Check for hash collision
#         if match_id in func._chatfield_match_rules:
#             # If same rule text, it's a duplicate - error
#             if func._chatfield_match_rules[match_id]['criteria'] == rule:
#                 raise ValueError(f"Duplicate @reject rule: '{rule}'")
#             # If different rule text, it's a hash collision - regenerate
#             counter = 0
#             new_match_id = match_id
#             while new_match_id in func._chatfield_match_rules:
#                 counter += 1
#                 new_match_id = f"{match_id}_{counter}"
#             match_id = new_match_id
        
#         # Store as a match rule with expected=False
#         func._chatfield_match_rules[match_id] = {
#             'criteria': rule,
#             'expected': False,  # Reject rules expect False
#             'type': 'reject'
#         }
        
#         # Also keep backward compatibility
#         if not hasattr(func, '_chatfield_reject_rules'):
#             func._chatfield_reject_rules = []
#         func._chatfield_reject_rules.append(rule)
        
#         return func
    
#     return decorator


# def hint(tooltip: str) -> Callable:
#     """Provide helpful context for users.
    
#     Args:
#         tooltip: Helpful explanation or example for the field
#     """
#     def decorator(func: Callable) -> Callable:
#         if not hasattr(func, '_chatfield_hints'):
#             func._chatfield_hints = []
#         func._chatfield_hints.append(tooltip)
#         return func
    
#     return decorator



# Implement a more generic approach for decorating the Interview class.
class InterviewDecorator:
    """Decorator for Interview classes to define their behavior."""
    def __init__(self, name):
        self.name = name
    
    # A helper to ensure that a class has ._roles and its contents initialized.
    def _ensure_roles(self, cls):
        if not hasattr(cls, '_roles'):
            cls._roles = {}
        if self.name not in cls._roles:
            cls._roles[self.name] = {'type': None, 'traits': []}
    
    def __call__(self, callable_or_role: Optional[Union[Callable, str]]=None) -> Callable:
        """Makes these work (but not simultaneously on the same class):
        
        @alice
        @alice()
        @alice(None)
        @alice("Personal Assistant")
        """

        # print(f'Call InterviewDecorator> {self.name!r} with {callable_or_role!r}', file=sys.stderr)
        if callable(callable_or_role):
            return callable_or_role

        role_type = callable_or_role
        def decorator(cls):
            if role_type is None: # Note: This could possibly check for empty string, or only whitespace, etc.
                return cls

            self._ensure_roles(cls)
            if cls._roles[self.name]['type'] is not None:
                raise ValueError(f"{self.name} role is {cls._roles[self.name]['type']!r}. Cannot set to {role_type!r}.")
            cls._roles[self.name]['type'] = role_type
            return cls
        return decorator
    
    def trait(self, description):
        """Makes @alice.trait("...") work"""
        def decorator(cls):
            self._ensure_roles(cls)
            cls._roles[self.name]['traits'].append(description)
            return cls
        return decorator

class FieldSpecificationDecorator:
    """Decorator for specifying information about fields in an Interview class."""

    def __init__(self, name: str):
        self.name = name

        # TODO: It is not possible to populate the "title" field of the tools schema for the LLM.
        # It would be nice to pass a value or use a docstring or something.
    
    def __call__(self, description: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            if not hasattr(func, '_chatfield'):
                func._chatfield = {}
            if 'specs' not in func._chatfield:
                func._chatfield['specs'] = {}
            if self.name not in func._chatfield['specs']:
                func._chatfield['specs'][self.name] = []
            func._chatfield['specs'][self.name].append(description)
            return func
        return decorator

class FieldCastDecorator:
    """
    Decorator for specifying "casts" i.e. re-castings or transformations of valid field values.

    Initialization arguments:
    - name: Name of the cast (e.g. 'as_int')
    - primitive_type: The type to cast the value to (e.g. int, float, list)
    - prompt: Default prompt for the cast, if needed
    """

    # TODO: Something nice would be if used as @as_whatever then that is the field for the LLM tool call.
    # But if the user customizes the prompt, that field name for the tool call should be as_whatever_custom
    
    def __init__(self, name:str, primitive_type: Type[T], prompt: str):
        self.name = name
        self.prompt = prompt
        self.primitive_type = primitive_type

        ok_primitive_types = (int, float, str, bool)
        if primitive_type not in ok_primitive_types:
            raise ValueError(f"Bad primitive type: {primitive_type!r}; must be one of {ok_primitive_types!r}")
    
    def __call__(self, callable_or_prompt: Union[Callable, str]) -> Callable:
        # print(f'FieldCastDecorator> {self.name!r} with prompt {callable_or_prompt!r}', file=sys.stderr)
        if callable(callable_or_prompt):
            target = callable_or_prompt
            override_prompt = None
        else:
            override_prompt = callable_or_prompt
            target = None

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, '_chatfield'):
                func._chatfield = {}
            if 'casts' not in func._chatfield:
                func._chatfield['casts'] = {}
            if self.name in func._chatfield['casts']:
                raise ValueError(f"Field {self.name!r} already has a cast defined: {func._chatfield['casts'][self.name]!r}. Cannot redefine it.")
            
            func._chatfield['casts'][self.name] = {
                'type': self.primitive_type.__name__,
                'prompt': override_prompt or self.prompt,
            }

            return func

        return decorator(target) if target else decorator


alice = InterviewDecorator('alice')
bob = InterviewDecorator('bob')

hint = FieldSpecificationDecorator('hint')
must = FieldSpecificationDecorator('must')
reject = FieldSpecificationDecorator('reject')

as_int = FieldCastDecorator('as_int', int, 'handle words like "five", abbreviations like "2.5k"')
as_bool = FieldCastDecorator('as_bool', bool, 'handle true/false, yes/no, 1/0, falsy, or the most suitable interpretation')
as_float = FieldCastDecorator('as_float', float, 'handle phrases e.g. "five point five", mathematical constants, or the most suitable interpretation')