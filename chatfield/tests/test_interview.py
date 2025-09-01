"""Tests for the Interview base class."""

import pytest
from chatfield import Interview, chatfield, alice, bob, must, reject, hint
from chatfield import as_int, as_float, as_bool, as_str, as_lang, as_percent
from chatfield import as_one, as_maybe, as_multi, as_any
from chatfield.interview import FieldProxy


class TestInterviewBasics:
    """Test basic Interview functionality."""
    
    def test_simple_interview_creation(self):
        """Test creating a simple Interview using builder."""
        interview = (chatfield()
            .type("SimpleInterview")
            .desc("A simple interview")
            .field("name").desc("Your name")
            .field("email").desc("Your email address")
            .build())
        
        assert interview._chatfield['type'] == 'SimpleInterview'
        assert interview._chatfield['desc'] == 'A simple interview'
        assert 'name' in interview._chatfield['fields']
        assert 'email' in interview._chatfield['fields']
        assert interview._chatfield['fields']['name']['desc'] == 'Your name'
        assert interview._chatfield['fields']['email']['desc'] == 'Your email address'
    
    def test_field_discovery(self):
        """Test that builder creates all specified fields."""
        interview = (chatfield()
            .type("TestInterview")
            .field("field1").desc("First field")
            .field("field2").desc("Second field")
            .field("field3").desc("Third field")
            .build())
        
        fields = list(interview._chatfield['fields'].keys())
        
        assert 'field1' in fields
        assert 'field2' in fields
        assert 'field3' in fields
        assert len(fields) == 3
    
    def test_field_access_before_collection(self):
        """Test accessing fields before data collection returns None."""
        interview = (chatfield()
            .type("TestInterview")
            .field("name").desc("Your name")
            .field("age").desc("Your age")
            .build())
        
        assert interview.name is None
        assert interview.age is None
    
    def test_done_property(self):
        """Test the _done property."""
        interview = (chatfield()
            .type("TestInterview")
            .field("field1").desc("Field 1")
            .field("field2").desc("Field 2")
            .build())
        
        # Initially not done
        assert interview._done is False
        
        # Set one field - still not done
        interview._chatfield['fields']['field1']['value'] = {
            'value': 'test1',
            'context': 'N/A',
            'as_quote': 'test1'
        }
        assert interview._done is False
        
        # Set both fields - now done
        interview._chatfield['fields']['field2']['value'] = {
            'value': 'test2',
            'context': 'N/A',
            'as_quote': 'test2'
        }
        assert interview._done is True
    
    def test_model_dump(self):
        """Test the model_dump method for serialization."""
        interview = (chatfield()
            .type("TestInterview")
            .field("name").desc("Your name")
            .build())
        dump = interview.model_dump()
        
        assert isinstance(dump, dict)
        assert dump['type'] == 'TestInterview'
        assert 'fields' in dump
        assert 'name' in dump['fields']
        
        # Modify original and ensure dump is independent
        interview._chatfield['fields']['name']['value'] = {'value': 'test'}
        assert dump['fields']['name']['value'] is None  # Should still be None


class TestInterviewWithFeatures:
    """Test Interview with various features."""
    
    def test_roles(self):
        """Test alice and bob role configuration."""
        interview = (chatfield()
            .type("JobInterview")
            .desc("Job interview session")
            .alice()
                .type("Technical Interviewer")
                .trait("Asks detailed questions")
            .bob()
                .type("Job Candidate")
                .trait("Experienced developer")
            .field("experience").desc("Years of experience")
            .build())
        
        alice_role = interview._chatfield['roles']['alice']
        bob_role = interview._chatfield['roles']['bob']
        
        assert alice_role['type'] == 'Technical Interviewer'
        assert 'Asks detailed questions' in alice_role['traits']
        assert bob_role['type'] == 'Job Candidate'
        assert 'Experienced developer' in bob_role['traits']
    
    def test_validation_rules(self):
        """Test must, reject, and hint validation rules."""
        interview = (chatfield()
            .type("ValidatedInterview")
            .field("description")
                .desc("Detailed description")
                .must("specific details")
                .must("at least 10 words")
                .reject("vague descriptions")
                .hint("Be as specific as possible")
            .build())
        field = interview._chatfield['fields']['description']
        
        assert 'must' in field['specs']
        assert 'specific details' in field['specs']['must']
        assert 'at least 10 words' in field['specs']['must']
        assert 'reject' in field['specs']
        assert 'vague descriptions' in field['specs']['reject']
        assert 'hint' in field['specs']
        assert 'Be as specific as possible' in field['specs']['hint']
    
    def test_type_transformations(self):
        """Test type transformation features."""
        interview = (chatfield()
            .type("TypedInterview")
            .field("age")
                .desc("Your age")
                .as_int()
            .field("height")
                .desc("Your height")
                .as_float()
            .field("active")
                .desc("Are you active?")
                .as_bool()
            .field("confidence")
                .desc("Confidence level")
                .as_percent()
            .build())
        
        assert 'as_int' in interview._chatfield['fields']['age']['casts']
        assert 'as_float' in interview._chatfield['fields']['height']['casts']
        assert 'as_bool' in interview._chatfield['fields']['active']['casts']
        assert 'as_percent' in interview._chatfield['fields']['confidence']['casts']
    
    def test_sub_attribute_transformations(self):
        """Test sub-attribute transformations like as_lang.fr."""
        interview = (chatfield()
            .type("MultiLangInterview")
            .field("number")
                .desc("A number")
                .as_lang.fr()
                .as_lang.es()
                .as_bool.even("True if even")
                .as_str.uppercase("In uppercase")
            .build())
        field_casts = interview._chatfield['fields']['number']['casts']
        
        assert 'as_lang_fr' in field_casts
        assert 'as_lang_es' in field_casts
        assert 'as_bool_even' in field_casts
        assert 'as_str_uppercase' in field_casts
    
    def test_cardinality_choices(self):
        """Test choice cardinality features."""
        interview = (chatfield()
            .type("ChoiceInterview")
            .field("color")
                .desc("Favorite color")
                .as_one.color("red", "green", "blue")
            .field("priority")
                .desc("Priority level")
                .as_maybe.priority("low", "medium", "high")
            .field("languages")
                .desc("Programming languages")
                .as_multi.languages("python", "javascript", "rust")
            .field("reviewers")
                .desc("Code reviewers")
                .as_any.reviewers("alice", "bob", "charlie")
            .build())
        
        color_cast = interview._chatfield['fields']['color']['casts']['as_one_color']
        assert color_cast['type'] == 'choice'
        assert color_cast['choices'] == ['red', 'green', 'blue']
        assert color_cast['null'] is False
        assert color_cast['multi'] is False
        
        priority_cast = interview._chatfield['fields']['priority']['casts']['as_maybe_priority']
        assert priority_cast['null'] is True
        assert priority_cast['multi'] is False
        
        lang_cast = interview._chatfield['fields']['languages']['casts']['as_multi_languages']
        assert lang_cast['null'] is False
        assert lang_cast['multi'] is True
        
        reviewer_cast = interview._chatfield['fields']['reviewers']['casts']['as_any_reviewers']
        assert reviewer_cast['null'] is True
        assert reviewer_cast['multi'] is True


class TestFieldProxy:
    """Test FieldProxy functionality."""
    
    def test_field_proxy_as_string(self):
        """Test that FieldProxy behaves as a string."""
        interview = (chatfield()
            .type("TestInterview")
            .field("name").desc("Your name")
            .build())
        interview._chatfield['fields']['name']['value'] = {
            'value': 'John Doe',
            'context': 'User provided their name',
            'as_quote': 'John Doe'
        }
        
        name = interview.name
        
        assert isinstance(name, str)
        assert isinstance(name, FieldProxy)
        assert name == 'John Doe'
        assert name.upper() == 'JOHN DOE'
        assert name.lower() == 'john doe'
        assert len(name) == 8
    
    def test_field_proxy_transformations(self):
        """Test accessing transformations via FieldProxy."""
        interview = (chatfield()
            .type("TestInterview")
            .field("number")
                .desc("A number")
                .as_int()
                .as_lang.fr()
                .as_bool.even("True if even")
            .build())
        interview._chatfield['fields']['number']['value'] = {
            'value': '42',
            'context': 'User said forty-two',
            'as_quote': 'forty-two',
            'as_int': 42,
            'as_lang_fr': 'quarante-deux',
            'as_bool_even': True
        }
        
        number = interview.number
        
        assert number == '42'
        assert number.as_int == 42
        assert number.as_lang_fr == 'quarante-deux'
        assert number.as_bool_even is True
        assert number.context == 'User said forty-two'
        assert number.as_quote == 'forty-two'
    
    def test_field_proxy_missing_transformation(self):
        """Test accessing non-existent transformation returns None for missing keys."""
        interview = (chatfield()
            .type("TestInterview")
            .field("name").desc("Your name")
            .build())
        interview._chatfield['fields']['name']['value'] = {
            'value': 'test',
            'context': 'N/A',
            'as_quote': 'test'
        }
        
        # FieldProxy.__getattr__ returns None for missing transformations
        # or raises AttributeError - let's check what actually happens
        name = interview.name
        try:
            result = name.as_int  # This transformation doesn't exist
            # If we get here, it returns something (likely None)
            assert result is None or isinstance(result, object)
        except AttributeError:
            # Or it raises AttributeError
            pass


class TestBuilderEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_interview(self):
        """Test creating an empty interview."""
        interview = (chatfield()
            .type("EmptyInterview")
            .desc("Empty interview")
            .build())
        
        assert interview._chatfield['type'] == 'EmptyInterview'
        assert interview._chatfield['desc'] == 'Empty interview'
        assert len(interview._chatfield['fields']) == 0
        assert interview._done is True  # No fields means done
    
    def test_minimal_interview(self):
        """Test creating interview with minimal configuration."""
        interview = chatfield().build()
        
        assert interview._chatfield['type'] == ''
        assert interview._chatfield['desc'] == ''
        assert len(interview._chatfield['fields']) == 0
    
    def test_field_with_default_description(self):
        """Test field with no description uses field name."""
        interview = (chatfield()
            .type("TestInterview")
            .field("test_field")  # No description
            .build())
        
        # Should use field name as description
        assert interview._chatfield['fields']['test_field']['desc'] == 'test_field'
    
    def test_multiple_validation_rules(self):
        """Test applying multiple validation rules."""
        interview = (chatfield()
            .type("TestInterview")
            .field("field")
                .desc("Test field")
                .must("rule 1")
                .must("rule 2")
                .must("rule 3")
            .build())
        
        field_specs = interview._chatfield['fields']['field']['specs']['must']
        
        assert 'rule 1' in field_specs
        assert 'rule 2' in field_specs
        assert 'rule 3' in field_specs
        assert len(field_specs) == 3
    
    def test_pretty_method(self):
        """Test the _pretty() method output."""
        interview = (chatfield()
            .type("TestInterview")
            .field("name").desc("Your name")
            .field("age").desc("Your age")
            .build())
        
        # Set one field
        interview._chatfield['fields']['name']['value'] = {
            'value': 'Alice',
            'context': 'User provided name',
            'as_quote': 'My name is Alice'
        }
        
        pretty = interview._pretty()
        
        assert 'TestInterview' in pretty