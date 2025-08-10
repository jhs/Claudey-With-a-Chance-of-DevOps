"""Tests for type transformation decorators."""

import pytest
from chatfield.types import (
    as_int, as_float, as_percent,
    as_list, as_set, as_dict,
    as_choice, as_choose_one, as_choose_many,
    as_date, as_duration, as_timezone,
    get_field_transformations, build_transformation_prompt
)


class TestNumericDecorators:
    """Test numeric type transformation decorators."""
    
    def test_as_int_decorator(self):
        """Test @as_int decorator adds transformation."""
        @as_int
        def age(): 
            return "Your age"
        
        transformations = get_field_transformations(age)
        assert 'as_int' in transformations
        assert 'Convert to integer' in transformations['as_int']['description']
    
    def test_as_float_decorator(self):
        """Test @as_float decorator."""
        @as_float
        def height(): 
            return "Your height in meters"
        
        transformations = get_field_transformations(height)
        assert 'as_float' in transformations
        assert 'decimal number' in transformations['as_float']['description']
    
    def test_as_percent_decorator(self):
        """Test @as_percent decorator."""
        @as_percent
        def confidence(): 
            return "How confident are you?"
        
        transformations = get_field_transformations(confidence)
        assert 'as_percent' in transformations
        assert 'between 0 and 1' in transformations['as_percent']['description']
    
    def test_multiple_numeric_decorators(self):
        """Test multiple numeric decorators on same field."""
        @as_int
        @as_float
        @as_percent
        def value(): 
            return "Enter a value"
        
        transformations = get_field_transformations(value)
        assert len(transformations) == 3
        assert 'as_int' in transformations
        assert 'as_float' in transformations
        assert 'as_percent' in transformations


class TestCollectionDecorators:
    """Test collection type transformation decorators."""
    
    def test_as_list_default(self):
        """Test @as_list with default Any type."""
        @as_list()
        def items(): 
            return "List your items"
        
        transformations = get_field_transformations(items)
        assert 'as_list' in transformations
        assert transformations['as_list']['item_type'] == 'Any'
    
    def test_as_list_with_type(self):
        """Test @as_list with specific type."""
        @as_list(of=int)
        def numbers(): 
            return "Enter numbers"
        
        transformations = get_field_transformations(numbers)
        assert 'as_list' in transformations
        assert transformations['as_list']['item_type'] == 'int'
    
    def test_as_set_decorator(self):
        """Test @as_set decorator."""
        @as_set
        def tags(): 
            return "Enter tags"
        
        transformations = get_field_transformations(tags)
        assert 'as_set' in transformations
        assert 'unique values' in transformations['as_set']['description']
    
    def test_as_dict_decorator(self):
        """Test @as_dict decorator."""
        @as_dict("name", "email", "age")
        def info(): 
            return "Your information"
        
        transformations = get_field_transformations(info)
        assert 'as_dict' in transformations
        assert transformations['as_dict']['keys'] == ["name", "email", "age"]
    
    def test_as_dict_no_keys_raises(self):
        """Test @as_dict without keys raises error."""
        with pytest.raises(ValueError, match="requires at least one key"):
            @as_dict()
            def info(): 
                return "Your info"


class TestChoiceDecorators:
    """Test choice selection decorators."""
    
    def test_as_choice_basic(self):
        """Test basic @as_choice decorator."""
        @as_choice("small", "medium", "large")
        def size(): 
            return "Pick a size"
        
        transformations = get_field_transformations(size)
        assert 'as_choice' in transformations
        assert transformations['as_choice']['choices'] == ["small", "medium", "large"]
        assert transformations['as_choice']['mandatory'] is False
        assert transformations['as_choice']['allow_multiple'] is False
    
    def test_as_choice_with_options(self):
        """Test @as_choice with options."""
        @as_choice("red", "blue", "green", mandatory=True, allow_multiple=True)
        def colors(): 
            return "Pick colors"
        
        transformations = get_field_transformations(colors)
        assert transformations['as_choice']['mandatory'] is True
        assert transformations['as_choice']['allow_multiple'] is True
    
    def test_as_choose_one_wrapper(self):
        """Test @as_choose_one convenience wrapper."""
        @as_choose_one("yes", "no", mandatory=True)
        def confirm(): 
            return "Confirm?"
        
        transformations = get_field_transformations(confirm)
        assert 'as_choice' in transformations
        assert transformations['as_choice']['allow_multiple'] is False
        assert transformations['as_choice']['mandatory'] is True
    
    def test_as_choose_many_wrapper(self):
        """Test @as_choose_many convenience wrapper."""
        @as_choose_many("python", "javascript", "rust")
        def languages(): 
            return "Programming languages?"
        
        transformations = get_field_transformations(languages)
        assert 'as_choice' in transformations
        assert transformations['as_choice']['allow_multiple'] is True
    
    def test_as_choice_no_choices_raises(self):
        """Test @as_choice without choices raises error."""
        with pytest.raises(ValueError, match="requires at least one choice"):
            @as_choice()
            def pick(): 
                return "Pick something"


class TestTimeDateDecorators:
    """Test time and date transformation decorators."""
    
    def test_as_date_default(self):
        """Test @as_date with default ISO format."""
        @as_date()
        def birthday(): 
            return "Your birthday"
        
        transformations = get_field_transformations(birthday)
        assert 'as_date' in transformations
        assert transformations['as_date']['format'] == "ISO"
    
    def test_as_date_custom_format(self):
        """Test @as_date with custom format."""
        @as_date(format="US")
        def start_date(): 
            return "Start date"
        
        transformations = get_field_transformations(start_date)
        assert transformations['as_date']['format'] == "US"
    
    def test_as_duration_default(self):
        """Test @as_duration with default seconds."""
        @as_duration()
        def time_spent(): 
            return "Time spent"
        
        transformations = get_field_transformations(time_spent)
        assert 'as_duration' in transformations
        assert transformations['as_duration']['unit'] == "seconds"
    
    def test_as_duration_custom_unit(self):
        """Test @as_duration with custom unit."""
        @as_duration(unit="hours")
        def work_hours(): 
            return "Hours worked"
        
        transformations = get_field_transformations(work_hours)
        assert transformations['as_duration']['unit'] == "hours"
    
    def test_as_duration_invalid_unit_raises(self):
        """Test @as_duration with invalid unit raises error."""
        with pytest.raises(ValueError, match="unit must be one of"):
            @as_duration(unit="fortnights")
            def time(): 
                return "Time"
    
    def test_as_timezone_decorator(self):
        """Test @as_timezone decorator."""
        @as_timezone
        def tz(): 
            return "Your timezone"
        
        transformations = get_field_transformations(tz)
        assert 'as_timezone' in transformations
        assert 'IANA timezone' in transformations['as_timezone']['description']


class TestCombinedDecorators:
    """Test combining multiple decorator types."""
    
    def test_combine_different_types(self):
        """Test combining different transformation types."""
        @as_int
        @as_list(of=str)
        @as_choice("low", "medium", "high")
        def mixed_field(): 
            return "Enter value"
        
        transformations = get_field_transformations(mixed_field)
        assert len(transformations) == 3
        assert 'as_int' in transformations
        assert 'as_list' in transformations
        assert 'as_choice' in transformations
    
    def test_duplicate_decorator_raises(self):
        """Test duplicate decorator type raises error."""
        with pytest.raises(ValueError, match="Duplicate transformation"):
            @as_int
            @as_int  # Duplicate!
            def value(): 
                return "Value"


class TestPromptBuilder:
    """Test the prompt building functionality."""
    
    def test_build_empty_transformations(self):
        """Test building prompt with no transformations."""
        prompt = build_transformation_prompt(
            "age", "Your age", "25", {}
        )
        assert prompt == ""
    
    def test_build_single_transformation(self):
        """Test building prompt with single transformation."""
        transformations = {
            'as_int': {
                'description': 'Convert to integer'
            }
        }
        prompt = build_transformation_prompt(
            "age", "Your age", "twenty-five", transformations
        )
        
        assert "Your age" in prompt
        assert "twenty-five" in prompt
        assert "as_int: Convert to integer" in prompt
        assert '"as_int":' in prompt
    
    def test_build_multiple_transformations(self):
        """Test building prompt with multiple transformations."""
        transformations = {
            'as_int': {'description': 'Convert to integer'},
            'as_float': {'description': 'Convert to float'},
            'is_adult': {'description': 'Check if 18 or older', 'type': 'match'}
        }
        prompt = build_transformation_prompt(
            "age", "Your age", "25 years old", transformations
        )
        
        assert "Your age" in prompt
        assert "25 years old" in prompt
        assert "as_int:" in prompt
        assert "as_float:" in prompt
        assert "is_adult:" in prompt
        assert "Return as JSON" in prompt
    
    def test_build_complex_transformation_prompt(self):
        """Test building prompt with complex transformations."""
        transformations = {
            'as_list': {
                'description': 'Parse as list',
                'item_type': 'str'
            },
            'as_choice': {
                'description': 'Select from: A, B, C',
                'choices': ['A', 'B', 'C'],
                'allow_multiple': True
            }
        }
        prompt = build_transformation_prompt(
            "options", "Select options", "I want A and B", transformations
        )
        
        assert "Select options" in prompt
        assert "I want A and B" in prompt
        assert "as_list:" in prompt
        assert "as_choice:" in prompt
        assert '"as_list":' in prompt
        assert '"as_choice":' in prompt


class TestIntegrationWithMatch:
    """Test integration with existing @match decorator."""
    
    def test_match_alongside_types(self):
        """Test @match works alongside type decorators."""
        from chatfield.match import match
        
        @as_int
        @match.is_large("greater than 1000")
        @match.is_round("divisible by 100")
        def amount(): 
            return "Enter amount"
        
        # Check both transformation systems have the data
        transformations = get_field_transformations(amount)
        assert 'as_int' in transformations
        assert 'is_large' in transformations
        assert 'is_round' in transformations
        
        # Check match rules are also preserved
        assert hasattr(amount, '_chatfield_match_rules')
        match_rules = amount._chatfield_match_rules
        assert 'is_large' in match_rules
        assert 'is_round' in match_rules