"""Unit tests for Chatfield decorators."""

import pytest
from chatfield import Dialogue, must, reject, hint, user, agent
from chatfield.socrates import SocratesMeta, process_socrates_class


class TestFieldDecorators:
    """Test field decorators like @must, @reject, @hint."""
    
    def test_basic_function_fields(self):
        """Test basic function-based field definition."""
        class SimpleFunction(Dialogue):
            def name(): "Your name"
            def email(): "Your email"
        
        meta = SimpleFunction._get_meta()
        assert len(meta.fields) == 2
        assert "name" in meta.fields
        assert "email" in meta.fields
        assert meta.fields["name"].description == "Your name"
        assert meta.fields["email"].description == "Your email"
    
    def test_must_decorator(self):
        """Test @must decorator stores rules."""
        class WithMust(Dialogue):
            @must("specific requirement")
            def field(): "Test field"
        
        meta = WithMust._get_meta()
        field_meta = meta.fields["field"]
        assert "specific requirement" in field_meta.must_rules
    
    def test_multiple_must_rules(self):
        """Test multiple @must decorators."""
        class MultipleMust(Dialogue):
            @must("rule 1")
            @must("rule 2")
            @must("rule 3")
            def field(): "Test field"
        
        meta = MultipleMust._get_meta()
        field_meta = meta.fields["field"]
        # Decorators apply in reverse order
        assert field_meta.must_rules == ["rule 3", "rule 2", "rule 1"]
    
    def test_reject_decorator(self):
        """Test @reject decorator."""
        class WithReject(Dialogue):
            @reject("avoid this")
            def field(): "Test field"
        
        meta = WithReject._get_meta()
        field_meta = meta.fields["field"]
        assert "avoid this" in field_meta.reject_rules
    
    def test_hint_decorator(self):
        """Test @hint decorator."""
        class WithHint(Dialogue):
            @hint("Helpful tip")
            def field(): "Test field"
        
        meta = WithHint._get_meta()
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
        class AllDecorators(Dialogue):
            @must("required info")
            @reject("forbidden content")
            @hint("Helpful guidance")
            def complex_field(): "Complex field"
        
        meta = AllDecorators._get_meta()
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
        class WithUser(Dialogue):
            def field(): "Test field"
        
        meta = WithUser._get_meta()
        assert "Test user context" in meta.user_context
    
    def test_multiple_user_contexts(self):
        """Test multiple @user decorators accumulate."""
        @user("Context 1")
        @user("Context 2")
        class MultipleUser(Dialogue):
            def field(): "Test field"
        
        meta = MultipleUser._get_meta()
        assert "Context 1" in meta.user_context
        assert "Context 2" in meta.user_context
    
    def test_agent_decorator(self):
        """Test @agent decorator stores behavior."""
        @agent("Test agent behavior")
        class WithAgent(Dialogue):
            def field(): "Test field"
        
        meta = WithAgent._get_meta()
        assert "Test agent behavior" in meta.agent_context
    
    def test_multiple_agent_contexts(self):
        """Test multiple @agent decorators accumulate."""
        @agent("Behavior 1")
        @agent("Behavior 2") 
        class MultipleAgent(Dialogue):
            def field(): "Test field"
        
        meta = MultipleAgent._get_meta()
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
        class FullStack(Dialogue):
            """Test docstring"""
            def field1(): "First field"
            def field2(): "Second field"
        
        meta = FullStack._get_meta()
        
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


class TestInheritance:
    """Test that decorators work properly with inheritance."""
    
    def test_decorator_on_inherited_method(self):
        """Test decorators on methods that might be inherited."""
        class BaseClass:
            @must("base requirement")
            def base_field(): "Base field"
        
        class DerivedClass(Dialogue, BaseClass):
            @must("derived requirement")
            def derived_field(): "Derived field"
        
        meta = DerivedClass._get_meta()
        
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
        class NoDocstring(Dialogue):
            def valid_field(): "This has a docstring"
            
            def invalid_field():
                pass  # No docstring
        
        meta = NoDocstring._get_meta()
        assert len(meta.fields) == 1
        assert "valid_field" in meta.fields
        assert "invalid_field" not in meta.fields
    
    def test_builtin_methods_ignored(self):
        """Test that built-in methods are ignored."""
        class WithBuiltins(Dialogue):
            def field(): "Valid field"
            
            # These should all be ignored
            def __init__(self):
                pass
            
            def __str__(self):
                return "test"
                
            def __repr__(self):
                return "test"
        
        meta = WithBuiltins._get_meta()
        assert len(meta.fields) == 1
        assert "field" in meta.fields
        assert "__init__" not in meta.fields
        assert "__str__" not in meta.fields
        assert "__repr__" not in meta.fields
    
    def test_mixed_functions_ignored_correctly(self):
        """Test that non-field functions are ignored properly."""
        class MixedFunctions(Dialogue):
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
        
        meta = MixedFunctions._get_meta()
        assert len(meta.fields) == 1
        assert "valid_field" in meta.fields
        assert "no_docstring" not in meta.fields
        assert "regular_method" not in meta.fields
        assert "static_method" not in meta.fields
        assert "class_method" not in meta.fields
    
    def test_empty_function_body(self):
        """Test that functions with empty bodies work correctly."""
        class EmptyBodies(Dialogue):
            def field1(): "Field with pass"
            def field2(): "Field with ellipsis"
                
        meta = EmptyBodies._get_meta()
        assert len(meta.fields) == 2
        assert meta.fields["field1"].description == "Field with pass"
        assert meta.fields["field2"].description == "Field with ellipsis"


class TestErrorCases:
    """Test error handling in decorators."""
    
    def test_empty_class(self):
        """Test Dialogue with no fields."""
        class Empty(Dialogue):
            """Empty dialogue"""
            pass
        
        assert hasattr(Empty, 'gather')
        meta = Empty._get_meta()
        assert meta.docstring == "Empty dialogue"
        assert len(meta.fields) == 0
    
    def test_no_docstring(self):
        """Test Dialogue with no docstring."""
        class NoDoc(Dialogue):
            def field(): "Test field"
        
        meta = NoDoc._get_meta()
        assert meta.docstring == ""
        assert len(meta.fields) == 1