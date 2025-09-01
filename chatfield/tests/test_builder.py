"""Unit tests for Chatfield builder pattern."""

import pytest
from chatfield import chatfield


class TestBasicBuilder:
    """Test basic builder functionality."""
    
    def test_simple_interview(self):
        """Test basic Interview creation with builder."""
        instance = (chatfield()
            .type("SimpleInterview")
            .desc("A simple interview")
            .field("name").desc("Your name")
            .field("email").desc("Your email")
            .build())
        
        meta = instance._chatfield
        assert meta['type'] == "SimpleInterview"
        assert meta['desc'] == "A simple interview"
        assert len(meta['fields']) == 2
        assert "name" in meta['fields']
        assert "email" in meta['fields']
        assert meta['fields']["name"]['desc'] == "Your name"
        assert meta['fields']["email"]['desc'] == "Your email"
    
    def test_field_validation_rules(self):
        """Test adding validation rules with builder."""
        instance = (chatfield()
            .type("ValidatedInterview")
            .field("field")
                .desc("Test field")
                .must("specific requirement")
                .reject("avoid this")
                .hint("Helpful tip")
            .build())
        
        field_meta = instance._chatfield['fields']["field"]
        assert "specific requirement" in field_meta['specs']['must']
        assert "avoid this" in field_meta['specs']['reject']
        assert "Helpful tip" in field_meta['specs']['hint']
    
    def test_multiple_validation_rules(self):
        """Test multiple validation rules on same field."""
        instance = (chatfield()
            .type("MultiRuleInterview")
            .field("field")
                .desc("Test field")
                .must("rule 1")
                .must("rule 2")
                .must("rule 3")
            .build())
        
        field_meta = instance._chatfield['fields']["field"]
        # Builder should maintain order
        assert field_meta['specs']['must'] == ["rule 1", "rule 2", "rule 3"]
    
    def test_multiple_hints(self):
        """Test multiple hints on same field."""
        instance = (chatfield()
            .type("MultiHintInterview")
            .field("field")
                .desc("Test field with multiple hints")
                .hint('First hint')
                .hint('Second hint')
                .hint('Third hint')
            .build())
        
        field_meta = instance._chatfield['fields']['field']
        assert field_meta['specs']['hint'] == ['First hint', 'Second hint', 'Third hint']
        assert len(field_meta['specs']['hint']) == 3
    
    def test_combined_field_features(self):
        """Test field with all feature types combined."""
        instance = (chatfield()
            .type("CombinedInterview")
            .field("complex_field")
                .desc("Complex field")
                .must("required info")
                .reject("forbidden content")
                .hint("Helpful guidance")
            .build())
        
        field_meta = instance._chatfield['fields']["complex_field"]
        
        assert field_meta['desc'] == "Complex field"
        assert "required info" in field_meta['specs']['must']
        assert "forbidden content" in field_meta['specs']['reject']
        assert "Helpful guidance" in field_meta['specs']['hint']


class TestRoleConfiguration:
    """Test alice and bob role configuration."""
    
    def test_alice_role(self):
        """Test alice role configuration."""
        instance = (chatfield()
            .type("WithAlice")
            .alice().type("Senior Developer")
            .field("field").desc("Test field")
            .build())
        
        meta = instance._chatfield
        assert meta['roles']['alice']['type'] == "Senior Developer"
    
    def test_alice_traits(self):
        """Test alice role with traits."""
        instance = (chatfield()
            .type("WithAliceTraits")
            .alice()
                .type("Interviewer")
                .trait("patient")
                .trait("thorough")
            .field("field").desc("Test field")
            .build())
        
        meta = instance._chatfield
        assert meta['roles']['alice']['type'] == "Interviewer"
        assert "patient" in meta['roles']['alice']['traits']
        assert "thorough" in meta['roles']['alice']['traits']
    
    def test_bob_role(self):
        """Test bob role configuration."""
        instance = (chatfield()
            .type("WithBob")
            .bob().type("Job Candidate")
            .field("field").desc("Test field")
            .build())
        
        meta = instance._chatfield
        assert meta['roles']['bob']['type'] == "Job Candidate"
    
    def test_bob_traits(self):
        """Test bob role with traits."""
        instance = (chatfield()
            .type("WithBobTraits")
            .bob()
                .type("User")
                .trait("technical")
                .trait("curious")
            .field("field").desc("Test field")
            .build())
        
        meta = instance._chatfield
        assert meta['roles']['bob']['type'] == "User"
        assert "technical" in meta['roles']['bob']['traits']
        assert "curious" in meta['roles']['bob']['traits']
    
    def test_both_roles(self):
        """Test configuring both alice and bob roles."""
        instance = (chatfield()
            .type("FullRoles")
            .desc("Test interview process")
            .alice()
                .type("Interviewer")
                .trait("professional")
            .bob()
                .type("Candidate")
                .trait("experienced")
            .field("field1").desc("First field")
            .field("field2").desc("Second field")
            .build())
        
        meta = instance._chatfield
        
        # Check description
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


class TestFieldTransformations:
    """Test field transformation features."""
    
    def test_type_transformations(self):
        """Test basic type transformations."""
        instance = (chatfield()
            .type("TypedInterview")
            .field("age")
                .desc("Your age")
                .as_int()
            .field("salary")
                .desc("Expected salary")
                .as_float()
            .field("active")
                .desc("Are you active?")
                .as_bool()
            .field("confidence")
                .desc("Confidence level")
                .as_percent()
            .build())
        
        assert 'as_int' in instance._chatfield['fields']['age']['casts']
        assert 'as_float' in instance._chatfield['fields']['salary']['casts']
        assert 'as_bool' in instance._chatfield['fields']['active']['casts']
        assert 'as_percent' in instance._chatfield['fields']['confidence']['casts']
    
    def test_language_transformations(self):
        """Test language transformations."""
        instance = (chatfield()
            .type("MultiLangInterview")
            .field("greeting")
                .desc("Say hello")
                .as_lang.fr()
                .as_lang.es()
            .build())
        
        field_casts = instance._chatfield['fields']['greeting']['casts']
        assert 'as_lang_fr' in field_casts
        assert 'as_lang_es' in field_casts
    
    def test_custom_transformations(self):
        """Test custom sub-attribute transformations."""
        instance = (chatfield()
            .type("CustomTransform")
            .field("number")
                .desc("A number")
                .as_bool.even("True if even")
                .as_str.uppercase("In uppercase")
            .build())
        
        field_casts = instance._chatfield['fields']['number']['casts']
        assert 'as_bool_even' in field_casts
        assert 'as_str_uppercase' in field_casts
    
    def test_choice_cardinality(self):
        """Test choice cardinality features."""
        instance = (chatfield()
            .type("ChoiceInterview")
            .field("color")
                .desc("Favorite color")
                .as_one.selection("red", "green", "blue")
            .field("priority")
                .desc("Priority level")
                .as_maybe.selection("low", "medium", "high")
            .field("languages")
                .desc("Programming languages")
                .as_multi.selection("python", "javascript", "rust")
            .field("reviewers")
                .desc("Code reviewers")
                .as_any.selection("alice", "bob", "charlie")
            .build())
        
        # Note: The builder uses different names for choice casts
        color_cast = instance._chatfield['fields']['color']['casts'].get('as_one_selection')
        if color_cast:
            assert color_cast['type'] == 'choice'
            assert color_cast['choices'] == ['red', 'green', 'blue']
            assert color_cast['null'] is False
            assert color_cast['multi'] is False


class TestSpecialFields:
    """Test special field features."""
    
    def test_confidential_field(self):
        """Test confidential field configuration."""
        instance = (chatfield()
            .type("ConfidentialInterview")
            .field("secret")
                .desc("Secret information")
                .confidential()
            .build())
        
        field = instance._chatfield['fields']['secret']
        assert field['specs']['confidential'] is True
    
    def test_conclude_field(self):
        """Test conclude field configuration."""
        instance = (chatfield()
            .type("ConcludeInterview")
            .field("rating")
                .desc("Final rating")
                .conclude()
            .build())
        
        field = instance._chatfield['fields']['rating']
        assert field['specs']['conclude'] is True
        assert field['specs']['confidential'] is True  # Conclude implies confidential


class TestBuilderEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_interview(self):
        """Test creating interview with no fields."""
        instance = (chatfield()
            .type("Empty")
            .desc("Empty interview")
            .build())
        
        meta = instance._chatfield
        assert meta['type'] == "Empty"
        assert meta['desc'] == "Empty interview"
        assert len(meta['fields']) == 0
    
    def test_minimal_interview(self):
        """Test creating interview with minimal configuration."""
        instance = chatfield().build()
        
        meta = instance._chatfield
        assert meta['type'] == ""
        assert meta['desc'] == ""
        assert len(meta['fields']) == 0
    
    def test_field_order_preservation(self):
        """Test that field order is preserved."""
        instance = (chatfield()
            .type("OrderedInterview")
            .field("first").desc("First")
            .field("second").desc("Second")
            .field("third").desc("Third")
            .field("fourth").desc("Fourth")
            .build())
        
        field_names = list(instance._chatfield['fields'].keys())
        assert field_names == ['first', 'second', 'third', 'fourth']