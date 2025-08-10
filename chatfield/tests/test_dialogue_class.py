"""Test the Dialogue base class inheritance pattern."""

import pytest
from chatfield import Dialogue, must, reject, hint, user, agent
from chatfield.socrates import SocratesMeta


class TestDialogueInheritance:
    """Test the Dialogue base class inheritance pattern."""
    
    def test_simple_dialogue(self):
        """Test basic Dialogue inheritance."""
        class SimpleDialogue(Dialogue):
            """Test dialogue"""
            def name(): "Your name"
            def email(): "Your email"
        
        # Should have gather method
        assert hasattr(SimpleDialogue, 'gather')
        assert callable(SimpleDialogue.gather)
        
        # Should have metadata
        meta = SimpleDialogue._get_meta()
        assert isinstance(meta, SocratesMeta)
        assert meta.docstring == "Test dialogue"
        assert 'name' in meta.fields
        assert 'email' in meta.fields
    
    def test_dialogue_with_field_decorators(self):
        """Test Dialogue with field decorators."""
        class DecoratedDialogue(Dialogue):
            """Test with decorators"""
            
            @must("be specific")
            @reject("vague")
            def problem(): "Your problem"
            
            @hint("Think carefully")
            def solution(): "Your solution"
        
        meta = DecoratedDialogue._get_meta()
        
        # Check problem field
        problem_field = meta.fields['problem']
        assert "be specific" in problem_field.must_rules
        assert "vague" in problem_field.reject_rules
        
        # Check solution field
        solution_field = meta.fields['solution']
        assert "Think carefully" in solution_field.hints
    
    def test_dialogue_with_class_decorators(self):
        """Test Dialogue with class-level decorators."""
        @user("Test user")
        @agent("Test agent")
        class ContextDialogue(Dialogue):
            """Test with context"""
            def field(): "Test field"
        
        meta = ContextDialogue._get_meta()
        assert "Test user" in meta.user_context
        assert "Test agent" in meta.agent_context
    
    
    def test_multiple_inheritance_levels(self):
        """Test inheritance from a Dialogue subclass."""
        class BaseDialogue(Dialogue):
            """Base dialogue"""
            def base_field(): "Base field"
        
        class DerivedDialogue(BaseDialogue):
            """Derived dialogue"""
            def derived_field(): "Derived field"
        
        # Both should have gather method
        assert hasattr(BaseDialogue, 'gather')
        assert hasattr(DerivedDialogue, 'gather')
        
        # Check metadata
        base_meta = BaseDialogue._get_meta()
        assert 'base_field' in base_meta.fields
        
        derived_meta = DerivedDialogue._get_meta()
        assert 'base_field' in derived_meta.fields
        assert 'derived_field' in derived_meta.fields
    
    def test_dialogue_with_match_decorators(self):
        """Test Dialogue with @match decorators."""
        from chatfield import match
        
        class MatchDialogue(Dialogue):
            """Test match decorators"""
            
            @match.personal("is personal")
            @match.work("is for work")
            def project_type(): "Project type"
        
        meta = MatchDialogue._get_meta()
        field_meta = meta.fields['project_type']
        
        # Check match rules are stored
        assert 'personal' in field_meta.match_rules
        assert field_meta.match_rules['personal']['criteria'] == "is personal"
        assert 'work' in field_meta.match_rules
        assert field_meta.match_rules['work']['criteria'] == "is for work"