"""Type transformation decorators for Chatfield.

These decorators work as siblings to @match, each requesting a specific
transformation or evaluation from the LLM. All decorators on a field
are processed in a single LLM call for efficiency.
"""

from typing import Callable, Any, Optional, Type, List, Union
from datetime import datetime


class TypeDecorator:
    """Base class for type transformation decorators.
    
    Each decorator stores its transformation request on the field,
    and all are processed together in a single LLM call.
    """
    
    def __init__(self, name: str, description: str, **kwargs):
        self.name = name
        self.description = description
        self.kwargs = kwargs
    
    def __call__(self, func: Callable) -> Callable:
        """Apply this transformation request to the field."""
        # Initialize transformations dict if needed
        if not hasattr(func, '_chatfield_transformations'):
            func._chatfield_transformations = {}
        
        # Check for duplicate transformation name
        if self.name in func._chatfield_transformations:
            raise ValueError(
                f"Duplicate transformation '{self.name}' on field. "
                f"Each transformation type can only be applied once per field."
            )
        
        # Store the transformation request
        func._chatfield_transformations[self.name] = {
            'description': self.description,
            **self.kwargs
        }
        
        return func


# Numeric Type Transformations

def as_int(func: Callable) -> Callable:
    """Transform the field value to an integer.
    
    Examples:
        "five" -> 5
        "about 100" -> 100
        "2.5k" -> 2500
    """
    decorator = TypeDecorator(
        'as_int',
        'Convert to integer (handle words like "five", abbreviations like "2.5k")'
    )
    return decorator(func)


def as_float(func: Callable) -> Callable:
    """Transform the field value to a floating-point number.
    
    Examples:
        "three and a half" -> 3.5
        "about 99.9" -> 99.9
        "1.5 million" -> 1500000.0
    """
    decorator = TypeDecorator(
        'as_float',
        'Convert to decimal number (handle words, fractions, abbreviations)'
    )
    return decorator(func)


def as_percent(func: Callable) -> Callable:
    """Transform the field value to a percentage (0-1 scale).
    
    Examples:
        "50%" -> 0.5
        "half" -> 0.5
        "three quarters" -> 0.75
        "90 percent" -> 0.9
    """
    decorator = TypeDecorator(
        'as_percent',
        'Convert to percentage as decimal between 0 and 1'
    )
    return decorator(func)


# Collection Type Transformations

def as_list(of: Type = Any) -> Callable:
    """Transform the field value to a list of specified type.
    
    Args:
        of: The type of items in the list (default: Any)
    
    Examples:
        "apples, oranges, and bananas" -> ["apples", "oranges", "bananas"]
        "1, 2, 3" with of=int -> [1, 2, 3]
    """
    def decorator(func: Callable) -> Callable:
        type_name = of.__name__ if hasattr(of, '__name__') else str(of)
        type_hint = f" as {type_name}" if of != Any else ""
        
        decorator_obj = TypeDecorator(
            'as_list',
            f'Parse as a list of items{type_hint}',
            item_type=type_name
        )
        return decorator_obj(func)
    
    return decorator


def as_set(func: Callable) -> Callable:
    """Transform the field value to a set of unique values.
    
    Examples:
        "red, blue, red, green" -> {"red", "blue", "green"}
        "apple, Apple, APPLE" -> {"apple"}  # normalized
    """
    decorator = TypeDecorator(
        'as_set',
        'Parse as unique values only (remove duplicates, normalize case)'
    )
    return decorator(func)


def as_dict(*keys: str) -> Callable:
    """Transform the field value to a dictionary with specified keys.
    
    Args:
        *keys: The keys to extract from the response
    
    Examples:
        @as_dict("name", "age", "email")
        "John, 30 years old, john@example.com" -> 
        {"name": "John", "age": "30", "email": "john@example.com"}
    """
    def decorator(func: Callable) -> Callable:
        if not keys:
            raise ValueError("as_dict requires at least one key")
        
        decorator_obj = TypeDecorator(
            'as_dict',
            f'Extract key-value pairs for: {", ".join(keys)}',
            keys=list(keys)
        )
        return decorator_obj(func)
    
    return decorator


# Choice Selection Decorators

def choose(*choices: str, mandatory: bool = False, allow_multiple: bool = False) -> Callable:
    """Select from provided choices.
    
    Args:
        *choices: Available options to choose from
        mandatory: If False (default), can return None if no match
        allow_multiple: If True, can select multiple choices
    
    Examples:
        @choose("small", "medium", "large")
        "I need a medium one" -> "medium"
        
        @choose("red", "blue", "green", allow_multiple=True)
        "red and blue" -> ["red", "blue"]
    """
    def decorator(func: Callable) -> Callable:
        if not choices:
            raise ValueError("choose requires at least one choice")
        
        decorator_obj = TypeDecorator(
            'choose',
            f'Select from choices: {", ".join(choices)}' +
            (f' ({"required" if mandatory else "optional"}, '
             f'{"multiple allowed" if allow_multiple else "single choice"})'),
            choices=list(choices),
            mandatory=mandatory,
            allow_multiple=allow_multiple
        )
        return decorator_obj(func)
    
    return decorator


def choose_one(*choices: str, mandatory: bool = False) -> Callable:
    """Select exactly one from provided choices.
    
    Convenience wrapper for choose with allow_multiple=False.
    
    Args:
        *choices: Available options to choose from
        mandatory: If False (default), can return None if no match
    """
    return choose(*choices, mandatory=mandatory, allow_multiple=False)


def choose_many(*choices: str, mandatory: bool = False) -> Callable:
    """Select multiple from provided choices.
    
    Convenience wrapper for choose with allow_multiple=True.
    
    Args:
        *choices: Available options to choose from  
        mandatory: If False (default), can return empty list
    """
    return choose(*choices, mandatory=mandatory, allow_multiple=True)


# Time/Date Type Transformations

def as_date(format: str = "ISO") -> Callable:
    """Transform the field value to a date.
    
    Args:
        format: Output format ("ISO", "US", "EU", etc.)
    
    Examples:
        "next Tuesday" -> "2024-01-16"
        "March 15th" -> "2024-03-15"
        "yesterday" -> "2024-01-11"
    """
    def decorator(func: Callable) -> Callable:
        decorator_obj = TypeDecorator(
            'as_date',
            f'Parse as date in {format} format',
            format=format
        )
        return decorator_obj(func)
    
    return decorator


def as_duration(unit: str = "seconds") -> Callable:
    """Transform the field value to a time duration.
    
    Args:
        unit: Output unit ("seconds", "minutes", "hours", "days")
    
    Examples:
        "2 hours" with unit="seconds" -> 7200
        "90 minutes" with unit="hours" -> 1.5
        "a week" with unit="days" -> 7
    """
    def decorator(func: Callable) -> Callable:
        valid_units = ["seconds", "minutes", "hours", "days"]
        if unit not in valid_units:
            raise ValueError(f"unit must be one of {valid_units}")
        
        decorator_obj = TypeDecorator(
            'as_duration',
            f'Convert time duration to {unit}',
            unit=unit
        )
        return decorator_obj(func)
    
    return decorator


def as_timezone(func: Callable) -> Callable:
    """Transform the field value to a timezone identifier.
    
    Examples:
        "Eastern time" -> "America/New_York"
        "PST" -> "America/Los_Angeles"
        "London time" -> "Europe/London"
    """
    decorator = TypeDecorator(
        'as_timezone',
        'Convert to IANA timezone identifier (e.g., America/New_York)'
    )
    return decorator(func)


# Helper function to collect all transformations from a field
def get_field_transformations(field_func: Callable) -> dict:
    """Get all transformation requests from a field.
    
    Args:
        field_func: The field function with decorators applied
        
    Returns:
        Dictionary of transformation names to their configurations
    """
    return getattr(field_func, '_chatfield_transformations', {})


# Helper function to build LLM prompt for all transformations
def build_transformation_prompt(
    field_name: str,
    field_description: str,
    user_response: str,
    transformations: dict
) -> str:
    """Build a single prompt for all transformations on a field.
    
    Args:
        field_name: Name of the field
        field_description: Description of what the field asks
        user_response: The user's raw response
        transformations: Dictionary of transformations to apply
        
    Returns:
        Prompt string for the LLM
    """
    if not transformations:
        return ""
    
    prompt_parts = [
        f'For the field "{field_description}", the user said: "{user_response}"',
        "",
        "Please provide the following transformations:",
    ]
    
    for name, config in transformations.items():
        prompt_parts.append(f"- {name}: {config['description']}")
    
    prompt_parts.extend([
        "",
        "Return as JSON with these exact keys:",
        "{"
    ])
    
    example_values = {
        'as_int': '5000',
        'as_float': '5000.0',
        'as_percent': '0.5',
        'as_list': '["item1", "item2"]',
        'as_set': '["unique1", "unique2"]',
        'as_dict': '{"key1": "value1", "key2": "value2"}',
        'choose': '"selected_choice"',
        'as_date': '"2024-01-15"',
        'as_duration': '7200',
        'as_timezone': '"America/New_York"'
    }
    
    for name in transformations:
        example = example_values.get(name, '...')
        prompt_parts.append(f'  "{name}": {example},')
    
    # Remove trailing comma and close
    if prompt_parts[-1].endswith(','):
        prompt_parts[-1] = prompt_parts[-1][:-1]
    prompt_parts.append("}")
    
    return "\n".join(prompt_parts)