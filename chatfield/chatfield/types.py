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