"""Unit tests for Chatfield Socratic dialogue metadata classes."""

import pytest
from chatfield.socrates import FieldMeta, SocratesMeta, SocratesInstance, process_socrates_class


class TestFieldMeta:
    """Test FieldMeta class."""
    
    def test_field_meta_creation(self):
        """Test creating a FieldMeta instance."""
        field = FieldMeta("name", "Your name")
        assert field.name == "name"
        assert field.description == "Your name"
        assert field.must_rules == []
        assert field.reject_rules == []
        assert field.hints == []
    
    def test_add_must_rule(self):
        """Test adding must rules."""
        field = FieldMeta("email", "Your email")
        field.add_must_rule("valid email format")
        field.add_must_rule("not temporary email")
        
        assert len(field.must_rules) == 2
        assert "valid email format" in field.must_rules
        assert "not temporary email" in field.must_rules
    
    def test_add_reject_rule(self):
        """Test adding reject rules."""
        field = FieldMeta("password", "Your password")
        field.add_reject_rule("common passwords")
        field.add_reject_rule("personal information")
        
        assert len(field.reject_rules) == 2
        assert "common passwords" in field.reject_rules
        assert "personal information" in field.reject_rules
    
    def test_add_hint(self):
        """Test adding field hints."""
        field = FieldMeta("username", "Choose a username")
        field.add_hint("3-20 characters, letters and numbers only")
        
        assert field.hints == ["3-20 characters, letters and numbers only"]
    
    def test_has_validation_rules(self):
        """Test validation rule detection."""
        field = FieldMeta("test", "Test field")
        assert not field.has_validation_rules()
        
        field.add_must_rule("required")
        assert field.has_validation_rules()
        
        field2 = FieldMeta("test2", "Test field 2")
        field2.add_reject_rule("forbidden")
        assert field2.has_validation_rules()


class TestSocratesMeta:
    """Test SocratesMeta class."""
    
    def test_socrates_meta_creation(self):
        """Test creating a SocratesMeta instance."""
        meta = SocratesMeta()
        assert meta.user_context == []
        assert meta.agent_context == []
        assert meta.docstring == ""
        assert meta.fields == {}
    
    def test_add_user_context(self):
        """Test adding user context."""
        meta = SocratesMeta()
        meta.add_user_context("Small business owner")
        meta.add_user_context("Not technical")
        
        assert len(meta.user_context) == 2
        assert "Small business owner" in meta.user_context
        assert "Not technical" in meta.user_context
    
    def test_add_agent_context(self):
        """Test adding agent context."""
        meta = SocratesMeta()
        meta.add_agent_context("Helpful assistant")
        meta.add_agent_context("Patient teacher")
        
        assert len(meta.agent_context) == 2
        assert "Helpful assistant" in meta.agent_context
        assert "Patient teacher" in meta.agent_context
    
    def test_set_docstring(self):
        """Test setting docstring."""
        meta = SocratesMeta()
        meta.set_docstring("  Test docstring  ")
        assert meta.docstring == "Test docstring"
        
        meta.set_docstring("")
        assert meta.docstring == ""
        
        meta.set_docstring(None)
        assert meta.docstring == ""
    
    def test_add_field(self):
        """Test adding fields."""
        meta = SocratesMeta()
        field1 = meta.add_field("name", "Your name")
        field2 = meta.add_field("email", "Your email")
        
        assert isinstance(field1, FieldMeta)
        assert isinstance(field2, FieldMeta)
        assert len(meta.fields) == 2
        assert "name" in meta.fields
        assert "email" in meta.fields
        assert meta.fields["name"] == field1
        assert meta.fields["email"] == field2
    
    def test_get_field(self):
        """Test getting fields."""
        meta = SocratesMeta()
        field = meta.add_field("test", "Test field")
        
        retrieved = meta.get_field("test")
        assert retrieved == field
        
        missing = meta.get_field("nonexistent")
        assert missing is None
    
    def test_get_field_names(self):
        """Test getting field names in order."""
        meta = SocratesMeta()
        meta.add_field("first", "First field")
        meta.add_field("second", "Second field")
        meta.add_field("third", "Third field")
        
        names = meta.get_field_names()
        assert names == ["first", "second", "third"]
    
    def test_has_context(self):
        """Test context detection."""
        meta = SocratesMeta()
        assert not meta.has_context()
        
        meta.add_user_context("User info")
        assert meta.has_context()
        
        meta2 = GathererMeta()
        meta2.add_agent_context("Agent behavior")
        assert meta2.has_context()
        
        meta3 = GathererMeta()
        meta3.set_docstring("Test docstring")
        assert meta3.has_context()


class TestSocratesInstance:
    """Test SocratesInstance class."""
    
    def test_instance_creation(self):
        """Test creating a SocratesInstance."""
        meta = SocratesMeta()
        meta.add_field("name", "Your name")
        meta.add_field("email", "Your email")
        
        data = {"name": "John Doe", "email": "john@example.com"}
        instance = SocratesInstance(meta, data)
        
        assert instance.name == "John Doe"
        assert instance.email == "john@example.com"
    
    def test_attribute_access(self):
        """Test accessing collected data as attributes."""
        meta = SocratesMeta()
        data = {"field1": "value1", "field2": "value2"}
        instance = SocratesInstance(meta, data)
        
        assert instance.field1 == "value1"
        assert instance.field2 == "value2"
        
        with pytest.raises(AttributeError):
            _ = instance.nonexistent_field
    
    def test_get_data(self):
        """Test getting all data as dictionary."""
        meta = SocratesMeta()
        original_data = {"name": "John", "email": "john@example.com"}
        instance = GathererInstance(meta, original_data)
        
        retrieved_data = instance.get_data()
        assert retrieved_data == original_data
        
        # Should be a copy, not the original
        retrieved_data["name"] = "Jane"
        assert instance.name == "John"
    
    def test_get_with_default(self):
        """Test getting field with default value."""
        meta = SocratesMeta()
        data = {"name": "John"}
        instance = SocratesInstance(meta, data)
        
        assert instance.get("name") == "John"
        assert instance.get("email") is None
        assert instance.get("email", "default@example.com") == "default@example.com"
    
    def test_repr(self):
        """Test string representation."""
        meta = SocratesMeta()
        data = {"name": "John", "email": "john@example.com"}
        instance = SocratesInstance(meta, data)
        
        repr_str = repr(instance)
        assert "SocratesInstance" in repr_str
        assert "name='John'" in repr_str
        assert "email='john@example.com'" in repr_str
    
    def test_repr_long_values(self):
        """Test string representation with long values."""
        meta = SocratesMeta()
        long_value = "a" * 100
        data = {"long_field": long_value}
        instance = SocratesInstance(meta, data)
        
        repr_str = repr(instance)
        assert "..." in repr_str  # Should be truncated


class TestProcessSocratesClass:
    """Test the process_socrates_class function."""
    
    def test_process_simple_class(self):
        """Test processing a simple class."""
        class Simple:
            """Simple Socratic dialogue"""
            def name(): "Your name"
            def email(): "Your email"
        
        meta = process_socrates_class(Simple)
        
        assert meta.docstring == "Simple Socratic dialogue"
        assert len(meta.fields) == 2
        assert "name" in meta.fields
        assert "email" in meta.fields
        assert meta.fields["name"].description == "Your name"
        assert meta.fields["email"].description == "Your email"
    
    def test_process_class_with_context(self):
        """Test processing class with user/agent context."""
        class WithContext:
            _chatfield_user_context = ["User info"]
            _chatfield_agent_context = ["Agent behavior"]
            def field(): "Test field"
        
        meta = process_gatherer_class(WithContext)
        
        assert "User info" in meta.user_context
        assert "Agent behavior" in meta.agent_context
    
    def test_process_empty_class(self):
        """Test processing class with no annotations."""
        class Empty:
            """Empty class"""
            pass
        
        meta = process_gatherer_class(Empty)
        
        assert meta.docstring == "Empty class"
        assert len(meta.fields) == 0
    
    def test_process_mixed_functions(self):
        """Test processing class with mixed function types."""
        class Mixed:
            def string_field(): "This is a field"
            
            # Regular method without docstring should be ignored
            def regular_method(self):
                return "not a field"
                
            # Function with no docstring should be ignored
            def no_docstring():
                pass
        
        meta = process_gatherer_class(Mixed)
        
        assert len(meta.fields) == 1
        assert "string_field" in meta.fields
        assert "regular_method" not in meta.fields
        assert "no_docstring" not in meta.fields