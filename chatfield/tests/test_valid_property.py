"""Tests for the .valid property on field values."""

import pytest
from chatfield.field_proxy import FieldValueProxy
from chatfield.socrates import FieldMeta
from chatfield.match import match
from chatfield.decorators import gather, must, reject


class TestValidProperty:
    """Test suite for the .valid property functionality."""
    
    def test_valid_property_all_must_rules_pass(self):
        """Test that .valid returns True when all @must rules are satisfied."""
        # Create field metadata with must rules
        field_meta = FieldMeta(name="description", description="Project description")
        field_meta.match_rules = {
            "_must_001": {"criteria": "includes timeline", "expected": True, "type": "must"},
            "_must_002": {"criteria": "mentions budget", "expected": True, "type": "must"}
        }
        
        # Create proxy with all must rules satisfied
        evaluations = {
            "_must_001": True,  # Timeline included
            "_must_002": True   # Budget mentioned
        }
        proxy = FieldValueProxy("Q1 2024 project with $50k budget", field_meta, evaluations)
        
        # Should be valid
        assert proxy.valid is True
    
    def test_valid_property_must_rule_fails(self):
        """Test that .valid returns False when a @must rule is not satisfied."""
        # Create field metadata with must rules
        field_meta = FieldMeta(name="description", description="Project description")
        field_meta.match_rules = {
            "_must_001": {"criteria": "includes timeline", "expected": True, "type": "must"},
            "_must_002": {"criteria": "mentions budget", "expected": True, "type": "must"}
        }
        
        # Create proxy with one must rule not satisfied
        evaluations = {
            "_must_001": True,   # Timeline included
            "_must_002": False   # Budget NOT mentioned
        }
        proxy = FieldValueProxy("Q1 2024 project details", field_meta, evaluations)
        
        # Should be invalid
        assert proxy.valid is False
    
    def test_valid_property_all_reject_rules_pass(self):
        """Test that .valid returns True when all @reject rules are satisfied."""
        # Create field metadata with reject rules
        field_meta = FieldMeta(name="email", description="Email address")
        field_meta.match_rules = {
            "_reject_001": {"criteria": "contains profanity", "expected": False, "type": "reject"},
            "_reject_002": {"criteria": "is disposable email", "expected": False, "type": "reject"}
        }
        
        # Create proxy with all reject rules satisfied (no bad content)
        evaluations = {
            "_reject_001": False,  # No profanity
            "_reject_002": False   # Not disposable
        }
        proxy = FieldValueProxy("user@company.com", field_meta, evaluations)
        
        # Should be valid
        assert proxy.valid is True
    
    def test_valid_property_reject_rule_fails(self):
        """Test that .valid returns False when a @reject rule is violated."""
        # Create field metadata with reject rules
        field_meta = FieldMeta(name="email", description="Email address")
        field_meta.match_rules = {
            "_reject_001": {"criteria": "contains profanity", "expected": False, "type": "reject"},
            "_reject_002": {"criteria": "is disposable email", "expected": False, "type": "reject"}
        }
        
        # Create proxy with reject rule violated
        evaluations = {
            "_reject_001": False,  # No profanity
            "_reject_002": True    # IS disposable (violates reject rule)
        }
        proxy = FieldValueProxy("user@tempmail.com", field_meta, evaluations)
        
        # Should be invalid
        assert proxy.valid is False
    
    def test_valid_property_mixed_must_and_reject(self):
        """Test .valid with both @must and @reject rules."""
        # Create field metadata with both must and reject rules
        field_meta = FieldMeta(name="proposal", description="Project proposal")
        field_meta.match_rules = {
            "_must_001": {"criteria": "includes objectives", "expected": True, "type": "must"},
            "_must_002": {"criteria": "has timeline", "expected": True, "type": "must"},
            "_reject_001": {"criteria": "contains jargon", "expected": False, "type": "reject"},
            "_reject_002": {"criteria": "is vague", "expected": False, "type": "reject"}
        }
        
        # All rules satisfied
        evaluations = {
            "_must_001": True,   # Has objectives
            "_must_002": True,   # Has timeline
            "_reject_001": False, # No jargon
            "_reject_002": False  # Not vague
        }
        proxy = FieldValueProxy("Clear objectives for Q1 2024", field_meta, evaluations)
        assert proxy.valid is True
        
        # One must rule fails
        evaluations["_must_001"] = False
        proxy = FieldValueProxy("Timeline for Q1 2024", field_meta, evaluations)
        assert proxy.valid is False
        
        # One reject rule fails (reset must rule)
        evaluations["_must_001"] = True
        evaluations["_reject_001"] = True  # Contains jargon
        proxy = FieldValueProxy("Synergize objectives for Q1", field_meta, evaluations)
        assert proxy.valid is False
    
    def test_valid_property_unevaluated_rules(self):
        """Test that .valid returns False when rules haven't been evaluated."""
        # Create field metadata with rules
        field_meta = FieldMeta(name="description", description="Description")
        field_meta.match_rules = {
            "_must_001": {"criteria": "complete", "expected": True, "type": "must"}
        }
        
        # Create proxy with no evaluations
        proxy = FieldValueProxy("Some text", field_meta, {})
        
        # Should be invalid (rule not evaluated)
        assert proxy.valid is False
        
        # Partially evaluated
        field_meta.match_rules["_must_002"] = {"criteria": "detailed", "expected": True, "type": "must"}
        evaluations = {"_must_001": True}  # Only one rule evaluated
        proxy = FieldValueProxy("Complete text", field_meta, evaluations)
        
        # Should be invalid (not all rules evaluated)
        assert proxy.valid is False
    
    def test_valid_property_no_validation_rules(self):
        """Test that .valid returns True when there are no validation rules."""
        # Create field metadata with no must/reject rules
        field_meta = FieldMeta(name="name", description="Your name")
        
        # Add a custom match rule (not must/reject)
        field_meta.match_rules = {
            "is_corporate": {"criteria": "sounds like company name", "expected": None, "type": "custom"}
        }
        
        evaluations = {"is_corporate": True}
        proxy = FieldValueProxy("John Doe", field_meta, evaluations)
        
        # Should be valid (no must/reject rules to check)
        assert proxy.valid is True
    
    def test_valid_property_is_read_only(self):
        """Test that the .valid property cannot be set."""
        field_meta = FieldMeta(name="test", description="Test field")
        proxy = FieldValueProxy("test value", field_meta, {})
        
        # Try to set the valid property - should raise AttributeError
        with pytest.raises(AttributeError) as exc_info:
            proxy.valid = True
        
        assert "Cannot set 'valid' attribute" in str(exc_info.value)
        assert "automatically based on its @must and @reject validation rules" in str(exc_info.value)
    
    def test_match_valid_decorator_raises_error(self):
        """Test that @match.valid() raises an error."""
        # Try to use @match.valid as a decorator
        with pytest.raises(AttributeError) as exc_info:
            @match.valid("some criteria")
            def field():
                """Field description"""
                pass
        
        assert "Cannot use 'valid' as a match name" in str(exc_info.value)
        assert "reserved for checking if all @must and @reject validation rules pass" in str(exc_info.value)
    
    def test_valid_property_with_gather_class(self):
        """Test .valid property in the context of a full @gather class."""
        @gather
        class TestForm:
            """Test form with validation"""
            
            @must("include email")
            @must("include phone")
            @reject("profanity")
            def contact():
                """Your contact information"""
                pass
        
        # Simulate a gathered instance
        from chatfield.socrates import SocratesInstance, process_socrates_class
        
        meta = process_socrates_class(TestForm)
        
        # Simulate collected data with evaluations
        collected_data = {"contact": "Email: test@example.com, Phone: 555-1234"}
        
        # Get the field meta for contact
        contact_field = meta.get_field("contact")
        
        # Verify the match rules were created
        assert len([k for k in contact_field.match_rules if k.startswith("_must_")]) == 2
        assert len([k for k in contact_field.match_rules if k.startswith("_reject_")]) == 1
        
        # Create evaluations for all rules
        evaluations = {}
        for rule_name, rule_config in contact_field.match_rules.items():
            if rule_config["type"] == "must":
                evaluations[rule_name] = True  # All must rules pass
            elif rule_config["type"] == "reject":
                evaluations[rule_name] = False  # All reject rules pass
        
        # Create instance with evaluations
        instance = SocratesInstance(meta, collected_data, {"contact": evaluations})
        
        # Access the contact field and check validity
        contact_value = instance.contact
        assert contact_value.valid is True
        
        # Now simulate a failed validation
        evaluations_failed = evaluations.copy()
        # Make one must rule fail
        must_rule_key = next(k for k in evaluations if k.startswith("_must_"))
        evaluations_failed[must_rule_key] = False
        
        instance_failed = SocratesInstance(meta, collected_data, {"contact": evaluations_failed})
        contact_failed = instance_failed.contact
        assert contact_failed.valid is False