"""Tests for FieldValueProxy as a str subclass.

This test file specifically tests the string behavior of FieldValueProxy
after it was changed to subclass str instead of being a regular class.
"""

import json
import pytest
from chatfield.field_proxy import FieldValueProxy
from chatfield.socrates import FieldMeta


class TestFieldProxyAsString:
    """Test that FieldValueProxy behaves as a proper string."""
    
    def test_is_instance_of_str(self):
        """Test that proxy is an instance of str."""
        field_meta = FieldMeta(name="test", description="Test field")
        proxy = FieldValueProxy("hello world", field_meta)
        
        assert isinstance(proxy, str)
        assert isinstance(proxy, FieldValueProxy)
    
    def test_string_methods_work(self):
        """Test that all string methods work on the proxy."""
        field_meta = FieldMeta(name="message", description="A message")
        proxy = FieldValueProxy("Hello World", field_meta)
        
        # Case methods
        assert proxy.upper() == "HELLO WORLD"
        assert proxy.lower() == "hello world"
        assert proxy.capitalize() == "Hello world"
        assert proxy.title() == "Hello World"
        assert proxy.swapcase() == "hELLO wORLD"
        
        # Search methods
        assert proxy.startswith("Hello")
        assert proxy.endswith("World")
        assert proxy.find("World") == 6
        assert proxy.index("World") == 6
        assert proxy.count("l") == 3
        
        # Modification methods (return new strings)
        assert proxy.replace("World", "Python") == "Hello Python"
        assert proxy.strip() == "Hello World"
        assert "  Hello World  ".strip() == "Hello World"
        
        # Split/join methods
        assert proxy.split() == ["Hello", "World"]
        assert proxy.split("o") == ["Hell", " W", "rld"]
        assert "-".join(proxy.split()) == "Hello-World"
        
        # Check methods
        assert not proxy.isdigit()
        assert not proxy.isalpha()  # Has space
        assert proxy.isprintable()
        assert not proxy.islower()
        assert not proxy.isupper()
    
    def test_string_concatenation(self):
        """Test that string concatenation works."""
        field_meta = FieldMeta(name="name", description="Name")
        proxy = FieldValueProxy("John", field_meta)
        
        # Different concatenation methods
        assert proxy + " Doe" == "John Doe"
        assert "Hello " + proxy == "Hello John"
        assert proxy * 2 == "JohnJohn"
        
        # Format strings
        assert f"Name: {proxy}" == "Name: John"
        assert "Name: {}".format(proxy) == "Name: John"
        assert "Name: %s" % proxy == "Name: John"
    
    def test_string_comparison(self):
        """Test string comparison operations."""
        field_meta = FieldMeta(name="value", description="Value")
        proxy1 = FieldValueProxy("apple", field_meta)
        proxy2 = FieldValueProxy("banana", field_meta)
        
        # Equality
        assert proxy1 == "apple"
        assert proxy1 != "banana"
        assert proxy1 != proxy2
        
        # Ordering
        assert proxy1 < proxy2  # "apple" < "banana"
        assert proxy1 < "banana"
        assert proxy1 <= "apple"
        assert proxy2 > "apple"
        assert proxy2 >= "banana"
    
    def test_proxy_as_dict_key(self):
        """Test that proxy can be used as a dictionary key."""
        field_meta = FieldMeta(name="id", description="ID")
        proxy = FieldValueProxy("user123", field_meta)
        
        # Use as dict key
        data = {proxy: "value"}
        assert data[proxy] == "value"
        assert data["user123"] == "value"  # String key works too
        
        # Use in set
        items = {proxy, "other"}
        assert proxy in items
        assert "user123" in items
    
    def test_json_serialization(self):
        """Test that proxy serializes properly with JSON."""
        field_meta = FieldMeta(name="data", description="Data")
        proxy = FieldValueProxy("test value", field_meta)
        
        # Direct serialization
        assert json.dumps(proxy) == '"test value"'
        
        # In a data structure
        data = {"field": proxy, "list": [proxy]}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed == {"field": "test value", "list": ["test value"]}
    
    def test_string_slicing(self):
        """Test that string slicing works."""
        field_meta = FieldMeta(name="text", description="Text")
        proxy = FieldValueProxy("Hello World", field_meta)
        
        assert proxy[0] == "H"
        assert proxy[-1] == "d"
        assert proxy[0:5] == "Hello"
        assert proxy[6:] == "World"
        assert proxy[::2] == "HloWrd"
        assert proxy[::-1] == "dlroW olleH"
    
    def test_string_iteration(self):
        """Test that we can iterate over the proxy as a string."""
        field_meta = FieldMeta(name="chars", description="Characters")
        proxy = FieldValueProxy("abc", field_meta)
        
        chars = list(proxy)
        assert chars == ["a", "b", "c"]
        
        # List comprehension
        upper_chars = [c.upper() for c in proxy]
        assert upper_chars == ["A", "B", "C"]
    
    def test_len_and_bool(self):
        """Test len() and bool() work correctly."""
        field_meta = FieldMeta(name="test", description="Test")
        
        proxy_full = FieldValueProxy("content", field_meta)
        assert len(proxy_full) == 7
        assert bool(proxy_full) is True
        
        proxy_empty = FieldValueProxy("", field_meta)
        assert len(proxy_empty) == 0
        assert bool(proxy_empty) is False


class TestFieldProxyCustomFeatures:
    """Test that custom proxy features still work with str subclass."""
    
    def test_transformation_access(self):
        """Test that transformations are still accessible."""
        field_meta = FieldMeta(name="age", description="Age")
        field_meta.transformations = {"as_int": {"description": "As integer"}}
        
        transformations = {"as_int": 25}
        proxy = FieldValueProxy("twenty-five", field_meta, transformations=transformations)
        
        # String behavior
        assert proxy == "twenty-five"
        assert proxy.upper() == "TWENTY-FIVE"
        
        # Transformation still works
        assert proxy.as_int == 25
    
    def test_match_rule_access(self):
        """Test that match rules are still accessible."""
        field_meta = FieldMeta(name="budget", description="Budget")
        field_meta.match_rules = {"is_large": {"criteria": "over 1000"}}
        
        evaluations = {"is_large": True}
        proxy = FieldValueProxy("5000 dollars", field_meta, evaluations=evaluations)
        
        # String behavior
        assert proxy == "5000 dollars"
        assert proxy.replace("dollars", "USD") == "5000 USD"
        
        # Match rule still works
        assert proxy.is_large is True
    
    def test_combined_features(self):
        """Test that string methods work alongside custom features."""
        field_meta = FieldMeta(name="project", description="Project name")
        field_meta.transformations = {"as_list": {"description": "As list"}}
        field_meta.match_rules = {"is_valid": {"criteria": "valid name"}}
        
        transformations = {"as_list": ["My", "Project"]}
        evaluations = {"is_valid": True}
        proxy = FieldValueProxy("My Project", field_meta, evaluations, transformations)
        
        # All features work together
        assert proxy == "My Project"
        assert proxy.upper() == "MY PROJECT"
        assert proxy.as_list == ["My", "Project"]
        assert proxy.is_valid is True
        assert len(proxy) == 10
        assert proxy.startswith("My")
    
    def test_repr_method(self):
        """Test that custom __repr__ still works."""
        field_meta = FieldMeta(name="description", description="Description")
        
        # Short value
        proxy_short = FieldValueProxy("Short text", field_meta)
        repr_str = repr(proxy_short)
        assert "FieldValueProxy" in repr_str
        assert "description" in repr_str
        assert "Short text" in repr_str
        assert "..." not in repr_str
        
        # Long value
        long_text = "x" * 100
        proxy_long = FieldValueProxy(long_text, field_meta)
        repr_long = repr(proxy_long)
        assert "FieldValueProxy" in repr_long
        assert "..." in repr_long
    
    def test_value_property(self):
        """Test that the value property still works."""
        field_meta = FieldMeta(name="content", description="Content")
        proxy = FieldValueProxy("test content", field_meta)
        
        assert proxy.value == "test content"
        assert proxy.value == proxy  # Should be the same
        assert type(proxy.value) == str
    
    def test_undefined_attribute_error(self):
        """Test that accessing undefined attributes raises proper errors."""
        field_meta = FieldMeta(name="field", description="Field")
        proxy = FieldValueProxy("value", field_meta)
        
        # Undefined transformation
        with pytest.raises(AttributeError) as exc:
            _ = proxy.as_undefined
        assert "has no transformation 'as_undefined'" in str(exc.value)
        
        # Undefined match rule
        with pytest.raises(AttributeError) as exc:
            _ = proxy.is_undefined
        assert "has no attribute 'is_undefined'" in str(exc.value)


class TestFieldProxyEdgeCases:
    """Test edge cases with str subclass."""
    
    def test_empty_string_proxy(self):
        """Test proxy with empty string value."""
        field_meta = FieldMeta(name="empty", description="Empty field")
        proxy = FieldValueProxy("", field_meta)
        
        assert proxy == ""
        assert len(proxy) == 0
        assert bool(proxy) is False
        assert proxy.upper() == ""
        assert list(proxy) == []
    
    def test_whitespace_preservation(self):
        """Test that whitespace is preserved."""
        field_meta = FieldMeta(name="code", description="Code")
        code = "  def hello():\n    print('hi')  "
        proxy = FieldValueProxy(code, field_meta)
        
        assert proxy == code
        assert len(proxy) == len(code)
        assert proxy.strip() == "def hello():\n    print('hi')"
        assert proxy.startswith("  ")
        assert proxy.endswith("  ")
    
    def test_unicode_support(self):
        """Test that Unicode strings work correctly."""
        field_meta = FieldMeta(name="text", description="Text")
        proxy = FieldValueProxy("Hello 世界 🌍", field_meta)
        
        assert proxy == "Hello 世界 🌍"
        assert len(proxy) == 10  # Unicode chars count correctly
        assert proxy.upper() == "HELLO 世界 🌍"
        assert "世界" in proxy
    
    def test_proxy_equality_with_proxy(self):
        """Test equality between two proxies."""
        field_meta = FieldMeta(name="test", description="Test")
        proxy1 = FieldValueProxy("same value", field_meta)
        proxy2 = FieldValueProxy("same value", field_meta)
        proxy3 = FieldValueProxy("different", field_meta)
        
        assert proxy1 == proxy2
        assert proxy1 != proxy3
        assert hash(proxy1) == hash(proxy2)  # Can be hashed
        assert hash(proxy1) != hash(proxy3)
    
    def test_proxy_in_string_operations(self):
        """Test proxy in various string contexts."""
        field_meta = FieldMeta(name="word", description="Word")
        proxy = FieldValueProxy("test", field_meta)
        
        # String membership
        assert "es" in proxy
        assert "xyz" not in proxy
        
        # String multiplication
        assert proxy * 3 == "testtesttest"
        assert 2 * proxy == "testtest"
        
        # String methods that return booleans
        assert proxy.isalpha()
        assert not proxy.isspace()
        assert proxy.isascii()


class TestBackwardCompatibility:
    """Test that existing code still works with the new implementation."""
    
    def test_str_conversion_still_works(self):
        """Test that str(proxy) still returns the string value."""
        field_meta = FieldMeta(name="field", description="Field")
        proxy = FieldValueProxy("value", field_meta)
        
        # Explicit str() conversion (even though unnecessary now)
        assert str(proxy) == "value"
        assert f"{proxy}" == "value"
        assert "%s" % proxy == "value"
    
    def test_equality_with_strings_still_works(self):
        """Test that proxy == "string" comparisons still work."""
        field_meta = FieldMeta(name="field", description="Field")
        proxy = FieldValueProxy("test value", field_meta)
        
        assert proxy == "test value"
        assert not (proxy == "other value")
        assert proxy != "other value"
        assert not (proxy != "test value")
    
    def test_len_still_works(self):
        """Test that len(proxy) still returns string length."""
        field_meta = FieldMeta(name="field", description="Field")
        proxy = FieldValueProxy("12345", field_meta)
        
        assert len(proxy) == 5
    
    def test_bool_still_works(self):
        """Test that bool(proxy) still works correctly."""
        field_meta = FieldMeta(name="field", description="Field")
        
        proxy_full = FieldValueProxy("content", field_meta)
        assert bool(proxy_full) is True
        if proxy_full:  # Should enter this branch
            pass
        else:
            pytest.fail("Should have been truthy")
        
        proxy_empty = FieldValueProxy("", field_meta)
        assert bool(proxy_empty) is False
        if proxy_empty:
            pytest.fail("Should have been falsy")