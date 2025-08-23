"""Test the Interview base class inheritance pattern."""

import pytest
from chatfield import Interview, must, reject, hint, alice, bob


class TestInterviewInheritancePattern:
    """Test the Interview base class inheritance pattern."""
    
    def test_simple_interview(self):
        """Test basic Interview inheritance."""
        class SimpleInterview(Interview):
            """Test interview"""
            def name(): "Your name"
            def email(): "Your email"
        
        # Create instance
        instance = SimpleInterview()
        meta = instance._chatfield
        
        # Should have metadata
        assert meta['desc'] == "Test interview"
        assert 'name' in meta['fields']
        assert 'email' in meta['fields']
    
    def test_interview_with_field_decorators(self):
        """Test Interview with field decorators."""
        class DecoratedInterview(Interview):
            """Test with decorators"""
            
            @must("be specific")
            @reject("vague")
            def problem(): "Your problem"
            
            @hint("Think carefully")
            def solution(): "Your solution"
        
        instance = DecoratedInterview()
        meta = instance._chatfield
        
        # Check problem field
        problem_field = meta['fields']['problem']
        assert "be specific" in problem_field['specs']['must']
        assert "vague" in problem_field['specs']['reject']
        
        # Check solution field
        solution_field = meta['fields']['solution']
        assert "Think carefully" in solution_field['specs']['hint']
    
    def test_interview_with_class_decorators(self):
        """Test Interview with class decorators."""
        @alice("Interviewer")
        @bob("Candidate")
        class DecoratedInterview(Interview):
            """Role-based interview"""
            def question(): "Your question"
        
        instance = DecoratedInterview()
        meta = instance._chatfield
        
        assert meta['roles']['alice']['type'] == "Interviewer"
        assert meta['roles']['bob']['type'] == "Candidate"
        assert 'question' in meta['fields']
    
    def test_complex_interview(self):
        """Test Interview with all decorator types."""
        @alice("Technical Interviewer")
        @alice.trait("thorough")
        @bob("Senior Developer")
        @bob.trait("experienced")
        class ComplexInterview(Interview):
            """Technical interview process"""
            
            @must("include specific examples")
            @reject("generic answers")
            @hint("Think about real-world scenarios")
            def experience(): "Describe your experience"
            
            @must("be measurable")
            def goals(): "Your career goals"
        
        instance = ComplexInterview()
        meta = instance._chatfield
        
        # Class metadata
        assert meta['desc'] == "Technical interview process"
        
        # Roles
        assert meta['roles']['alice']['type'] == "Technical Interviewer"
        assert "thorough" in meta['roles']['alice']['traits']
        assert meta['roles']['bob']['type'] == "Senior Developer"
        assert "experienced" in meta['roles']['bob']['traits']
        
        # Fields
        assert 'experience' in meta['fields']
        assert 'goals' in meta['fields']
        
        # Field decorators
        exp_field = meta['fields']['experience']
        assert "include specific examples" in exp_field['specs']['must']
        assert "generic answers" in exp_field['specs']['reject']
        assert "Think about real-world scenarios" in exp_field['specs']['hint']
        
        goals_field = meta['fields']['goals']
        assert "be measurable" in goals_field['specs']['must']
    
    def test_interview_inheritance_chain(self):
        """Test that Interview can be properly inherited."""
        class BaseInterview(Interview):
            """Base interview"""
            def base_field(): "Base question"
        
        class DerivedInterview(BaseInterview):
            """Derived interview"""
            def derived_field(): "Derived question"
        
        instance = DerivedInterview()
        meta = instance._chatfield
        
        # Should have both fields from inheritance
        assert 'base_field' in meta['fields']
        assert 'derived_field' in meta['fields']
        
        # Docstring from derived class
        assert meta['desc'] == "Derived interview"
    
    def test_interview_method_override(self):
        """Test that Interview methods can be overridden."""
        class CustomInterview(Interview):
            """Custom interview with override"""
            def field(): "Test field"
            
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.custom_attribute = "custom"
        
        instance = CustomInterview()
        assert instance.custom_attribute == "custom"
        assert 'field' in instance._chatfield['fields']