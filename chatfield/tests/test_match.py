"""Tests for the @match decorator system."""

import pytest
from chatfield import Gatherer, must, reject
from chatfield.match import match
from chatfield.field_proxy import FieldValueProxy
from chatfield.socrates import FieldMeta, SocratesInstance


class TestMatchDecorator:
    """Test the @match decorator functionality."""
    
    def test_basic_match_decorator(self):
        """Test basic @match decorator usage."""
        class Example(Gatherer):
            @match.is_personal("mentions personal use")
            def purpose(): "What's your project for?"
        
        meta = Example._get_meta()
        field_meta = meta.fields["purpose"]
        
        assert "is_personal" in field_meta.match_rules
        assert field_meta.match_rules["is_personal"]["criteria"] == "mentions personal use"
        assert field_meta.match_rules["is_personal"]["type"] == "custom"
    
    def test_multiple_match_decorators(self):
        """Test multiple @match decorators on same field."""
        class Example(Gatherer):
            @match.is_personal("mentions personal use")
            @match.is_commercial("for business purposes")
            @match.is_educational("for learning")
            def purpose(): "What's your project for?"
        
        meta = Example._get_meta()
        field_meta = meta.fields["purpose"]
        
        assert len(field_meta.match_rules) == 3
        assert "is_personal" in field_meta.match_rules
        assert "is_commercial" in field_meta.match_rules
        assert "is_educational" in field_meta.match_rules
    
    def test_duplicate_match_name_raises_error(self):
        """Test that duplicate match names raise ValueError."""
        with pytest.raises(ValueError, match="Duplicate match name 'is_valid'"):
            class Example(Gatherer):
                @match.is_valid("checks validity")
                @match.is_valid("another validity check")
                def field(): "Test field"
    
    def test_match_with_must_reject(self):
        """Test @match works alongside @must and @reject."""
        class Example(Gatherer):
            @match.is_personal("personal project")
            @must("clear purpose")
            @reject("vague ideas")
            def purpose(): "What's your purpose?"
        
        meta = Example._get_meta()
        field_meta = meta.fields["purpose"]
        
        # Check custom match rule
        assert "is_personal" in field_meta.match_rules
        
        # Check must/reject are stored as match rules
        must_rules = [k for k in field_meta.match_rules if k.startswith("_must_")]
        reject_rules = [k for k in field_meta.match_rules if k.startswith("_reject_")]
        
        assert len(must_rules) == 1
        assert len(reject_rules) == 1
        
        # Check backward compatibility
        assert field_meta.get_must_rules() == ["clear purpose"]
        assert field_meta.get_reject_rules() == ["vague ideas"]


class TestMustRejectAsMatch:
    """Test that @must and @reject are implemented via @match."""
    
    def test_must_creates_match_rule(self):
        """Test @must creates internal match rule."""
        class Example(Gatherer):
            @must("specific requirement")
            def field(): "Test field"
        
        meta = Example._get_meta()
        field_meta = meta.fields["field"]
        
        # Should have one internal must match rule
        must_rules = [k for k in field_meta.match_rules if k.startswith("_must_")]
        assert len(must_rules) == 1
        
        match_id = must_rules[0]
        assert field_meta.match_rules[match_id]["criteria"] == "specific requirement"
        assert field_meta.match_rules[match_id]["expected"] is True
        assert field_meta.match_rules[match_id]["type"] == "must"
    
    def test_reject_creates_match_rule(self):
        """Test @reject creates internal match rule."""
        class Example(Gatherer):
            @reject("avoid this")
            def field(): "Test field"
        
        meta = Example._get_meta()
        field_meta = meta.fields["field"]
        
        # Should have one internal reject match rule
        reject_rules = [k for k in field_meta.match_rules if k.startswith("_reject_")]
        assert len(reject_rules) == 1
        
        match_id = reject_rules[0]
        assert field_meta.match_rules[match_id]["criteria"] == "avoid this"
        assert field_meta.match_rules[match_id]["expected"] is False
        assert field_meta.match_rules[match_id]["type"] == "reject"
    
    def test_duplicate_must_raises_error(self):
        """Test duplicate @must rules raise error."""
        with pytest.raises(ValueError, match="Duplicate @must rule"):
            class Example(Gatherer):
                @must("same rule")
                @must("same rule")
                def field(): "Test field"
    
    def test_duplicate_reject_raises_error(self):
        """Test duplicate @reject rules raise error."""
        with pytest.raises(ValueError, match="Duplicate @reject rule"):
            class Example(Gatherer):
                @reject("same rule")
                @reject("same rule")
                def field(): "Test field"
    
    def test_different_must_rules_allowed(self):
        """Test different @must rules are allowed."""
        class Example(Gatherer):
            @must("rule one")
            @must("rule two")
            @must("rule three")
            def field(): "Test field"
        
        meta = Example._get_meta()
        field_meta = meta.fields["field"]
        
        must_rules = [k for k in field_meta.match_rules if k.startswith("_must_")]
        assert len(must_rules) == 3
        
        # Check backward compatibility
        assert set(field_meta.get_must_rules()) == {"rule one", "rule two", "rule three"}


class TestFieldValueProxy:
    """Test the FieldValueProxy functionality."""
    
    def test_proxy_string_behavior(self):
        """Test proxy behaves like a string."""
        field_meta = FieldMeta(name="test", description="Test field")
        proxy = FieldValueProxy("test value", field_meta, {})
        
        assert str(proxy) == "test value"
        assert len(proxy) == 10
        assert proxy == "test value"
        assert bool(proxy) is True
    
    def test_proxy_match_attributes(self):
        """Test accessing match attributes on proxy."""
        field_meta = FieldMeta(
            name="purpose",
            description="Purpose",
            match_rules={
                "is_personal": {"criteria": "personal", "type": "custom"},
                "is_commercial": {"criteria": "commercial", "type": "custom"}
            }
        )
        
        evaluations = {
            "is_personal": True,
            "is_commercial": False
        }
        
        proxy = FieldValueProxy("my personal blog", field_meta, evaluations)
        
        assert proxy.is_personal is True
        assert proxy.is_commercial is False
    
    def test_proxy_nonexistent_match_raises_error(self):
        """Test accessing non-existent match raises AttributeError."""
        field_meta = FieldMeta(name="test", description="Test")
        proxy = FieldValueProxy("value", field_meta, {})
        
        with pytest.raises(AttributeError, match="has no match rule 'is_valid'"):
            _ = proxy.is_valid
    
    def test_proxy_internal_rules_not_accessible(self):
        """Test internal must/reject rules are not accessible."""
        field_meta = FieldMeta(
            name="test",
            description="Test",
            match_rules={
                "_must_123abc": {"criteria": "must rule", "type": "must"},
                "_reject_456def": {"criteria": "reject rule", "type": "reject"}
            }
        )
        
        proxy = FieldValueProxy("value", field_meta, {})
        
        with pytest.raises(AttributeError, match="Internal validation rule"):
            _ = proxy._must_123abc
        
        with pytest.raises(AttributeError, match="Internal validation rule"):
            _ = proxy._reject_456def


class TestSocratesInstanceWithProxy:
    """Test SocratesInstance returns FieldValueProxy objects."""
    
    def test_instance_returns_proxy(self):
        """Test that SocratesInstance returns proxy objects."""
        from chatfield.socrates import SocratesMeta
        
        meta = SocratesMeta()
        field_meta = meta.add_field("purpose", "What's your purpose?")
        field_meta.match_rules = {
            "is_personal": {"criteria": "personal", "type": "custom"}
        }
        
        evaluations = {
            "purpose": {"is_personal": True}
        }
        
        instance = SocratesInstance(meta, {"purpose": "personal blog"}, evaluations)
        
        # Should return a FieldValueProxy
        purpose = instance.purpose
        assert isinstance(purpose, FieldValueProxy)
        assert str(purpose) == "personal blog"
        assert purpose.is_personal is True