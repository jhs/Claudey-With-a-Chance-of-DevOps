"""Type transformation decorators for Chatfield.

These decorators work as siblings to @match, each requesting a specific
transformation or evaluation from the LLM. All decorators on a field
are processed in a single LLM call for efficiency.
"""

# Choice Selection Decorators

def as_choice(*choices: str, mandatory: bool = False, allow_multiple: bool = False) -> Callable:
    """Select from provided choices.
    
    Args:
        *choices: Available options to choose from
        mandatory: If False (default), can return None if no match
        allow_multiple: If True, can select multiple choices
    
    Examples:
        @as_choice("small", "medium", "large")
        "I need a medium one" -> "medium"
        
        @as_choice("red", "blue", "green", allow_multiple=True)
        "red and blue" -> ["red", "blue"]
    """
    def decorator(func: Callable) -> Callable:
        if not choices:
            raise ValueError("as_choice requires at least one choice")
        
        decorator_obj = TypeDecorator(
            'as_choice',
            f'Select from choices: {", ".join(choices)}' +
            (f' ({"required" if mandatory else "optional"}, '
             f'{"multiple allowed" if allow_multiple else "single choice"})'),
            choices=list(choices),
            mandatory=mandatory,
            allow_multiple=allow_multiple
        )
        return decorator_obj(func)
    
    return decorator


def as_choose_one(*choices: str, mandatory: bool = True) -> Callable:
    """Select exactly one from provided choices.
    
    Convenience wrapper for as_choice with allow_multiple=False.
    
    Args:
        *choices: Available options to choose from
        mandatory: If False, can return None if no match
    """
    return as_choice(*choices, mandatory=mandatory, allow_multiple=False)


def as_choose_many(*choices: str, mandatory: bool = True) -> Callable:
    """Select multiple from provided choices.
    
    Convenience wrapper for as_choice with allow_multiple=True.
    
    Args:
        *choices: Available options to choose from  
        mandatory: If False, can return empty list
    """
    return as_choice(*choices, mandatory=mandatory, allow_multiple=True)


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
        'as_choice': '"selected_choice"',
        'as_date': '"2024-01-15"',
        'as_duration': '7200',
        'as_timezone': '"America/New_York"',
        'as_lang': '"<content in specified language>"'
    }
    
    for name in transformations:
        example = example_values.get(name, '...')
        prompt_parts.append(f'  "{name}": {example},')
    
    # Remove trailing comma and close
    if prompt_parts[-1].endswith(','):
        prompt_parts[-1] = prompt_parts[-1][:-1]
    prompt_parts.append("}")
    
    return "\n".join(prompt_parts)