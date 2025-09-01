"""Test the Interview base class inheritance pattern."""

import pytest
from chatfield import Interview, chatfield, must, reject, hint, alice, bob


class TestInterviewInheritancePattern:
    """Test the Interview base class inheritance pattern."""
    
    def test_simple_interview(self):
        """Test basic Interview using builder pattern."""
        instance = (chatfield()
            .type("SimpleInterview")
            .desc("Test interview")
            .field("name").desc("Your name")
            .field("email").desc("Your email")
            .build())
        
        meta = instance._chatfield
        
        # Should have metadata
        assert meta['desc'] == "Test interview"
        assert 'name' in meta['fields']
        assert 'email' in meta['fields']
    
    def test_interview_with_field_decorators(self):
        """Test Interview with field validation using builder pattern."""
        instance = (chatfield()
            .type("DecoratedInterview")
            .desc("Test with decorators")
            .field("problem")
                .desc("Your problem")
                .must("be specific")
                .reject("vague")
            .field("solution")
                .desc("Your solution")
                .hint("Think carefully")
            .build())
        
        meta = instance._chatfield
        
        # Check problem field
        problem_field = meta['fields']['problem']
        assert "be specific" in problem_field['specs']['must']
        assert "vague" in problem_field['specs']['reject']
        
        # Check solution field
        solution_field = meta['fields']['solution']
        assert "Think carefully" in solution_field['specs']['hint']
    
    def test_interview_with_class_decorators(self):
        """Test Interview with roles using builder pattern."""
        instance = (chatfield()
            .type("DecoratedInterview")
            .desc("Role-based interview")
            .alice().type("Interviewer")
            .bob().type("Candidate")
            .field("question").desc("Your question")
            .build())
        
        meta = instance._chatfield
        
        assert meta['roles']['alice']['type'] == "Interviewer"
        assert meta['roles']['bob']['type'] == "Candidate"
        assert 'question' in meta['fields']
    
    def test_complex_interview(self):
        """Test Interview with all builder features."""
        instance = (chatfield()
            .type("ComplexInterview")
            .desc("Technical interview process")
            .alice()
                .type("Technical Interviewer")
                .trait("thorough")
            .bob()
                .type("Senior Developer")
                .trait("experienced")
            .field("experience")
                .desc("Describe your experience")
                .must("include specific examples")
                .reject("generic answers")
                .hint("Think about real-world scenarios")
            .field("goals")
                .desc("Your career goals")
                .must("be measurable")
            .build())
        
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
    
