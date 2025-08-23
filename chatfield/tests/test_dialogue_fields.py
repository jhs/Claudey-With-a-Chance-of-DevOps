"""Test field behaviors and decorators in Interview classes."""

import pytest
from chatfield import Interview, must, hint, as_int, as_float, as_bool, as_lang


class TestInterviewFields:
    """Test various field behaviors in Interview classes."""
    
    def test_field_with_type_transformations(self):
        """Test fields with type transformation decorators."""
        class TypedInterview(Interview):
            """Interview with typed fields"""
            
            @as_int
            def age(): "Your age"
            
            @as_float
            def salary(): "Expected salary"
            
            @as_bool
            def available(): "Are you available immediately?"
        
        instance = TypedInterview()
        meta = instance._chatfield
        
        # Check fields exist
        assert 'age' in meta['fields']
        assert 'salary' in meta['fields']
        assert 'available' in meta['fields']
        
        # Check transformations are registered
        assert 'as_int' in meta['fields']['age']['casts']
        assert 'as_float' in meta['fields']['salary']['casts']
        assert 'as_bool' in meta['fields']['available']['casts']
    
    def test_field_with_language_transformations(self):
        """Test fields with language transformation decorators."""
        class MultilingualInterview(Interview):
            """Interview with language transformations"""
            
            @as_lang.fr
            @as_lang.es
            def greeting(): "Say hello"
        
        instance = MultilingualInterview()
        meta = instance._chatfield
        
        # Check field exists
        assert 'greeting' in meta['fields']
        
        # Check language transformations
        field_casts = meta['fields']['greeting']['casts']
        assert 'as_lang_fr' in field_casts
        assert 'as_lang_es' in field_casts
    
    def test_field_with_mixed_decorators(self):
        """Test fields with mixed decorator types."""
        class MixedInterview(Interview):
            """Interview with mixed decorators"""
            
            @must("be positive")
            @hint("Think of your best qualities")
            @as_int
            def years_experience(): "Years of experience"
        
        instance = MixedInterview()
        meta = instance._chatfield
        
        field = meta['fields']['years_experience']
        
        # Check validation rules
        assert "be positive" in field['specs']['must']
        assert "Think of your best qualities" in field['specs']['hint']
        
        # Check transformation
        assert 'as_int' in field['casts']
    
    def test_multiple_fields_with_decorators(self):
        """Test multiple fields each with decorators."""
        class CompleteInterview(Interview):
            """Complete interview process"""
            
            @must("be honest")
            def name(): "Your full name"
            
            @must("valid email")
            @hint("We'll send confirmation here")
            def email(): "Your email address"
            
            @as_int
            @must("be realistic")
            def experience(): "Years of experience"
            
            @as_bool
            def remote(): "Open to remote work?"
        
        instance = CompleteInterview()
        meta = instance._chatfield
        
        # Verify all fields exist
        assert len(meta['fields']) == 4
        assert all(field in meta['fields'] for field in ['name', 'email', 'experience', 'remote'])
        
        # Check specific field configurations
        assert "be honest" in meta['fields']['name']['specs']['must']
        assert "valid email" in meta['fields']['email']['specs']['must']
        assert "We'll send confirmation here" in meta['fields']['email']['specs']['hint']
        assert 'as_int' in meta['fields']['experience']['casts']
        assert 'as_bool' in meta['fields']['remote']['casts']
    
    def test_field_description_extraction(self):
        """Test that field descriptions are properly extracted."""
        class DescriptiveInterview(Interview):
            """Interview with detailed descriptions"""
            
            def short(): "Name"
            
            def medium(): "Please provide your full legal name"
            
            def long(): "This is a very long description that explains in great detail what we need from you and why it's important for the process"
        
        instance = DescriptiveInterview()
        meta = instance._chatfield
        
        assert meta['fields']['short']['desc'] == "Name"
        assert meta['fields']['medium']['desc'] == "Please provide your full legal name"
        assert meta['fields']['long']['desc'] == "This is a very long description that explains in great detail what we need from you and why it's important for the process"
    
    def test_field_order_preservation(self):
        """Test that field order is preserved as defined."""
        class OrderedInterview(Interview):
            """Interview with specific field order"""
            
            def first(): "First question"
            def second(): "Second question"
            def third(): "Third question"
            def fourth(): "Fourth question"
        
        instance = OrderedInterview()
        meta = instance._chatfield
        
        # Python 3.7+ guarantees dict order
        field_names = list(meta['fields'].keys())
        assert field_names == ['first', 'second', 'third', 'fourth']
    
    def test_empty_specs_and_casts(self):
        """Test fields without any decorators have empty specs and casts."""
        class PlainInterview(Interview):
            """Plain interview without decorators"""
            
            def undecorated(): "Simple field"
        
        instance = PlainInterview()
        meta = instance._chatfield
        
        field = meta['fields']['undecorated']
        
        # Should have empty specs and casts
        assert field['specs'] == {'must': [], 'reject': [], 'hint': []}
        assert field['casts'] == {}
        assert field['value'] is None  # Not collected yet