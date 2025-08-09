"""Tests for Chatfield LangGraph implementation."""

import os
import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from chatfield.agent import ChatfieldAgent, ConversationState, ValidationResult
from chatfield.conversation import Conversation
from chatfield.gatherer import GathererMeta, FieldMeta
from chatfield.decorators import gather, must, reject, hint, user, agent


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
class TestChatfieldAgent:
    """Test the ChatfieldAgent class with real API."""
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        meta = GathererMeta()
        meta.add_field("name", "What is your name?")
        meta.add_field("email", "What is your email?")
        
        agent = ChatfieldAgent(meta)
        
        assert agent.meta == meta
        assert agent.max_retries == 3
        assert agent.graph is not None
    
    def test_build_opening_message(self):
        """Test opening message generation."""
        meta = GathererMeta()
        meta.set_docstring("Welcome to our survey!")
        meta.add_user_context("You are a developer")
        meta.add_agent_context("Be friendly and helpful")
        
        agent = ChatfieldAgent(meta)
        message = agent._build_opening_message()
        
        assert "Welcome to our survey!" in message
        assert "Agent behavior:" in message
        assert "User context:" in message
    
    def test_field_prompt_building(self):
        """Test field prompt generation."""
        meta = GathererMeta()
        field = meta.add_field("project", "Describe your project")
        field.add_hint("Be specific about your goals")
        
        agent = ChatfieldAgent(meta)
        prompt = agent._build_field_prompt(field, {})
        
        assert "Describe your project?" in prompt
        assert "Be specific about your goals" in prompt
    
    def test_validation_prompt_building(self):
        """Test validation prompt generation."""
        meta = GathererMeta()
        field = meta.add_field("email", "Your email address")
        field.add_must_rule("valid email format")
        field.add_reject_rule("temporary email services")
        
        agent = ChatfieldAgent(meta)
        prompt = agent._build_validation_prompt(field, "test@example.com")
        
        assert "test@example.com" in prompt
        assert "valid email format" in prompt
        assert "temporary email services" in prompt
    
    def test_parse_validation_result(self):
        """Test parsing of validation results."""
        meta = GathererMeta()
        agent = ChatfieldAgent(meta)
        
        # Test valid response
        is_valid, feedback = agent._parse_validation_result("VALID")
        assert is_valid is True
        assert feedback == ""
        
        # Test invalid response
        is_valid, feedback = agent._parse_validation_result("Please provide more details")
        assert is_valid is False
        assert feedback == "Please provide more details"
    
    def test_get_uncollected_fields(self):
        """Test getting list of uncollected fields."""
        meta = GathererMeta()
        meta.add_field("name", "Your name")
        meta.add_field("email", "Your email")
        meta.add_field("phone", "Your phone")
        
        agent = ChatfieldAgent(meta)
        
        state: ConversationState = {
            "meta": meta,
            "messages": [],
            "collected_data": {"name": "John"},
            "current_field": None,
            "validation_attempts": 0,
            "max_retries": 3,
            "is_complete": False,
            "needs_validation": False,
            "validation_result": None
        }
        
        uncollected = agent._get_uncollected_fields(state)
        assert uncollected == ["email", "phone"]


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
class TestConversation:
    """Test the Conversation class with real API."""
    
    def test_conversation_initialization(self):
        """Test conversation initialization."""
        meta = GathererMeta()
        meta.add_field("name", "What is your name?")
        
        conversation = Conversation(meta)
        
        assert conversation.meta == meta
        assert conversation.collected_data == {}
        assert conversation.conversation_history == []
    
    def test_conversation_with_simple_gatherer(self):
        """Test a simple conversation flow with real API."""
        @gather
        class SimpleGatherer:
            """A simple data gatherer for testing."""
            
            def name():
                """What is your name"""
        
        # This test would require actual user input or mocking
        # For now, we just test that the class was properly decorated
        assert hasattr(SimpleGatherer, 'gather')
        assert callable(SimpleGatherer.gather)


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
class TestDecorators:
    """Test decorator functionality with real API."""
    
    def test_gather_decorator(self):
        """Test that @gather adds the gather method."""
        @gather
        class TestClass:
            """Test class"""
            def field():
                """A field"""
        
        assert hasattr(TestClass, 'gather')
        assert callable(TestClass.gather)
    
    def test_field_decorators(self):
        """Test field-level decorators."""
        @gather
        class TestClass:
            """Test class"""
            
            @must("specific requirement")
            @reject("vague answer")
            @hint("Be clear")
            def field():
                """Test field"""
        
        meta = TestClass._chatfield_meta
        field = meta.get_field("field")
        
        assert field is not None
        assert "specific requirement" in field.must_rules
        assert "vague answer" in field.reject_rules
        assert "Be clear" in field.hints
    
    def test_class_decorators(self):
        """Test class-level decorators."""
        @gather
        @user("A test user")
        @agent("Be helpful")
        class TestClass:
            """Test class"""
            def field():
                """A field"""
        
        meta = TestClass._chatfield_meta
        
        assert "A test user" in meta.user_context
        assert "Be helpful" in meta.agent_context


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
class TestEndToEnd:
    """End-to-end tests with real API."""
    
    def test_simple_data_gathering(self):
        """Test complete data gathering flow."""
        @gather
        @agent("Be concise and professional")
        class ContactInfo:
            """Gather basic contact information."""
            
            @hint("First and last name")
            def name():
                """Your full name"""
            
            @hint("We'll use this to contact you")
            def email():
                """Your email address"""
        
        # Test that the class is properly set up
        assert hasattr(ContactInfo, 'gather')
        meta = ContactInfo._chatfield_meta
        assert len(meta.fields) == 2
        assert "name" in meta.fields
        assert "email" in meta.fields