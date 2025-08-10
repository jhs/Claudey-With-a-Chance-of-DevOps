"""Tests for field presence indicating validity (None = invalid, any string = valid)."""

import pytest
from chatfield.field_proxy import FieldValueProxy
from chatfield.socrates import FieldMeta, SocratesInstance, process_socrates_class
from chatfield import Gatherer, must, reject
from chatfield.match import match


class TestFieldPresence:
    """Test suite for field presence as validity indicator."""
    
    def test_none_means_invalid(self):
        """Test that None indicates field is invalid/not collected."""
        class TestForm(Gatherer):
            """Test form"""
            def name():
                """Your name"""
                pass
            def email():
                """Your email"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {})  # No data collected
        
        # Uncollected fields should return None
        assert instance.name is None
        assert instance.email is None
    
    def test_empty_string_is_valid(self):
        """Test that empty string is a valid collected value."""
        class TestForm(Gatherer):
            """Test form"""
            def name():
                """Your name"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {"name": ""})  # Empty string collected
        
        # Empty string is valid (user explicitly said N/A or similar)
        assert instance.name is not None
        assert str(instance.name) == ""
    
    def test_whitespace_only_is_valid(self):
        """Test that whitespace-only string is a valid collected value."""
        class TestForm(Gatherer):
            """Test form"""
            def description():
                """Description"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {"description": "   "})  # Whitespace only
        
        # Whitespace is valid (user provided something, even if just spaces)
        assert instance.description is not None
        assert str(instance.description) == "   "
    
    def test_explicit_na_is_valid(self):
        """Test that user explicitly saying N/A is valid."""
        class TestForm(Gatherer):
            """Test form"""
            def notes():
                """Additional notes"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {"notes": "N/A"})
        
        # "N/A" is valid - user explicitly provided this response
        assert instance.notes is not None
        assert str(instance.notes) == "N/A"
    
    def test_actual_content_is_valid(self):
        """Test that fields with actual content are valid."""
        class TestForm(Gatherer):
            """Test form"""
            def project():
                """Project description"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {"project": "Building a web app"})
        
        # Content is valid
        assert instance.project is not None
        assert str(instance.project) == "Building a web app"
    
    def test_mixed_collected_and_uncollected(self):
        """Test instance with some collected and some uncollected fields."""
        class TestForm(Gatherer):
            """Test form"""
            def name():
                """Your name"""
                pass
            def email():
                """Your email"""
                pass
            def phone():
                """Your phone"""
                pass
        
        meta = process_socrates_class(TestForm)
        # Only name and email collected
        instance = SocratesInstance(meta, {
            "name": "John Doe",
            "email": ""  # Empty but collected
        })
        
        # Collected fields (including empty) are not None
        assert instance.name is not None
        assert str(instance.name) == "John Doe"
        assert instance.email is not None
        assert str(instance.email) == ""
        
        # Uncollected field is None
        assert instance.phone is None
    
    def test_field_with_validation_rules_none_when_not_collected(self):
        """Test that fields with @must/@reject rules are None when not collected."""
        class TestForm(Gatherer):
            """Test form"""
            
            @must("include timeline")
            @reject("vague statements")
            def proposal():
                """Your project proposal"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {})  # Nothing collected
        
        # Field with validation rules is None when not collected
        assert instance.proposal is None
    
    def test_field_with_validation_rules_not_none_when_collected(self):
        """Test that fields with @must/@reject rules are not None when collected."""
        class TestForm(Gatherer):
            """Test form"""
            
            @must("include timeline")
            @reject("vague statements")
            def proposal():
                """Your project proposal"""
                pass
        
        meta = process_socrates_class(TestForm)
        # Field passed validation and was collected
        instance = SocratesInstance(meta, {"proposal": "Q1 2024 launch"})
        
        # Field with validation rules is not None when collected
        assert instance.proposal is not None
        assert str(instance.proposal) == "Q1 2024 launch"
    
    def test_checking_validity_with_is_not_none(self):
        """Test that we can check field validity using 'is not None'."""
        class TestForm(Gatherer):
            """Test form"""
            def required_field():
                """Required information"""
                pass
            def optional_field():
                """Optional information"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {"required_field": "Data"})
        
        # Can check validity with is not None
        if instance.required_field is not None:
            # Field is valid, can use it
            value = str(instance.required_field)
            assert value == "Data"
        
        if instance.optional_field is None:
            # Field is not valid/not collected
            assert True  # This branch should execute
        else:
            assert False  # Should not get here
    
    def test_field_proxy_still_works_for_collected_fields(self):
        """Test that FieldValueProxy features still work for collected fields."""
        class TestForm(Gatherer):
            """Test form"""
            
            @match.is_corporate("sounds like a company")
            def entity():
                """Entity name"""
                pass
        
        meta = process_socrates_class(TestForm)
        
        # Set up match evaluations
        match_evals = {
            "entity": {"is_corporate": True}
        }
        
        instance = SocratesInstance(meta, {"entity": "Acme Corp"}, match_evals)
        
        # Field is not None (valid)
        assert instance.entity is not None
        
        # Can still access match attributes
        assert instance.entity.is_corporate == True
        
        # String conversion still works
        assert str(instance.entity) == "Acme Corp"
    
    def test_unknown_field_raises_attribute_error(self):
        """Test that accessing unknown fields raises AttributeError."""
        class TestForm(Gatherer):
            """Test form"""
            def name():
                """Your name"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {"name": "John"})
        
        # Known field works
        assert instance.name is not None
        
        # Unknown field raises AttributeError
        with pytest.raises(AttributeError) as exc_info:
            _ = instance.unknown_field
        
        assert "'SocratesInstance' object has no attribute 'unknown_field'" in str(exc_info.value)
    
    def test_get_method_with_none_fields(self):
        """Test the get() method returns None for uncollected fields."""
        class TestForm(Gatherer):
            """Test form"""
            def field1():
                """Field 1"""
                pass
            def field2():
                """Field 2"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {"field1": "value1"})
        
        # get() returns the value for collected fields
        assert instance.get("field1") is not None
        assert str(instance.get("field1")) == "value1"
        
        # get() returns default (None) for uncollected fields
        assert instance.get("field2") is None
        assert instance.get("field2", "default") == "default"
    
    def test_distinction_between_none_and_empty(self):
        """Explicitly test the distinction between None (not discussed) and "" (discussed as N/A)."""
        class TestForm(Gatherer):
            """Test form"""
            def not_discussed():
                """Field not discussed yet"""
                pass
            def discussed_as_na():
                """Field discussed, user said N/A"""
                pass
            def discussed_with_value():
                """Field discussed with actual value"""
                pass
        
        meta = process_socrates_class(TestForm)
        instance = SocratesInstance(meta, {
            "discussed_as_na": "",  # User explicitly provided empty/N/A
            "discussed_with_value": "Some content"
        })
        
        # Not discussed = None = invalid
        assert instance.not_discussed is None
        
        # Discussed as N/A = "" = valid
        assert instance.discussed_as_na is not None
        assert str(instance.discussed_as_na) == ""
        
        # Discussed with value = valid
        assert instance.discussed_with_value is not None
        assert str(instance.discussed_with_value) == "Some content"
        
        # Can distinguish between the three states
        fields_status = []
        for field_name in ["not_discussed", "discussed_as_na", "discussed_with_value"]:
            field_value = getattr(instance, field_name)
            if field_value is None:
                fields_status.append(f"{field_name}: not discussed")
            elif str(field_value) == "":
                fields_status.append(f"{field_name}: explicitly N/A")
            else:
                fields_status.append(f"{field_name}: has value")
        
        assert fields_status == [
            "not_discussed: not discussed",
            "discussed_as_na: explicitly N/A", 
            "discussed_with_value: has value"
        ]