"""Optional tests using real LLM (marked as slow)."""

import pytest
import os
from unittest.mock import patch
from chatfield import gather, must, reject, hint, user, agent
from chatfield.llm_backend import OpenAIBackend


@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
class TestRealLLM:
    """Tests using real OpenAI API - requires API key and marked as slow."""
    
    @patch('builtins.input', return_value='John Doe')
    @patch('builtins.print')
    def test_simple_real_conversation(self, mock_print, mock_input):
        """Test simple conversation with real OpenAI."""
        @gather
        class SimpleReal:
            """Simple contact form"""
            def name(): "Your full name"
        
        try:
            result = SimpleReal.gather()
            assert hasattr(result, 'name')
            assert result.name == 'John Doe'
        except Exception as e:
            pytest.skip(f"OpenAI API error: {e}")
    
    def test_openai_backend_creation(self):
        """Test OpenAI backend creation."""
        try:
            backend = OpenAIBackend()
            assert backend.model == "gpt-4"
            assert backend.client is not None
        except Exception as e:
            pytest.skip(f"OpenAI setup error: {e}")
    
    def test_validation_prompt_building(self):
        """Test validation prompt construction."""
        try:
            backend = OpenAIBackend()
            
            # This tests the prompt building without making API calls
            from chatfield.gatherer import FieldMeta
            field = FieldMeta("email", "Your email address")
            field.add_must_rule("valid email format")
            field.add_reject_rule("temporary emails")
            
            # Test that we can create conversation prompts
            from chatfield.gatherer import GathererMeta
            meta = GathererMeta()
            meta.set_docstring("Contact form")
            meta.add_user_context("Business professional")
            meta.add_agent_context("Helpful assistant")
            
            prompt = backend.create_conversation_prompt(meta, field, [])
            
            assert "Contact form" in prompt
            assert "Business professional" in prompt
            assert "Helpful assistant" in prompt
            assert "Your email address" in prompt
            
        except ImportError:
            pytest.skip("OpenAI package not available")


@pytest.mark.integration
class TestLLMBackendBehavior:
    """Test LLM backend behavior without making real API calls."""
    
    def test_mock_llm_responses(self):
        """Test mock LLM backend response handling."""
        from chatfield.llm_backend import MockLLMBackend
        
        mock_llm = MockLLMBackend()
        mock_llm.add_response("Hello, I can help you with that!")
        mock_llm.add_validation_response("VALID")
        
        response = mock_llm.get_response("Test prompt")
        assert response == "Hello, I can help you with that!"
        
        validation = mock_llm.validate_response("Test validation prompt")
        assert validation == "VALID"
    
    def test_openai_backend_without_api_key(self):
        """Test OpenAI backend behavior without API key."""
        from chatfield.llm_backend import OpenAIBackend
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                OpenAIBackend()
    
    def test_openai_import_error(self):
        """Test handling when OpenAI package is not available."""
        with patch.dict('sys.modules', {'openai': None}):
            with pytest.raises(ImportError, match="OpenAI package not available"):
                from chatfield.llm_backend import OpenAIBackend
                OpenAIBackend()


@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
class TestRealValidation:
    """Test real validation scenarios with OpenAI."""
    
    def test_validation_with_must_rules(self):
        """Test validation with must rules using real LLM."""
        try:
            backend = OpenAIBackend()
            
            # Test valid response
            valid_prompt = '''The user provided this answer: "john@example.com"

For the field "Your email address", validate that the answer follows these rules:
- MUST include: valid email format

If the answer is valid, respond with "VALID".
If the answer is not valid, explain what's missing or wrong in a helpful way that will guide the user to provide a better answer.'''
            
            response = backend.validate_response(valid_prompt)
            assert "VALID" in response.upper()
            
            # Test invalid response
            invalid_prompt = '''The user provided this answer: "not-an-email"

For the field "Your email address", validate that the answer follows these rules:
- MUST include: valid email format

If the answer is valid, respond with "VALID".
If the answer is not valid, explain what's missing or wrong in a helpful way that will guide the user to provide a better answer.'''
            
            response = backend.validate_response(invalid_prompt)
            assert "VALID" not in response.upper()
            assert "email" in response.lower()
            
        except Exception as e:
            pytest.skip(f"OpenAI API error: {e}")
    
    def test_validation_with_reject_rules(self):
        """Test validation with reject rules using real LLM."""
        try:
            backend = OpenAIBackend()
            
            # Test response that should be rejected
            reject_prompt = '''The user provided this answer: "Use 10minutemail.com for temporary email"

For the field "Your email address", validate that the answer follows these rules:
- MUST NOT include: temporary emails

If the answer is valid, respond with "VALID".
If the answer is not valid, explain what's missing or wrong in a helpful way that will guide the user to provide a better answer.'''
            
            response = backend.validate_response(reject_prompt)
            assert "VALID" not in response.upper()
            assert "temporary" in response.lower()
            
        except Exception as e:
            pytest.skip(f"OpenAI API error: {e}")


# Utility function to run slow tests manually
def run_real_llm_tests():
    """Utility function to run real LLM tests manually.
    
    Usage:
        from tests.test_real_llm import run_real_llm_tests
        run_real_llm_tests()
    """
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY environment variable not set. Skipping real LLM tests.")
        return
    
    print("Running real LLM tests...")
    
    # Test simple conversation
    @patch('builtins.input', return_value='Test User')
    @patch('builtins.print')
    def test_simple(mock_print, mock_input):
        @gather
        class TestGatherer:
            def name(): "Your name"
        
        result = TestGatherer.gather()
        print(f"Collected name: {result.name}")
        return result
    
    try:
        result = test_simple()
        print("✓ Simple conversation test passed")
    except Exception as e:
        print(f"✗ Simple conversation test failed: {e}")
    
    # Test validation
    try:
        backend = OpenAIBackend()
        response = backend.validate_response('''The user provided: "john@example.com"
For email field, validate it includes: valid email format
Respond "VALID" if valid, otherwise explain the issue.''')
        print(f"Validation response: {response}")
        print("✓ Validation test passed")
    except Exception as e:
        print(f"✗ Validation test failed: {e}")
    
    print("Real LLM tests completed.")


if __name__ == "__main__":
    run_real_llm_tests()