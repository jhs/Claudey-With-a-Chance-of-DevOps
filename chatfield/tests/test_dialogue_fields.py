"""Test field behaviors and decorators in Interview classes."""

import pytest
from chatfield import Interview, chatfield, must, hint, as_int, as_float, as_bool, as_lang


class TestInterviewFields:
    """Test various field behaviors in Interview classes."""
    
    def test_field_with_type_transformations(self):
        """Test fields with type transformation using builder."""
        instance = (chatfield()
            .type("TypedInterview")
            .desc("Interview with typed fields")
            .field("age")
                .desc("Your age")
                .as_int()
            .field("salary")
                .desc("Expected salary")
                .as_float()
            .field("available")
                .desc("Are you available immediately?")
                .as_bool()
            .build())
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
        """Test fields with language transformation using builder."""
        instance = (chatfield()
            .type("MultilingualInterview")
            .desc("Interview with language transformations")
            .field("greeting")
                .desc("Say hello")
                .as_lang.fr()
                .as_lang.es()
            .build())
        meta = instance._chatfield
        
        # Check field exists
        assert 'greeting' in meta['fields']
        
        # Check language transformations
        field_casts = meta['fields']['greeting']['casts']
        assert 'as_lang_fr' in field_casts
        assert 'as_lang_es' in field_casts
    
    def test_field_with_mixed_decorators(self):
        """Test fields with mixed features using builder."""
        instance = (chatfield()
            .type("MixedInterview")
            .desc("Interview with mixed decorators")
            .field("years_experience")
                .desc("Years of experience")
                .must("be positive")
                .hint("Think of your best qualities")
                .as_int()
            .build())
        meta = instance._chatfield
        
        field = meta['fields']['years_experience']
        
        # Check validation rules
        assert "be positive" in field['specs']['must']
        assert "Think of your best qualities" in field['specs']['hint']
        
        # Check transformation
        assert 'as_int' in field['casts']
    
    def test_multiple_fields_with_decorators(self):
        """Test multiple fields each with features using builder."""
        instance = (chatfield()
            .type("CompleteInterview")
            .desc("Complete interview process")
            .field("name")
                .desc("Your full name")
                .must("be honest")
            .field("email")
                .desc("Your email address")
                .must("valid email")
                .hint("We'll send confirmation here")
            .field("experience")
                .desc("Years of experience")
                .must("be realistic")
                .as_int()
            .field("remote")
                .desc("Open to remote work?")
                .as_bool()
            .build())
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
        """Test that field descriptions are properly set using builder."""
        instance = (chatfield()
            .type("DescriptiveInterview")
            .desc("Interview with detailed descriptions")
            .field("short").desc("Name")
            .field("medium").desc("Please provide your full legal name")
            .field("long").desc("This is a very long description that explains in great detail what we need from you and why it's important for the process")
            .build())
        meta = instance._chatfield
        
        assert meta['fields']['short']['desc'] == "Name"
        assert meta['fields']['medium']['desc'] == "Please provide your full legal name"
        assert meta['fields']['long']['desc'] == "This is a very long description that explains in great detail what we need from you and why it's important for the process"
    
    def test_field_order_preservation(self):
        """Test that field order is preserved as defined using builder."""
        instance = (chatfield()
            .type("OrderedInterview")
            .desc("Interview with specific field order")
            .field("first").desc("First question")
            .field("second").desc("Second question")
            .field("third").desc("Third question")
            .field("fourth").desc("Fourth question")
            .build())
        meta = instance._chatfield
        
        # Python 3.7+ guarantees dict order
        field_names = list(meta['fields'].keys())
        assert field_names == ['first', 'second', 'third', 'fourth']
    
    def test_empty_specs_and_casts(self):
        """Test fields without any features have empty specs and casts using builder."""
        instance = (chatfield()
            .type("PlainInterview")
            .desc("Plain interview without decorators")
            .field("undecorated").desc("Simple field")
            .build())
        meta = instance._chatfield
        
        field = meta['fields']['undecorated']
        
        # Should have empty specs and casts
        assert field['specs']['must'] == []
        assert field['specs']['reject'] == []
        assert field['specs']['hint'] == []
        assert field['casts'] == {}
        assert field['value'] is None  # Not collected yet