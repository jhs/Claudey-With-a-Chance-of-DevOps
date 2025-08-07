"""Unit tests for Chatfield conversation management."""

import pytest
from unittest.mock import Mock, patch
from chatfield.conversation import Conversation, ConversationMessage
from chatfield.gatherer import GathererMeta, FieldMeta
from chatfield.llm_backend import MockLLMBackend


class TestConversationMessage:
    """Test ConversationMessage class."""
    
    def test_message_creation(self):
        """Test creating a conversation message."""
        msg = ConversationMessage("user", "Hello there")
        assert msg.role == "user"
        assert msg.content == "Hello there"
    
    def test_message_repr(self):
        """Test message string representation."""
        msg = ConversationMessage("assistant", "This is a longer message")
        repr_str = repr(msg)
        assert "assistant:" in repr_str
        assert "This is a longer message" in repr_str


class TestConversation:
    """Test Conversation class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.meta = GathererMeta()
        self.meta.set_docstring("Test gatherer")
        self.meta.add_field("name", "Your name")
        self.meta.add_field("email", "Your email")
        
        self.mock_llm = MockLLMBackend()
        self.conversation = Conversation(self.meta, self.mock_llm)
    
    def test_conversation_creation(self):
        """Test creating a conversation."""
        assert self.conversation.meta == self.meta
        assert self.conversation.collected_data == {}
        assert self.conversation.conversation_history == []
        assert self.conversation.llm == self.mock_llm
    
    def test_get_next_field(self):
        """Test getting the next field to collect."""
        # Should return first field when none collected
        next_field = self.conversation.get_next_field()
        assert next_field.name == "name"
        
        # Collect first field
        self.conversation.collected_data["name"] = "John"
        
        # Should return second field
        next_field = self.conversation.get_next_field()
        assert next_field.name == "email"
        
        # Collect second field
        self.conversation.collected_data["email"] = "john@example.com"
        
        # Should return None when all collected
        next_field = self.conversation.get_next_field()
        assert next_field is None
    
    def test_get_uncollected_fields(self):
        """Test getting list of uncollected fields."""
        uncollected = self.conversation.get_uncollected_fields()
        assert uncollected == ["name", "email"]
        
        self.conversation.collected_data["name"] = "John"
        uncollected = self.conversation.get_uncollected_fields()
        assert uncollected == ["email"]
        
        self.conversation.collected_data["email"] = "john@example.com"
        uncollected = self.conversation.get_uncollected_fields()
        assert uncollected == []
    
    def test_validate_response_no_rules(self):
        """Test validation when field has no rules."""
        field = FieldMeta("name", "Your name")  # No validation rules
        
        is_valid, feedback = self.conversation.validate_response(field, "John Doe")
        assert is_valid is True
        assert feedback == ""
    
    def test_validate_response_with_rules(self):
        """Test validation with must/reject rules."""
        field = FieldMeta("email", "Your email")
        field.add_must_rule("valid email format")
        field.add_reject_rule("temporary emails")
        
        # Mock LLM to return valid
        self.mock_llm.add_validation_response("VALID")
        
        is_valid, feedback = self.conversation.validate_response(field, "john@example.com")
        assert is_valid is True
        assert feedback == ""
        
        # Mock LLM to return invalid
        self.mock_llm.add_validation_response("Invalid: not a proper email format")
        
        is_valid, feedback = self.conversation.validate_response(field, "invalid-email")
        assert is_valid is False
        assert "Invalid: not a proper email format" in feedback
    
    def test_build_validation_prompt(self):
        """Test building validation prompts."""
        field = FieldMeta("description", "Project description")
        field.add_must_rule("specific requirements")
        field.add_reject_rule("vague statements")
        
        prompt = self.conversation._build_validation_prompt(field, "We need a website")
        
        assert "We need a website" in prompt
        assert "Project description" in prompt
        assert "specific requirements" in prompt
        assert "vague statements" in prompt
        assert "VALID" in prompt
    
    def test_get_opening_message(self):
        """Test generating opening message."""
        # Test with docstring
        message = self.conversation._get_opening_message()
        assert "Test gatherer" in message
        
        # Test without docstring
        meta_no_doc = GathererMeta()
        conversation_no_doc = Conversation(meta_no_doc, self.mock_llm)
        message = conversation_no_doc._get_opening_message()
        assert "Let me ask you a few questions" in message
    
    def test_build_field_prompt(self):
        """Test building prompts for individual fields."""
        field = FieldMeta("name", "What is your name")
        
        # Test basic prompt
        prompt = self.conversation._build_field_prompt(field)
        assert "What is your name?" in prompt
        
        # Test with collected data context
        self.conversation.collected_data["email"] = "john@example.com"
        prompt = self.conversation._build_field_prompt(field)
        assert "email: john@example.com" in prompt.lower()
    
    def test_get_conversation_summary(self):
        """Test generating conversation summary."""
        # Empty summary
        summary = self.conversation.get_conversation_summary()
        assert "No data collected yet" in summary
        
        # With collected data
        self.conversation.collected_data["name"] = "John Doe"
        self.conversation.collected_data["email"] = "john@example.com"
        
        summary = self.conversation.get_conversation_summary()
        assert "Collected so far:" in summary
        assert "John Doe" in summary
        assert "john@example.com" in summary
    
    @patch('builtins.input', return_value='John Doe')
    @patch('builtins.print')
    def test_ask_about_field_success(self, mock_print, mock_input):
        """Test successfully asking about a field."""
        field = FieldMeta("name", "Your name")
        
        # Mock LLM to validate successfully
        self.mock_llm.add_validation_response("VALID")
        
        result = self.conversation._ask_about_field(field)
        
        assert result is True
        assert self.conversation.collected_data["name"] == "John Doe"
        assert len(self.conversation.conversation_history) == 1
        assert self.conversation.conversation_history[0].content == "John Doe"
    
    @patch('builtins.input', side_effect=['', 'invalid', 'John Doe'])
    @patch('builtins.print')
    def test_ask_about_field_retries(self, mock_print, mock_input):
        """Test field asking with retries."""
        field = FieldMeta("name", "Your name")
        field.add_must_rule("not empty")
        
        # Mock LLM responses: first invalid, then valid
        self.mock_llm.add_validation_response("Invalid: field cannot be empty")
        self.mock_llm.add_validation_response("VALID")
        
        result = self.conversation._ask_about_field(field)
        
        assert result is True
        assert self.conversation.collected_data["name"] == "John Doe"
    
    @patch('builtins.input', return_value='invalid')
    @patch('builtins.print')
    def test_ask_about_field_max_retries(self, mock_print, mock_input):
        """Test field asking with max retries exceeded."""
        field = FieldMeta("name", "Your name")
        field.add_must_rule("specific format")
        
        # Mock LLM to always return invalid
        for _ in range(5):
            self.mock_llm.add_validation_response("Invalid: wrong format")
        
        result = self.conversation._ask_about_field(field)
        
        assert result is False
        assert "name" not in self.conversation.collected_data


class TestConversationWithValidation:
    """Test conversation with complex validation scenarios."""
    
    def test_field_with_multiple_rules(self):
        """Test field with multiple must/reject rules."""
        meta = GathererMeta()
        field = meta.add_field("description", "Project description")
        field.add_must_rule("specific problem")
        field.add_must_rule("target audience")
        field.add_reject_rule("vague statements")
        field.add_reject_rule("unrealistic expectations")
        
        mock_llm = MockLLMBackend()
        conversation = Conversation(meta, mock_llm)
        
        prompt = conversation._build_validation_prompt(field, "We need a website")
        
        assert "specific problem" in prompt
        assert "target audience" in prompt
        assert "vague statements" in prompt
        assert "unrealistic expectations" in prompt
    
    def test_validation_error_handling(self):
        """Test handling of LLM validation errors."""
        meta = GathererMeta()
        field = meta.add_field("test", "Test field")
        field.add_must_rule("some rule")
        
        # Create a mock that raises an exception
        mock_llm = Mock()
        mock_llm.validate_response.side_effect = Exception("API Error")
        
        conversation = Conversation(meta, mock_llm)
        
        # Should handle exception gracefully and be permissive
        is_valid, feedback = conversation.validate_response(field, "test response")
        assert is_valid is True  # Should be permissive on error
        assert feedback == ""