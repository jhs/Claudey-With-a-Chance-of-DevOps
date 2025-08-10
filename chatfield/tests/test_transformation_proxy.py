"""Tests for field proxy transformation access functionality."""

import pytest
from chatfield.field_proxy import FieldValueProxy
from chatfield.socrates import FieldMeta, SocratesInstance, process_socrates_class
from chatfield import Dialogue
from chatfield.types import as_int, as_float, as_percent, as_list, as_dict
from chatfield.match import match


class TestTransformationProxy:
    """Test suite for accessing transformations through field proxy."""
    
    def test_field_proxy_string_evaluation(self):
        """Test that field proxy evaluates as raw string value."""
        field_meta = FieldMeta(name="budget", description="Your budget")
        proxy = FieldValueProxy("One hundred US Dollars", field_meta)
        
        # Direct string conversion
        assert str(proxy) == "One hundred US Dollars"
        
        # String equality
        assert proxy == "One hundred US Dollars"
        
        # Length
        assert len(proxy) == len("One hundred US Dollars")
        
        # Boolean evaluation
        assert bool(proxy) is True
        
        # Access to raw value
        assert proxy.value == "One hundred US Dollars"
    
    def test_transformation_access_as_int(self):
        """Test accessing as_int transformation through proxy."""
        field_meta = FieldMeta(name="age", description="Your age")
        field_meta.transformations = {"as_int": {"description": "Convert to integer"}}
        
        transformations = {"as_int": 25}
        proxy = FieldValueProxy("twenty-five", field_meta, transformations=transformations)
        
        # Raw value access
        assert str(proxy) == "twenty-five"
        
        # Transformation access
        assert proxy.as_int == 25
    
    def test_transformation_access_as_float(self):
        """Test accessing as_float transformation through proxy."""
        field_meta = FieldMeta(name="height", description="Your height")
        field_meta.transformations = {"as_float": {"description": "Convert to float"}}
        
        transformations = {"as_float": 5.5}
        proxy = FieldValueProxy("five and a half feet", field_meta, transformations=transformations)
        
        assert str(proxy) == "five and a half feet"
        assert proxy.as_float == 5.5
    
    def test_transformation_access_as_percent(self):
        """Test accessing as_percent transformation through proxy."""
        field_meta = FieldMeta(name="confidence", description="How confident")
        field_meta.transformations = {"as_percent": {"description": "Convert to percent"}}
        
        transformations = {"as_percent": 0.75}
        proxy = FieldValueProxy("seventy-five percent", field_meta, transformations=transformations)
        
        assert str(proxy) == "seventy-five percent"
        assert proxy.as_percent == 0.75
    
    def test_transformation_access_as_list(self):
        """Test accessing as_list transformation through proxy."""
        field_meta = FieldMeta(name="items", description="List items")
        field_meta.transformations = {"as_list": {"description": "Parse as list"}}
        
        transformations = {"as_list": ["apple", "banana", "orange"]}
        proxy = FieldValueProxy("apple, banana, and orange", field_meta, transformations=transformations)
        
        assert str(proxy) == "apple, banana, and orange"
        assert proxy.as_list == ["apple", "banana", "orange"]
    
    def test_transformation_access_as_dict(self):
        """Test accessing as_dict transformation through proxy."""
        field_meta = FieldMeta(name="info", description="Your info")
        field_meta.transformations = {"as_dict": {"description": "Parse as dict"}}
        
        transformations = {"as_dict": {"name": "John", "age": "30"}}
        proxy = FieldValueProxy("John, 30 years old", field_meta, transformations=transformations)
        
        assert str(proxy) == "John, 30 years old"
        assert proxy.as_dict == {"name": "John", "age": "30"}
    
    def test_multiple_transformations(self):
        """Test multiple transformations on same field."""
        field_meta = FieldMeta(name="budget", description="Budget")
        field_meta.transformations = {
            "as_int": {"description": "Convert to integer"},
            "as_float": {"description": "Convert to float"},
            "as_percent": {"description": "Convert to percent"}
        }
        
        transformations = {
            "as_int": 100,
            "as_float": 100.0,
            "as_percent": 0.0001  # As percentage of million
        }
        proxy = FieldValueProxy("one hundred dollars", field_meta, transformations=transformations)
        
        # All transformations accessible
        assert str(proxy) == "one hundred dollars"
        assert proxy.as_int == 100
        assert proxy.as_float == 100.0
        assert proxy.as_percent == 0.0001
    
    def test_transformation_not_evaluated_returns_none(self):
        """Test that transformations defined but not evaluated return None."""
        field_meta = FieldMeta(name="age", description="Your age")
        field_meta.transformations = {"as_int": {"description": "Convert to integer"}}
        
        # No transformation results provided
        proxy = FieldValueProxy("twenty-five", field_meta)
        
        assert str(proxy) == "twenty-five"
        assert proxy.as_int is None  # Defined but not evaluated
    
    def test_undefined_transformation_raises_error(self):
        """Test that accessing undefined transformation raises AttributeError."""
        field_meta = FieldMeta(name="name", description="Your name")
        proxy = FieldValueProxy("John Doe", field_meta)
        
        with pytest.raises(AttributeError) as exc_info:
            _ = proxy.as_int
        
        assert "has no transformation 'as_int'" in str(exc_info.value)
    
    def test_match_rules_still_work(self):
        """Test that match rules still work alongside transformations."""
        field_meta = FieldMeta(name="purpose", description="Purpose")
        field_meta.match_rules = {"is_personal": {"criteria": "personal use"}}
        field_meta.transformations = {"as_list": {"description": "Parse as list"}}
        
        evaluations = {"is_personal": True}
        transformations = {"as_list": ["hobby", "learning"]}
        proxy = FieldValueProxy("hobby and learning", field_meta, evaluations, transformations)
        
        # Both match and transformation work
        assert str(proxy) == "hobby and learning"
        assert proxy.is_personal is True
        assert proxy.as_list == ["hobby", "learning"]
    
    def test_socrates_instance_with_transformations(self):
        """Test SocratesInstance integration with transformations."""
        class TestForm(Dialogue):
            """Test form"""
            
            @as_int
            @as_float
            def age():
                """Your age"""
                pass
            
            @as_list()
            def hobbies():
                """Your hobbies"""
                pass
        
        meta = process_socrates_class(TestForm)
        
        # Verify transformations are extracted
        assert "as_int" in meta.fields["age"].transformations
        assert "as_float" in meta.fields["age"].transformations
        assert "as_list" in meta.fields["hobbies"].transformations
        
        # Create instance with transformation results
        transformations = {
            "age": {"as_int": 30, "as_float": 30.0},
            "hobbies": {"as_list": ["reading", "gaming"]}
        }
        
        instance = SocratesInstance(
            meta,
            {"age": "thirty", "hobbies": "reading and gaming"},
            transformations=transformations
        )
        
        # Access raw values
        assert str(instance.age) == "thirty"
        assert str(instance.hobbies) == "reading and gaming"
        
        # Access transformations
        assert instance.age.as_int == 30
        assert instance.age.as_float == 30.0
        assert instance.hobbies.as_list == ["reading", "gaming"]
    
    def test_none_field_with_transformations(self):
        """Test that uncollected fields return None even with transformations defined."""
        class TestForm(Dialogue):
            """Test form"""
            
            @as_int
            def age():
                """Your age"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {})  # No data collected
        
        # Field with transformations is still None when not collected
        assert instance.age is None
    
    def test_empty_string_with_transformations(self):
        """Test empty string field with transformations."""
        field_meta = FieldMeta(name="notes", description="Notes")
        field_meta.transformations = {"as_list": {"description": "Parse as list"}}
        
        transformations = {"as_list": []}  # Empty list for empty string
        proxy = FieldValueProxy("", field_meta, transformations=transformations)
        
        # Empty string is valid
        assert str(proxy) == ""
        assert proxy.as_list == []
        assert bool(proxy) is False  # Empty string evaluates to False
    
    def test_transformation_and_match_combined(self):
        """Test that match rules and transformations work together from decorators."""
        class TestForm(Dialogue):
            """Test form"""
            
            @as_int
            @as_percent
            @match.is_large("greater than 1000")
            def budget():
                """Your budget"""
                pass
        
        meta = process_socrates_class(TestForm)
        
        # Both transformations and match rules extracted
        assert "as_int" in meta.fields["budget"].transformations
        assert "as_percent" in meta.fields["budget"].transformations
        assert "is_large" in meta.fields["budget"].match_rules
        
        # Create instance with both evaluations and transformations
        instance = SocratesInstance(
            meta,
            {"budget": "fifty thousand dollars"},
            match_evaluations={"budget": {"is_large": True}},
            transformations={"budget": {"as_int": 50000, "as_percent": 0.05}}
        )
        
        # All accessible through proxy
        assert str(instance.budget) == "fifty thousand dollars"
        assert instance.budget.as_int == 50000
        assert instance.budget.as_percent == 0.05
        assert instance.budget.is_large is True
    
    def test_field_proxy_preserves_whitespace(self):
        """Test that field proxy preserves whitespace in values."""
        field_meta = FieldMeta(name="code", description="Code snippet")
        proxy = FieldValueProxy("  def hello():\n    print('hi')  ", field_meta)
        
        assert str(proxy) == "  def hello():\n    print('hi')  "
        assert len(proxy) == len("  def hello():\n    print('hi')  ")


class TestFieldProxyEdgeCases:
    """Test edge cases for field proxy behavior."""
    
    def test_proxy_with_none_transformations(self):
        """Test proxy works with None transformations dict."""
        field_meta = FieldMeta(name="test", description="Test")
        proxy = FieldValueProxy("value", field_meta, None, None)
        
        assert str(proxy) == "value"
    
    def test_proxy_equality_with_other_proxy(self):
        """Test proxy equality with another proxy."""
        field_meta = FieldMeta(name="test", description="Test")
        proxy1 = FieldValueProxy("value", field_meta)
        proxy2 = FieldValueProxy("value", field_meta)
        proxy3 = FieldValueProxy("other", field_meta)
        
        assert proxy1 == proxy2
        assert proxy1 != proxy3
    
    def test_proxy_repr(self):
        """Test proxy string representation."""
        field_meta = FieldMeta(name="test_field", description="Test")
        proxy = FieldValueProxy("short value", field_meta)
        
        repr_str = repr(proxy)
        assert "FieldValueProxy" in repr_str
        assert "test_field" in repr_str
        assert "short value" in repr_str
        
        # Test with long value
        long_value = "x" * 100
        proxy_long = FieldValueProxy(long_value, field_meta)
        repr_long = repr(proxy_long)
        assert "..." in repr_long  # Should truncate