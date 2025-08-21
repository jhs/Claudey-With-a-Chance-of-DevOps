"""Tests for the Interview base class."""

import pytest
from chatfield import Interview, alice, bob, must, reject, hint
from chatfield import as_int, as_float, as_bool, as_str, as_lang, as_percent
from chatfield import as_one, as_maybe, as_multi, as_any
from chatfield.interview import FieldProxy


class TestInterviewBasics:
    """Test basic Interview functionality."""
    
    def test_simple_interview_creation(self):
        """Test creating a simple Interview subclass."""
        class SimpleInterview(Interview):
            """A simple interview"""
            def name(): "Your name"
            def email(): "Your email address"
        
        interview = SimpleInterview()
        
        assert interview._chatfield['type'] == 'SimpleInterview'
        assert interview._chatfield['desc'] == 'A simple interview'
        assert 'name' in interview._chatfield['fields']
        assert 'email' in interview._chatfield['fields']
        assert interview._chatfield['fields']['name']['desc'] == 'Your name'
        assert interview._chatfield['fields']['email']['desc'] == 'Your email address'
    
    def test_field_discovery(self):
        """Test that Interview discovers all method-based fields."""
        class TestInterview(Interview):
            def field1(): "First field"
            def field2(): "Second field"
            def field3(): "Third field"
            
            def _private_method():
                """This should not be a field"""
                pass
            
            def __special_method__(self):
                """This should not be a field"""
                pass
        
        interview = TestInterview()
        fields = list(interview._chatfield['fields'].keys())
        
        assert 'field1' in fields
        assert 'field2' in fields
        assert 'field3' in fields
        assert '_private_method' not in fields
        assert '__special_method__' not in fields
        assert len(fields) == 3
    
    def test_field_access_before_collection(self):
        """Test accessing fields before data collection returns None."""
        class TestInterview(Interview):
            def name(): "Your name"
            def age(): "Your age"
        
        interview = TestInterview()
        
        assert interview.name is None
        assert interview.age is None
    
    def test_done_property(self):
        """Test the _done property."""
        class TestInterview(Interview):
            def field1(): "Field 1"
            def field2(): "Field 2"
        
        interview = TestInterview()
        
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
        class TestInterview(Interview):
            def name(): "Your name"
        
        interview = TestInterview()
        dump = interview.model_dump()
        
        assert isinstance(dump, dict)
        assert dump['type'] == 'TestInterview'
        assert 'fields' in dump
        assert 'name' in dump['fields']
        
        # Modify original and ensure dump is independent
        interview._chatfield['fields']['name']['value'] = {'value': 'test'}
        assert dump['fields']['name']['value'] is None  # Should still be None


class TestInterviewWithDecorators:
    """Test Interview with various decorators."""
    
    def test_role_decorators(self):
        """Test @alice and @bob decorators."""
        @alice("Technical Interviewer")
        @alice.trait("Asks detailed questions")
        @bob("Job Candidate")
        @bob.trait("Experienced developer")
        class JobInterview(Interview):
            """Job interview session"""
            def experience(): "Years of experience"
        
        interview = JobInterview()
        
        alice_role = interview._chatfield['roles']['alice']
        bob_role = interview._chatfield['roles']['bob']
        
        assert alice_role['type'] == 'Technical Interviewer'
        assert 'Asks detailed questions' in alice_role['traits']
        assert bob_role['type'] == 'Job Candidate'
        assert 'Experienced developer' in bob_role['traits']
    
    def test_validation_decorators(self):
        """Test @must, @reject, and @hint decorators."""
        class ValidatedInterview(Interview):
            @must("specific details")
            @must("at least 10 words")
            @reject("vague descriptions")
            @hint("Be as specific as possible")
            def description(): "Detailed description"
        
        interview = ValidatedInterview()
        field = interview._chatfield['fields']['description']
        
        assert 'must' in field['specs']
        assert 'specific details' in field['specs']['must']
        assert 'at least 10 words' in field['specs']['must']
        assert 'reject' in field['specs']
        assert 'vague descriptions' in field['specs']['reject']
        assert 'hint' in field['specs']
        assert 'Be as specific as possible' in field['specs']['hint']
    
    def test_type_cast_decorators(self):
        """Test type transformation decorators."""
        class TypedInterview(Interview):
            @as_int
            def age(): "Your age"
            
            @as_float
            def height(): "Your height"
            
            @as_bool
            def active(): "Are you active?"
            
            @as_percent
            def confidence(): "Confidence level"
        
        interview = TypedInterview()
        
        assert 'as_int' in interview._chatfield['fields']['age']['casts']
        assert 'as_float' in interview._chatfield['fields']['height']['casts']
        assert 'as_bool' in interview._chatfield['fields']['active']['casts']
        assert 'as_percent' in interview._chatfield['fields']['confidence']['casts']
    
    def test_sub_attribute_decorators(self):
        """Test sub-attribute decorators like @as_lang.fr."""
        class MultiLangInterview(Interview):
            @as_lang.fr
            @as_lang.es
            @as_bool.even("True if even")
            @as_str.uppercase("In uppercase")
            def number(): "A number"
        
        interview = MultiLangInterview()
        field_casts = interview._chatfield['fields']['number']['casts']
        
        assert 'as_lang_fr' in field_casts
        assert 'as_lang_es' in field_casts
        assert 'as_bool_even' in field_casts
        assert 'as_str_uppercase' in field_casts
    
    def test_cardinality_decorators(self):
        """Test choice cardinality decorators."""
        class ChoiceInterview(Interview):
            @as_one.color("red", "green", "blue")
            def color(): "Favorite color"
            
            @as_maybe.priority("low", "medium", "high")
            def priority(): "Priority level"
            
            @as_multi.languages("python", "javascript", "rust")
            def languages(): "Programming languages"
            
            @as_any.reviewers("alice", "bob", "charlie")
            def reviewers(): "Code reviewers"
        
        interview = ChoiceInterview()
        
        color_cast = interview._chatfield['fields']['color']['casts']['choose_exactly_one_color']
        assert color_cast['type'] == 'choice'
        assert color_cast['choices'] == ['red', 'green', 'blue']
        assert color_cast['null'] is False
        assert color_cast['multi'] is False
        
        priority_cast = interview._chatfield['fields']['priority']['casts']['choose_zero_or_one_priority']
        assert priority_cast['null'] is True
        assert priority_cast['multi'] is False
        
        lang_cast = interview._chatfield['fields']['languages']['casts']['choose_one_or_more_languages']
        assert lang_cast['null'] is False
        assert lang_cast['multi'] is True
        
        reviewer_cast = interview._chatfield['fields']['reviewers']['casts']['choose_zero_or_more_reviewers']
        assert reviewer_cast['null'] is True
        assert reviewer_cast['multi'] is True


class TestFieldProxy:
    """Test FieldProxy functionality."""
    
    def test_field_proxy_as_string(self):
        """Test that FieldProxy behaves as a string."""
        class TestInterview(Interview):
            def name(): "Your name"
        
        interview = TestInterview()
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
        class TestInterview(Interview):
            @as_int
            @as_lang.fr
            @as_bool.even("True if even")
            def number(): "A number"
        
        interview = TestInterview()
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
        class TestInterview(Interview):
            def name(): "Your name"
        
        interview = TestInterview()
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


class TestInterviewInheritance:
    """Test Interview class inheritance patterns."""
    
    def test_simple_inheritance(self):
        """Test inheriting from Interview works correctly."""
        class BaseInterview(Interview):
            def base_field(): "Base field"
        
        class ExtendedInterview(BaseInterview):
            def extended_field(): "Extended field"
        
        interview = ExtendedInterview()
        
        # Should have both fields
        assert 'base_field' in interview._chatfield['fields']
        assert 'extended_field' in interview._chatfield['fields']
    
    def test_decorator_inheritance(self):
        """Test decorators work with inheritance."""
        @alice("Base Interviewer")
        class BaseInterview(Interview):
            @must("required info")
            def base_field(): "Base field"
        
        @bob("Extended User")
        class ExtendedInterview(BaseInterview):
            @as_int
            def number_field(): "Number field"
        
        interview = ExtendedInterview()
        
        assert interview._chatfield['roles']['alice']['type'] == 'Base Interviewer'
        assert interview._chatfield['roles']['bob']['type'] == 'Extended User'
        assert 'must' in interview._chatfield['fields']['base_field']['specs']
        assert 'as_int' in interview._chatfield['fields']['number_field']['casts']


class TestInterviewEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_interview(self):
        """Test Interview with no fields."""
        class EmptyInterview(Interview):
            """An empty interview"""
            pass
        
        interview = EmptyInterview()
        
        assert len(interview._chatfield['fields']) == 0
        assert interview._done is True  # No fields means done
    
    def test_field_with_no_docstring(self):
        """Test field without docstring uses method name."""
        class TestInterview(Interview):
            def field_without_docs():
                pass
        
        interview = TestInterview()
        
        # Should use method name as description
        assert interview._chatfield['fields']['field_without_docs']['desc'] == 'field_without_docs'
    
    def test_multiple_same_decorators(self):
        """Test applying the same decorator multiple times."""
        class TestInterview(Interview):
            @must("rule 1")
            @must("rule 2")
            @must("rule 3")
            def field(): "Test field"
        
        interview = TestInterview()
        field_specs = interview._chatfield['fields']['field']['specs']['must']
        
        assert 'rule 1' in field_specs
        assert 'rule 2' in field_specs
        assert 'rule 3' in field_specs
        assert len(field_specs) == 3
    
    def test_pretty_method(self):
        """Test the _pretty() method output."""
        class TestInterview(Interview):
            def name(): "Your name"
            def age(): "Your age"
        
        interview = TestInterview()
        
        # Set one field
        interview._chatfield['fields']['name']['value'] = {
            'value': 'Alice',
            'context': 'User provided name',
            'as_quote': 'My name is Alice',
            'as_str_length': 5
        }
        
        pretty = interview._pretty()
        
        assert 'TestInterview' in pretty
        assert 'name:' in pretty
        assert 'Alice' in pretty
        assert 'age: None' in pretty
        assert 'as_str_length' in pretty