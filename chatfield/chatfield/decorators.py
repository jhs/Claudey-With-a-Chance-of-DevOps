"""Core decorators for Chatfield."""

from typing import Any, Callable, TypeVar, Type, Optional, Union

from regex import F

from .interview import Interview

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
        return cls._ensure_roles()
    
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
            # if role_type is None: # Note: This could possibly check for empty string, or only whitespace, etc.
            if not role_type:
                return cls

            self._ensure_roles(cls)
            if cls._chatfield_roles[self.name]['type'] is not None:
                raise ValueError(f"{self.name} role is {cls._chatfield_roles[self.name]['type']!r}. Cannot set to {role_type!r}.")
            cls._chatfield_roles[self.name]['type'] = role_type
            return cls
        return decorator
    
    def trait(self, description):
        """Makes @alice.trait("...") work"""
        def decorator(cls):
            if not description:
                return cls

            self._ensure_roles(cls)
            if description not in cls._chatfield_roles[self.name]['traits']:
                cls._chatfield_roles[self.name]['traits'].append(description)
            return cls
        return decorator

class FieldSpecificationDecorator:
    """Decorator for specifying information about fields in an Interview class."""

    def __init__(self, category: str):
        self.category = category

        # TODO: It is not possible to populate the "title" field of the tools schema for the LLM.
        # It would be nice to pass a value or use a docstring or something.
    
    def __call__(self, description: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            Interview._init_field(func)
            if self.category not in func._chatfield['specs']:
                func._chatfield['specs'][self.category] = []
            if description not in func._chatfield['specs'][self.category]:
                func._chatfield['specs'][self.category].append(description)
            return func
        return decorator

class FieldCastDecorator:
    """
    Decorator for specifying "casts" i.e. re-castings or transformations of valid field values.

    Initialization arguments:
    - name: Name of the cast (e.g. 'as_int')
    - primitive_type: The type to cast the value to (e.g. int, float, list)
    - prompt: Default prompt for the cast, if needed
    - sub_only: If True, this decorator can only be used with sub-attributes (e.g., @as_lang.fr)
    """
    
    def __init__(self, name:str, primitive_type: Type[T], prompt: str, sub_only:bool = False):
        self.name = name
        self.prompt = prompt
        self.sub_only = sub_only
        self.primitive_type = primitive_type

        ok_primitive_types = (int, float, str, bool, list, set, dict)
        if primitive_type not in ok_primitive_types:
            raise ValueError(f"Bad primitive type: {primitive_type!r}; must be one of {ok_primitive_types!r}")

    def __call__(self, callable_or_prompt: Union[Callable, str]) -> Callable:
        if callable(callable_or_prompt):
            # Direct decoration: @as_bool or @as_bool.something
            target = callable_or_prompt
            override_prompt = None
        else:
            # With custom prompt: @as_bool("custom prompt") or @as_bool.something("custom prompt")
            target = None
            override_prompt = callable_or_prompt

        def decorator(func: Callable) -> Callable:
            Interview._init_field(func)
            type_name = self.primitive_type.__name__
            chatfield = func._chatfield

            # Check if this is a sub_only decorator being used directly
            if self.sub_only:
                raise ValueError(f"Decorator {self.name!r} can only be used with sub-attributes (e.g., @{self.name}.something)")

            # Check for duplicate cast definition
            if self.name in chatfield['casts']:
                raise ValueError(f"Field {self.name!r} already has a cast defined: {chatfield['casts'][self.name]!r}. Cannot redefine it.")

            # Add the cast with either the override prompt or the default prompt
            chatfield['casts'][self.name] = {
                'type': type_name,
                'prompt': override_prompt or self.prompt,
            }
            return func

        return decorator(target) if target else decorator
    
    def __getattr__(self, name: str):
        """Allow chaining like @as_int.some_other_method
        
        This creates a new FieldCastDecorator instance with a compound name.
        For example: @as_bool.spelling creates a new decorator with name 'as_bool_spelling'
        """
        if name.startswith('_'):
            raise AttributeError(f"{self.name} has no attribute: {name!r}")
        
        # Create a new decorator instance with a compound name
        compound_name = f'{self.name}_{name}'
        
        # Format the prompt if it contains {sub_name} placeholder
        compound_prompt = self.prompt.format(name=name)
        
        # Return a new FieldCastDecorator instance, never marked as sub_only
        return FieldCastDecorator(
            name=compound_name,
            primitive_type=self.primitive_type,
            prompt=compound_prompt,
            sub_only=False  # The new instance is not sub_only
        )

alice = InterviewDecorator('alice')
bob = InterviewDecorator('bob')

hint = FieldSpecificationDecorator('hint')
must = FieldSpecificationDecorator('must')
reject = FieldSpecificationDecorator('reject')

as_int = FieldCastDecorator('as_int', int, 'handle words like "five", abbreviations like "2.5k"')
as_bool = FieldCastDecorator('as_bool', bool, 'handle true/false, yes/no, 1/0, falsy, or the most suitable interpretation')
as_float = FieldCastDecorator('as_float', float, 'handle phrases e.g. "five point five", mathematical constants, or the most suitable interpretation')

as_percent = FieldCastDecorator('as_percent', float, 'handle "50%" or "half", etc. converted to the range 0.0 to 1.0')

as_set = FieldCastDecorator('as_set', set, 'interpret as a set of distinct items, in the most suitable way')
# TODO: Possibly allow a kwwarg @as_list(of=int) which would need to appear in the tool argument schema.
as_list = FieldCastDecorator('as_list', list, 'interpret as a list or array of items, in the most suitable way')

# TODO This is not working. For some reason the LLM always omits the "as_obj" field despite it being listed as required.
as_obj = FieldCastDecorator('as_obj', dict, 'represent as zero or more key-value pairs')
as_dict = as_obj

# TODO: I though if the language matches the standard name like "fr" or "fr_CA" then tell the LLM that.
as_lang = FieldCastDecorator('as_lang', str, 'represent as words and translate into to the language: {name}', sub_only=True)