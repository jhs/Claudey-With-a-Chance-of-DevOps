"""Unit tests for Chatfield decorators."""

import pytest
from chatfield import Interview, must, reject, hint, alice, bob


class TestFieldDecorators:
    """Test field decorators like @must, @reject, @hint."""
    
    def test_basic_function_fields(self):
        """Test basic function-based field definition."""
        class SimpleFunction(Interview):
            def name(): "Your name"
            def email(): "Your email"
        
        instance = SimpleFunction()
        meta = instance._chatfield
        assert len(meta['fields']) == 2
        assert "name" in meta['fields']
        assert "email" in meta['fields']
        assert meta['fields']["name"]['desc'] == "Your name"
        assert meta['fields']["email"]['desc'] == "Your email"
    
    def test_must_decorator(self):
        """Test @must decorator stores rules."""
        class WithMust(Interview):
            @must("specific requirement")
            def field(): "Test field"
        
        instance = WithMust()
        field_meta = instance._chatfield['fields']["field"]
        assert "specific requirement" in field_meta['specs']['must']
    
    def test_multiple_must_rules(self):
        """Test multiple @must decorators."""
        class MultipleMust(Interview):
            @must("rule 1")
            @must("rule 2")
            @must("rule 3")
            def field(): "Test field"
        
        instance = MultipleMust()
        field_meta = instance._chatfield['fields']["field"]
        # Decorators apply in reverse order
        assert field_meta['specs']['must'] == ["rule 3", "rule 2", "rule 1"]
    
    def test_reject_decorator(self):
        """Test @reject decorator."""
        class WithReject(Interview):
            @reject("avoid this")
            def field(): "Test field"
        
        instance = WithReject()
        field_meta = instance._chatfield['fields']["field"]
        assert "avoid this" in field_meta['specs']['reject']
    
    def test_hint_decorator(self):
        """Test @hint decorator."""
        class WithHint(Interview):
            @hint("Helpful tip")
            def field(): "Test field"
        
        instance = WithHint()
        field_meta = instance._chatfield['fields']["field"]
        assert field_meta['specs']['hint'] == ["Helpful tip"]
    
    def test_multiple_hints(self):
        """Test multiple @hint decorators accumulate like @must."""
        class TestClass(Interview):
            @hint('First hint')
            @hint('Second hint')
            @hint('Third hint')
            def field(): "Test field with multiple hints"
        
        instance = TestClass()
        field_meta = instance._chatfield['fields']['field']
        
        assert field_meta['specs']['hint'] == ['Third hint', 'Second hint', 'First hint']
        assert len(field_meta['specs']['hint']) == 3
    
    def test_all_field_decorators(self):
        """Test field with all decorator types combined."""
        class AllDecorators(Interview):
            @must("required info")
            @reject("forbidden content")
            @hint("Helpful guidance")
            def complex_field(): "Complex field"
        
        instance = AllDecorators()
        field_meta = instance._chatfield['fields']["complex_field"]
        
        assert field_meta['desc'] == "Complex field"
        assert "required info" in field_meta['specs']['must']
        assert "forbidden content" in field_meta['specs']['reject']
        assert field_meta['specs']['hint'] == ["Helpful guidance"]


class TestClassDecorators:
    """Test class-level decorators like @alice and @bob."""
    
    def test_alice_decorator(self):
        """Test @alice decorator stores context."""
        @alice("Senior Developer")
        class WithAlice(Interview):
            def field(): "Test field"
        
        instance = WithAlice()
        meta = instance._chatfield
        assert meta['roles']['alice']['type'] == "Senior Developer"
    
    def test_alice_traits(self):
        """Test @alice.trait decorator."""
        @alice("Interviewer")
        @alice.trait("patient")
        @alice.trait("thorough")
        class WithAliceTraits(Interview):
            def field(): "Test field"
        
        instance = WithAliceTraits()
        meta = instance._chatfield
        assert meta['roles']['alice']['type'] == "Interviewer"
        assert "patient" in meta['roles']['alice']['traits']
        assert "thorough" in meta['roles']['alice']['traits']
    
    def test_bob_decorator(self):
        """Test @bob decorator stores context."""
        @bob("Job Candidate")
        class WithBob(Interview):
            def field(): "Test field"
        
        instance = WithBob()
        meta = instance._chatfield
        assert meta['roles']['bob']['type'] == "Job Candidate"
    
    def test_bob_traits(self):
        """Test @bob.trait decorator."""
        @bob("User")
        @bob.trait("technical")
        @bob.trait("curious")
        class WithBobTraits(Interview):
            def field(): "Test field"
        
        instance = WithBobTraits()
        meta = instance._chatfield
        assert meta['roles']['bob']['type'] == "User"
        assert "technical" in meta['roles']['bob']['traits']
        assert "curious" in meta['roles']['bob']['traits']


class TestComplexDecorators:
    """Test complex decorator combinations."""
    
    def test_full_decorator_stack(self):
        """Test a class with all decorator types."""
        @alice("Interviewer")
        @alice.trait("professional")
        @bob("Candidate")
        @bob.trait("experienced")
        class FullStack(Interview):
            """Test interview process"""
            def field1(): "First field"
            def field2(): "Second field"
        
        instance = FullStack()
        meta = instance._chatfield
        
        # Check class description
        assert meta['desc'] == "Test interview process"
        
        # Check alice role
        assert meta['roles']['alice']['type'] == "Interviewer"
        assert "professional" in meta['roles']['alice']['traits']
        
        # Check bob role
        assert meta['roles']['bob']['type'] == "Candidate"
        assert "experienced" in meta['roles']['bob']['traits']
        
        # Check fields
        assert "field1" in meta['fields']
        assert "field2" in meta['fields']
        assert meta['fields']["field1"]['desc'] == "First field"
        assert meta['fields']["field2"]['desc'] == "Second field"


class TestInheritance:
    """Test that decorators work properly with inheritance."""
    
    def test_decorator_on_inherited_method(self):
        """Test decorators on methods that might be inherited."""
        class BaseInterview(Interview):
            @must("base requirement")
            def base_field(): "Base field"
        
        class DerivedInterview(BaseInterview):
            @must("derived requirement")
            def derived_field(): "Derived field"
        
        instance = DerivedInterview()
        meta = instance._chatfield
        
        # Should have both fields
        assert len(meta['fields']) == 2
        assert "base_field" in meta['fields']
        assert "derived_field" in meta['fields']
        
        # Check decorator metadata
        base_field = meta['fields']["base_field"]
        assert "base requirement" in base_field['specs']['must']
        
        derived_field = meta['fields']["derived_field"]
        assert "derived requirement" in derived_field['specs']['must']


class TestFunctionSyntaxValidation:
    """Test validation of function-based field syntax."""
    
    def test_functions_without_docstring_ignored(self):
        """Test that functions without docstrings are ignored."""
        class NoDocstring(Interview):
            def valid_field(): "This has a docstring"
            
            def invalid_field():
                pass  # No docstring
        
        instance = NoDocstring()
        meta = instance._chatfield
        assert len(meta['fields']) == 1
        assert "valid_field" in meta['fields']
        assert "invalid_field" not in meta['fields']
    
    def test_builtin_methods_ignored(self):
        """Test that built-in methods are ignored."""
        class WithBuiltins(Interview):
            def field(): "Valid field"
            
            # These should all be ignored
            def __init__(self):
                super().__init__()
            
            def __str__(self):
                return "test"
                
            def __repr__(self):
                return "test"
        
        instance = WithBuiltins()
        meta = instance._chatfield
        assert len(meta['fields']) == 1
        assert "field" in meta['fields']
        assert "__init__" not in meta['fields']
        assert "__str__" not in meta['fields']
        assert "__repr__" not in meta['fields']
    
    def test_empty_function_body(self):
        """Test that functions with empty bodies work correctly."""
        class EmptyBodies(Interview):
            def field1(): "Field with pass"
            def field2(): "Field with ellipsis"
                
        instance = EmptyBodies()
        meta = instance._chatfield
        assert len(meta['fields']) == 2
        assert meta['fields']["field1"]['desc'] == "Field with pass"
        assert meta['fields']["field2"]['desc'] == "Field with ellipsis"


class TestErrorCases:
    """Test error handling in decorators."""
    
    def test_empty_class(self):
        """Test Interview with no fields."""
        class Empty(Interview):
            """Empty interview"""
            pass
        
        instance = Empty()
        meta = instance._chatfield
        assert meta['desc'] == "Empty interview"
        assert len(meta['fields']) == 0
    
    def test_no_docstring(self):
        """Test Interview with no docstring."""
        class NoDoc(Interview):
            def field(): "Test field"
        
        instance = NoDoc()
        meta = instance._chatfield
        assert meta['desc'] == ""
        assert len(meta['fields']) == 1