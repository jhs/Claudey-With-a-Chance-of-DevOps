"""Test the Gatherer base class inheritance pattern."""

import pytest
from chatfield import Gatherer, must, reject, hint, user, agent
from chatfield.socrates import SocratesMeta


class TestGathererInheritance:
    """Test the Gatherer base class inheritance pattern."""
    
    def test_simple_gatherer(self):
        """Test basic Gatherer inheritance."""
        class SimpleGatherer(Gatherer):
            """Test gatherer"""
            def name(): "Your name"
            def email(): "Your email"
        
        # Should have gather method
        assert hasattr(SimpleGatherer, 'gather')
        assert callable(SimpleGatherer.gather)
        
        # Should have metadata
        meta = SimpleGatherer._get_meta()
        assert isinstance(meta, SocratesMeta)
        assert meta.docstring == "Test gatherer"
        assert 'name' in meta.fields
        assert 'email' in meta.fields
    
    def test_gatherer_with_field_decorators(self):
        """Test Gatherer with field decorators."""
        class DecoratedGatherer(Gatherer):
            """Test with decorators"""
            
            @must("be specific")
            @reject("vague")
            def problem(): "Your problem"
            
            @hint("Think carefully")
            def solution(): "Your solution"
        
        meta = DecoratedGatherer._get_meta()
        
        # Check problem field
        problem_field = meta.fields['problem']
        assert "be specific" in problem_field.must_rules
        assert "vague" in problem_field.reject_rules
        
        # Check solution field
        solution_field = meta.fields['solution']
        assert "Think carefully" in solution_field.hints
    
    def test_gatherer_with_class_decorators(self):
        """Test Gatherer with class-level decorators."""
        @user("Test user")
        @agent("Test agent")
        class ContextGatherer(Gatherer):
            """Test with context"""
            def field(): "Test field"
        
        meta = ContextGatherer._get_meta()
        assert "Test user" in meta.user_context
        assert "Test agent" in meta.agent_context
    
    
    def test_multiple_inheritance_levels(self):
        """Test inheritance from a Gatherer subclass."""
        class BaseGatherer(Gatherer):
            """Base gatherer"""
            def base_field(): "Base field"
        
        class DerivedGatherer(BaseGatherer):
            """Derived gatherer"""
            def derived_field(): "Derived field"
        
        # Both should have gather method
        assert hasattr(BaseGatherer, 'gather')
        assert hasattr(DerivedGatherer, 'gather')
        
        # Check metadata
        base_meta = BaseGatherer._get_meta()
        assert 'base_field' in base_meta.fields
        
        derived_meta = DerivedGatherer._get_meta()
        assert 'base_field' in derived_meta.fields
        assert 'derived_field' in derived_meta.fields
    
    def test_gatherer_with_match_decorators(self):
        """Test Gatherer with @match decorators."""
        from chatfield import match
        
        class MatchGatherer(Gatherer):
            """Test match decorators"""
            
            @match.personal("is personal")
            @match.work("is for work")
            def project_type(): "Project type"
        
        meta = MatchGatherer._get_meta()
        field_meta = meta.fields['project_type']
        
        # Check match rules are stored
        assert 'personal' in field_meta.match_rules
        assert field_meta.match_rules['personal']['criteria'] == "is personal"
        assert 'work' in field_meta.match_rules
        assert field_meta.match_rules['work']['criteria'] == "is for work"