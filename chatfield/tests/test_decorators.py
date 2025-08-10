"""Unit tests for Chatfield decorators."""

import pytest
from chatfield.decorators import gather, must, reject, hint, user, agent
from chatfield.socrates import SocratesMeta, process_socrates_class


class TestGatherDecorator:
    """Test the @gather decorator."""
    
    def test_gather_adds_method(self):
        """Test that @gather adds the gather() class method."""
        @gather
        class Simple:
            def name(): "Your name"
        
        assert hasattr(Simple, 'gather')
        assert callable(Simple.gather)
    
    def test_gather_stores_metadata(self):
        """Test that @gather stores metadata on the class."""
        @gather
        class WithMeta:
            """Test gatherer"""
            def field(): "Test field"
        
        assert hasattr(WithMeta, '_chatfield_meta')
        meta = WithMeta._chatfield_meta
        assert isinstance(meta, SocratesMeta)
        assert meta.docstring == "Test gatherer"
        assert 'field' in meta.fields


class TestFieldDecorators:
    """Test field decorators like @must, @reject, @hint."""
    
    def test_basic_function_fields(self):
        """Test basic function-based field definition."""
        @gather
        class SimpleFunction:
            def name(): "Your name"
            def email(): "Your email"
        
        meta = SimpleFunction._chatfield_meta
        assert len(meta.fields) == 2
        assert "name" in meta.fields
        assert "email" in meta.fields
        assert meta.fields["name"].description == "Your name"
        assert meta.fields["email"].description == "Your email"
    
    def test_must_decorator(self):
        """Test @must decorator stores rules."""
        @gather
        class WithMust:
            @must("specific requirement")
            def field(): "Test field"
        
        meta = WithMust._chatfield_meta
        field_meta = meta.fields["field"]
        assert "specific requirement" in field_meta.must_rules
    
    def test_multiple_must_rules(self):
        """Test multiple @must decorators."""
        @gather
        class MultipleMust:
            @must("rule 1")
            @must("rule 2")
            @must("rule 3")
            def field(): "Test field"
        
        meta = MultipleMust._chatfield_meta
        field_meta = meta.fields["field"]
        # Decorators apply in reverse order
        assert field_meta.must_rules == ["rule 3", "rule 2", "rule 1"]
    
    def test_reject_decorator(self):
        """Test @reject decorator."""
        @gather
        class WithReject:
            @reject("avoid this")
            def field(): "Test field"
        
        meta = WithReject._chatfield_meta
        field_meta = meta.fields["field"]
        assert "avoid this" in field_meta.reject_rules
    
    def test_hint_decorator(self):
        """Test @hint decorator."""
        @gather
        class WithHint:
            @hint("Helpful tip")
            def field(): "Test field"
        
        meta = WithHint._chatfield_meta
        field_meta = meta.fields["field"]
        assert field_meta.hints == ["Helpful tip"]
    
    def test_field_metadata_processing(self):
        """Test field metadata processing from function definitions."""
        class TestClass:
            @must('rule1')
            @must('rule2')
            @reject('avoid this')
            @hint('Test hint')
            def field(): "Test field description"
        
        meta = process_socrates_class(TestClass)
        
        assert 'field' in meta.fields
        field_meta = meta.fields['field']
        assert field_meta.description == "Test field description"
        assert field_meta.must_rules == ['rule2', 'rule1']
        assert field_meta.reject_rules == ['avoid this']
        assert field_meta.hints == ['Test hint']
    
    def test_multiple_hints(self):
        """Test multiple @hint decorators accumulate like @must."""
        class TestClass:
            @hint('First hint')
            @hint('Second hint')
            @hint('Third hint')
            def field(): "Test field with multiple hints"
        
        meta = process_socrates_class(TestClass)
        field_meta = meta.fields['field']
        
        assert field_meta.hints == ['Third hint', 'Second hint', 'First hint']
        assert len(field_meta.hints) == 3
    
    def test_all_field_decorators(self):
        """Test field with all decorator types combined."""
        @gather
        class AllDecorators:
            @must("required info")
            @reject("forbidden content")
            @hint("Helpful guidance")
            def complex_field(): "Complex field"
        
        meta = AllDecorators._chatfield_meta
        field_meta = meta.fields["complex_field"]
        
        assert field_meta.description == "Complex field"
        assert "required info" in field_meta.must_rules
        assert "forbidden content" in field_meta.reject_rules
        assert field_meta.hints == ["Helpful guidance"]


class TestClassDecorators:
    """Test class-level decorators like @user and @agent."""
    
    def test_user_decorator(self):
        """Test @user decorator stores context."""
        @user("Test user context")
        @gather
        class WithUser:
            def field(): "Test field"
        
        meta = WithUser._chatfield_meta
        assert "Test user context" in meta.user_context
    
    def test_multiple_user_contexts(self):
        """Test multiple @user decorators accumulate."""
        @user("Context 1")
        @user("Context 2")
        @gather
        class MultipleUser:
            def field(): "Test field"
        
        meta = MultipleUser._chatfield_meta
        assert "Context 1" in meta.user_context
        assert "Context 2" in meta.user_context
    
    def test_agent_decorator(self):
        """Test @agent decorator stores behavior."""
        @agent("Test agent behavior")
        @gather
        class WithAgent:
            def field(): "Test field"
        
        meta = WithAgent._chatfield_meta
        assert "Test agent behavior" in meta.agent_context
    
    def test_multiple_agent_contexts(self):
        """Test multiple @agent decorators accumulate."""
        @agent("Behavior 1")
        @agent("Behavior 2") 
        @gather
        class MultipleAgent:
            def field(): "Test field"
        
        meta = MultipleAgent._chatfield_meta
        assert "Behavior 1" in meta.agent_context
        assert "Behavior 2" in meta.agent_context


class TestComplexDecorators:
    """Test complex decorator combinations."""
    
    def test_full_decorator_stack(self):
        """Test a class with all decorator types."""
        @user("User context 1")
        @user("User context 2")
        @agent("Agent behavior 1")
        @agent("Agent behavior 2")
        @gather
        class FullStack:
            """Test docstring"""
            def field1(): "First field"
            def field2(): "Second field"
        
        meta = FullStack._chatfield_meta
        
        # Check docstring
        assert meta.docstring == "Test docstring"
        
        # Check user contexts
        assert "User context 1" in meta.user_context
        assert "User context 2" in meta.user_context
        
        # Check agent contexts
        assert "Agent behavior 1" in meta.agent_context
        assert "Agent behavior 2" in meta.agent_context
        
        # Check fields
        assert "field1" in meta.fields
        assert "field2" in meta.fields
        assert meta.fields["field1"].description == "First field"
        assert meta.fields["field2"].description == "Second field"


class TestDecoratorOrder:
    """Test that decorator order doesn't matter."""
    
    def test_gather_first(self):
        """Test @gather decorator applied first."""
        @gather
        @user("User context")
        @agent("Agent behavior")
        class GatherFirst:
            def field(): "Test field"
        
        assert hasattr(GatherFirst, 'gather')
        meta = GatherFirst._chatfield_meta
        assert "User context" in meta.user_context
        assert "Agent behavior" in meta.agent_context
    
    def test_gather_last(self):
        """Test @gather decorator applied last."""
        @user("User context")
        @agent("Agent behavior")
        @gather
        class GatherLast:
            def field(): "Test field"
        
        assert hasattr(GatherLast, 'gather')
        meta = GatherLast._chatfield_meta
        assert "User context" in meta.user_context
        assert "Agent behavior" in meta.agent_context


class TestBackwardCompatibility:
    """Test that old annotation syntax no longer works."""
    
    def test_annotations_ignored(self):
        """Test that __annotations__ are ignored now."""
        class OldStyle:
            # This old syntax should not work anymore
            name: "Your name"
            email: "Your email"
        
        # Process without @gather to test raw processing
        meta = process_socrates_class(OldStyle)
        
        # Should have no fields since we don't process annotations anymore
        assert len(meta.fields) == 0
    
    def test_mixed_old_and_new_syntax(self):
        """Test mixing old and new syntax (only new should work)."""
        @gather
        class Mixed:
            # Old syntax - should be ignored
            old_field: "Old style field"
            
            # New syntax - should work
            def new_field(): "New style field"
        
        meta = Mixed._chatfield_meta
        assert len(meta.fields) == 1
        assert "new_field" in meta.fields
        assert "old_field" not in meta.fields


class TestInheritance:
    """Test that decorators work properly with inheritance."""
    
    def test_decorator_on_inherited_method(self):
        """Test decorators on methods that might be inherited."""
        class BaseClass:
            @must("base requirement")
            def base_field(): "Base field"
        
        @gather
        class DerivedClass(BaseClass):
            @must("derived requirement")
            def derived_field(): "Derived field"
        
        meta = DerivedClass._chatfield_meta
        
        # Should have both fields
        assert len(meta.fields) == 2
        assert "base_field" in meta.fields
        assert "derived_field" in meta.fields
        
        # Check decorator metadata
        base_field = meta.fields["base_field"]
        assert "base requirement" in base_field.must_rules
        
        derived_field = meta.fields["derived_field"]
        assert "derived requirement" in derived_field.must_rules


class TestFunctionSyntaxValidation:
    """Test validation of function-based field syntax."""
    
    def test_functions_without_docstring_ignored(self):
        """Test that functions without docstrings are ignored."""
        @gather  
        class NoDocstring:
            def valid_field(): "This has a docstring"
            
            def invalid_field():
                pass  # No docstring
        
        meta = NoDocstring._chatfield_meta
        assert len(meta.fields) == 1
        assert "valid_field" in meta.fields
        assert "invalid_field" not in meta.fields
    
    def test_builtin_methods_ignored(self):
        """Test that built-in methods are ignored."""
        @gather
        class WithBuiltins:
            def field(): "Valid field"
            
            # These should all be ignored
            def __init__(self):
                pass
            
            def __str__(self):
                return "test"
                
            def __repr__(self):
                return "test"
        
        meta = WithBuiltins._chatfield_meta
        assert len(meta.fields) == 1
        assert "field" in meta.fields
        assert "__init__" not in meta.fields
        assert "__str__" not in meta.fields
        assert "__repr__" not in meta.fields
    
    def test_mixed_functions_ignored_correctly(self):
        """Test that non-field functions are ignored properly."""
        @gather
        class MixedFunctions:
            def valid_field(): "This is a valid field"
            
            def no_docstring():
                # Function without docstring should be ignored
                return "not a field"
            
            def regular_method(self):
                # Method with self should be ignored
                return "also not a field"
            
            @staticmethod
            def static_method():
                # Static method should be ignored even with docstring
                """This static method should be ignored"""
                return "not a field"
            
            @classmethod
            def class_method(cls):
                """Class method should be ignored"""
                return "not a field"
        
        meta = MixedFunctions._chatfield_meta
        assert len(meta.fields) == 1
        assert "valid_field" in meta.fields
        assert "no_docstring" not in meta.fields
        assert "regular_method" not in meta.fields
        assert "static_method" not in meta.fields
        assert "class_method" not in meta.fields
    
    def test_empty_function_body(self):
        """Test that functions with empty bodies work correctly."""
        @gather
        class EmptyBodies:
            def field1(): "Field with pass"
            def field2(): "Field with ellipsis"
                
        meta = EmptyBodies._chatfield_meta
        assert len(meta.fields) == 2
        assert meta.fields["field1"].description == "Field with pass"
        assert meta.fields["field2"].description == "Field with ellipsis"


class TestErrorCases:
    """Test error handling in decorators."""
    
    def test_empty_class(self):
        """Test @gather on class with no fields."""
        @gather
        class Empty:
            """Empty gatherer"""
            pass
        
        assert hasattr(Empty, 'gather')
        meta = Empty._chatfield_meta
        assert meta.docstring == "Empty gatherer"
        assert len(meta.fields) == 0
    
    def test_no_docstring(self):
        """Test @gather on class with no docstring."""
        @gather
        class NoDoc:
            def field(): "Test field"
        
        meta = NoDoc._chatfield_meta
        assert meta.docstring == ""