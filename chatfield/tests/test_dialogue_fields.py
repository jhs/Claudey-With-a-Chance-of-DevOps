"""Tests for Dialogue field initialization and access control."""

import pytest
from chatfield import Dialogue, must, hint
from chatfield.field_proxy import FieldValueProxy
from chatfield.types import as_int, as_float


class TestDialogueFieldInitialization:
    """Test that Dialogue fields are properly initialized to None."""
    
    def test_fields_initialize_as_none(self):
        """Test that all defined fields are initialized to None."""
        class UserRequest(Dialogue):
            """Test dialogue"""
            
            def scope():
                """Scope of work"""
                pass
            
            def budget():
                """Project budget"""
                pass
            
            def timeline():
                """Timeline"""
                pass
        
        # Create instance
        request = UserRequest()
        
        # All fields should be None initially
        assert request.scope is None
        assert request.budget is None
        assert request.timeline is None
    
    def test_fields_with_decorators_initialize_as_none(self):
        """Test that decorated fields also initialize as None."""
        class ProjectRequest(Dialogue):
            """Test dialogue with decorators"""
            
            @hint("Be specific")
            @must("include timeline")
            def scope():
                """Scope of work"""
                pass
            
            @as_int
            @as_float
            def budget():
                """Budget in dollars"""
                pass
        
        request = ProjectRequest()
        
        # Decorated fields should also be None initially
        assert request.scope is None
        assert request.budget is None
    
    def test_fields_are_read_only(self):
        """Test that fields cannot be set directly."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
            
            def field2():
                """Field 2"""
                pass
        
        dialogue = TestDialogue()
        
        # Attempting to set a field should raise AttributeError
        with pytest.raises(AttributeError) as exc_info:
            dialogue.field1 = "some value"
        
        assert "Cannot set field 'field1' directly" in str(exc_info.value)
        assert "fields are read-only" in str(exc_info.value)
        
        # Field should still be None
        assert dialogue.field1 is None
    
    def test_non_field_attributes_can_be_set(self):
        """Test that non-field attributes can be set normally."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
        
        dialogue = TestDialogue()
        
        # Should be able to set non-field attributes
        dialogue.custom_attr = "custom value"
        assert dialogue.custom_attr == "custom value"
        
        # But not fields
        with pytest.raises(AttributeError):
            dialogue.field1 = "value"
    
    def test_accessing_undefined_field_raises_error(self):
        """Test that accessing undefined fields raises AttributeError."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
        
        dialogue = TestDialogue()
        
        # Accessing undefined field should raise AttributeError
        with pytest.raises(AttributeError) as exc_info:
            _ = dialogue.undefined_field
        
        assert "'TestDialogue' object has no attribute 'undefined_field'" in str(exc_info.value)
    
    def test_done_property_initial_state(self):
        """Test that done property reflects field completion."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
            
            def field2():
                """Field 2"""
                pass
        
        dialogue = TestDialogue()
        
        # Initially not done (fields are None)
        assert dialogue.done is False
    
    def test_repr_shows_field_status(self):
        """Test that __repr__ shows field status."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
            
            def field2():
                """Field 2"""
                pass
        
        dialogue = TestDialogue()
        
        repr_str = repr(dialogue)
        assert "TestDialogue" in repr_str
        assert "field1=None" in repr_str
        assert "field2=None" in repr_str


class TestDialogueFieldSetting:
    """Test internal field setting mechanism."""
    
    def test_set_field_value_with_string(self):
        """Test setting field value internally."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def name():
                """Your name"""
                pass
        
        dialogue = TestDialogue()
        
        # Initially None
        assert dialogue.name is None
        
        # Set field value internally
        dialogue._set_field_value("name", "John Doe")
        
        # Now should be a FieldValueProxy
        assert dialogue.name is not None
        assert isinstance(dialogue.name, FieldValueProxy)
        assert str(dialogue.name) == "John Doe"
    
    def test_set_field_value_with_transformations(self):
        """Test setting field with transformations."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            @as_int
            @as_float
            def age():
                """Your age"""
                pass
        
        dialogue = TestDialogue()
        
        # Set with transformations
        dialogue._set_field_value(
            "age", 
            "twenty-five",
            transformations={"as_int": 25, "as_float": 25.0}
        )
        
        # Should have access to transformations
        assert str(dialogue.age) == "twenty-five"
        assert dialogue.age.as_int == 25
        assert dialogue.age.as_float == 25.0
    
    def test_set_field_value_with_evaluations(self):
        """Test setting field with match evaluations."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            @must("be specific")
            def scope():
                """Project scope"""
                pass
        
        dialogue = TestDialogue()
        
        # Set with evaluations
        dialogue._set_field_value(
            "scope",
            "Build a web application",
            evaluations={"_must_be_specific": True}
        )
        
        assert str(dialogue.scope) == "Build a web application"
    
    def test_set_field_value_to_none(self):
        """Test setting field back to None."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
        
        dialogue = TestDialogue()
        
        # Set to a value
        dialogue._set_field_value("field1", "value")
        assert dialogue.field1 is not None
        
        # Set back to None
        dialogue._set_field_value("field1", None)
        assert dialogue.field1 is None
    
    def test_set_unknown_field_raises_error(self):
        """Test that setting unknown field raises error."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
        
        dialogue = TestDialogue()
        
        with pytest.raises(ValueError) as exc_info:
            dialogue._set_field_value("unknown_field", "value")
        
        assert "Unknown field: unknown_field" in str(exc_info.value)
    
    def test_done_property_after_setting_fields(self):
        """Test done property after setting all fields."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
            
            def field2():
                """Field 2"""
                pass
        
        dialogue = TestDialogue()
        
        # Initially not done
        assert dialogue.done is False
        
        # Set one field
        dialogue._set_field_value("field1", "value1")
        assert dialogue.done is False  # Still not done
        
        # Set second field
        dialogue._set_field_value("field2", "value2")
        assert dialogue.done is True  # Now done
    
    def test_repr_after_setting_fields(self):
        """Test __repr__ after setting fields."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
            
            def field2():
                """Field 2"""
                pass
        
        dialogue = TestDialogue()
        
        # Set one field
        dialogue._set_field_value("field1", "value")
        
        repr_str = repr(dialogue)
        assert "field1=<set>" in repr_str
        assert "field2=None" in repr_str


class TestDialoguePrivateAttributes:
    """Test that private attributes work correctly."""
    
    def test_private_attributes_can_be_set(self):
        """Test that private attributes (starting with _) can be set."""
        class TestDialogue(Dialogue):
            """Test dialogue"""
            
            def field1():
                """Field 1"""
                pass
        
        dialogue = TestDialogue()
        
        # Should be able to set private attributes
        dialogue._custom_private = "private value"
        assert dialogue._custom_private == "private value"
        
        # Internal attributes should exist
        assert hasattr(dialogue, '_meta')
        assert hasattr(dialogue, '_field_values')
        assert hasattr(dialogue, '_collected_data')


class TestDialogueIntegration:
    """Integration tests with real-world usage patterns."""
    
    def test_evaluator_compatibility(self):
        """Test that the dialogue works with evaluator patterns."""
        from chatfield import user, agent
        
        @user("Product Owner")
        @agent("Tech partner")
        class UserRequest(Dialogue):
            """Product request"""
            
            @must("be specific")
            def scope():
                """Scope of work"""
                pass
            
            @as_int
            def budget():
                """Budget in dollars"""
                pass
        
        # Create instance like in run_real_api.py
        user_request = UserRequest()
        
        # Check initial state
        assert user_request.scope is None
        assert user_request.budget is None
        assert user_request.done is False
        
        # Simulate evaluator setting values
        user_request._set_field_value("scope", "Build a web app")
        user_request._set_field_value("budget", "50000", transformations={"as_int": 50000})
        
        # Check final state
        assert str(user_request.scope) == "Build a web app"
        assert str(user_request.budget) == "50000"
        assert user_request.budget.as_int == 50000
        assert user_request.done is True