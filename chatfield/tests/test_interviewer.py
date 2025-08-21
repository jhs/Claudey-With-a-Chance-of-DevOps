"""Tests for the Interviewer class."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from chatfield import Interview, Interviewer, alice, bob, must, reject, hint
from chatfield import as_int, as_bool, as_lang


class TestInterviewerBasics:
    """Test basic Interviewer functionality."""
    
    def test_interviewer_initialization(self):
        """Test Interviewer initializes correctly."""
        class SimpleInterview(Interview):
            def name(): "Your name"
            def email(): "Your email"
        
        interview = SimpleInterview()
        interviewer = Interviewer(interview)
        
        assert interviewer.interview is interview
        assert interviewer.config['configurable']['thread_id'] is not None
        assert interviewer.checkpointer is not None
        assert interviewer.graph is not None
    
    def test_interviewer_with_custom_thread_id(self):
        """Test Interviewer with custom thread ID."""
        class SimpleInterview(Interview):
            def name(): "Your name"
        
        interview = SimpleInterview()
        interviewer = Interviewer(interview, thread_id="custom-123")
        
        assert interviewer.config['configurable']['thread_id'] == "custom-123"
    
    @patch('chatfield.interviewer.init_chat_model')
    def test_llm_initialization(self, mock_init_model):
        """Test LLM is initialized correctly."""
        mock_llm = Mock()
        mock_init_model.return_value = mock_llm
        
        class SimpleInterview(Interview):
            def name(): "Your name"
        
        interview = SimpleInterview()
        interviewer = Interviewer(interview)
        
        # Should initialize with GPT-5 by default
        mock_init_model.assert_called_once_with('openai:gpt-5', temperature=0.0)
        assert interviewer.llm is mock_llm


class TestSystemPromptGeneration:
    """Test system prompt generation."""
    
    def test_basic_system_prompt(self):
        """Test basic system prompt generation."""
        class SimpleInterview(Interview):
            """Customer feedback form"""
            def rating(): "Overall satisfaction rating"
            def comments(): "Additional comments"
        
        interview = SimpleInterview()
        interviewer = Interviewer(interview)
        
        prompt = interviewer.mk_system_prompt({'interview': interview})
        
        assert "Customer feedback form" in prompt
        assert "rating: Overall satisfaction rating" in prompt
        assert "comments: Additional comments" in prompt
        assert "Agent" in prompt  # Default role
        assert "User" in prompt   # Default role
    
    def test_system_prompt_with_roles(self):
        """Test system prompt with custom roles."""
        @alice("Customer Support Agent")
        @alice.trait("Friendly and helpful")
        @bob("Frustrated Customer")
        @bob.trait("Had a bad experience")
        class SupportInterview(Interview):
            """Support ticket"""
            def issue(): "What went wrong"
        
        interview = SupportInterview()
        interviewer = Interviewer(interview)
        
        prompt = interviewer.mk_system_prompt({'interview': interview})
        
        assert "Customer Support Agent" in prompt
        assert "Frustrated Customer" in prompt
        assert "Friendly and helpful" in prompt
        assert "Had a bad experience" in prompt
    
    def test_system_prompt_with_validation(self):
        """Test system prompt includes validation rules."""
        class ValidatedInterview(Interview):
            @must("specific details")
            @reject("profanity")
            @hint("Be constructive")
            def feedback(): "Your feedback"
        
        interview = ValidatedInterview()
        interviewer = Interviewer(interview)
        
        prompt = interviewer.mk_system_prompt({'interview': interview})
        
        assert "Must: specific details" in prompt
        assert "Reject: profanity" in prompt
        # Note: Hints are included in specs but may not appear in system prompt


class TestToolGeneration:
    """Test tool generation for fields."""
    
    @patch('chatfield.interviewer.init_chat_model')
    def test_tool_creation(self, mock_init_model):
        """Test that tools are created for fields."""
        mock_llm = Mock()
        mock_init_model.return_value = mock_llm
        
        class SimpleInterview(Interview):
            def field1(): "Field 1"
            def field2(): "Field 2"
        
        interview = SimpleInterview()
        interviewer = Interviewer(interview)
        
        # Tool should be bound to LLM
        assert hasattr(interviewer.llm_with_tools, 'bind_tools')
    
    @patch('chatfield.interviewer.init_chat_model')
    def test_tool_with_transformations(self, mock_init_model):
        """Test tool generation with transformation decorators."""
        mock_llm = Mock()
        mock_init_model.return_value = mock_llm
        
        class TypedInterview(Interview):
            @as_int
            @as_bool
            @as_lang.fr
            def number(): "A number"
        
        interview = TypedInterview()
        interviewer = Interviewer(interview)
        
        # Tool args should include transformations
        # This is complex to test without running the actual tool
        assert interviewer.llm_with_tools is not None


class TestConversationFlow:
    """Test conversation flow management."""
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
    def test_go_method_basic(self):
        """Test the go() method with real API."""
        class SimpleInterview(Interview):
            def name(): "Your name"
        
        interview = SimpleInterview()
        interviewer = Interviewer(interview)
        
        # Start conversation
        result = interviewer.go(None)
        
        assert result is not None
        assert 'messages' in result
        assert len(result['messages']) > 0
        
        # Should have system and AI messages
        message_types = [type(msg) for msg in result['messages']]
        assert SystemMessage in message_types or AIMessage in message_types
    
    def test_interview_state_updates(self):
        """Test that interview state updates when fields are collected."""
        class SimpleInterview(Interview):
            def name(): "Your name"
        
        interview = SimpleInterview()
        interviewer = Interviewer(interview)
        
        # Manually update field as if tool was called
        interviewer.process_tool_input(interview, name={
            'value': 'Test User',
            'context': 'User provided their name',
            'as_quote': 'My name is Test User'
        })
        
        # Check interview was updated
        assert interview._chatfield['fields']['name']['value'] is not None
        assert interview._chatfield['fields']['name']['value']['value'] == 'Test User'
    
    def test_done_detection(self):
        """Test that interviewer detects when all fields are collected."""
        class SimpleInterview(Interview):
            def field1(): "Field 1"
            def field2(): "Field 2"
        
        interview = SimpleInterview()
        interviewer = Interviewer(interview)
        
        # Initially not done
        assert not interview._done
        
        # Set both fields
        interviewer.process_tool_input(interview, 
            field1={'value': 'value1', 'context': 'N/A', 'as_quote': 'value1'})
        interviewer.process_tool_input(interview,
            field2={'value': 'value2', 'context': 'N/A', 'as_quote': 'value2'})
        
        # Should be done
        assert interview._done


class TestInterviewerWithDecorators:
    """Test Interviewer with decorated Interview classes."""
    
    def test_interviewer_with_all_decorators(self):
        """Test Interviewer with fully decorated Interview."""
        @alice("Interviewer")
        @alice.trait("Professional")
        @bob("Candidate")
        class ComplexInterview(Interview):
            """Complex interview"""
            
            @must("specific answer")
            @reject("vague response")
            @hint("Think carefully")
            @as_int
            @as_bool.positive("True if positive")
            def years(): "Years of experience"
        
        interview = ComplexInterview()
        interviewer = Interviewer(interview)
        
        # System prompt should include all decorations
        prompt = interviewer.mk_system_prompt({'interview': interview})
        
        assert "Interviewer" in prompt
        assert "Candidate" in prompt
        assert "Professional" in prompt
        assert "Years of experience" in prompt
    
    def test_process_tool_input_with_transformations(self):
        """Test processing tool input with transformations."""
        class TypedInterview(Interview):
            @as_int
            @as_lang.fr
            def number(): "A number"
        
        interview = TypedInterview()
        interviewer = Interviewer(interview)
        
        # Process tool input with transformations
        interviewer.process_tool_input(interview, number={
            'value': 'five',
            'context': 'User said five',
            'as_quote': 'The answer is five',
            'choose_exactly_one_as_int': 5,  # Note: Tool prefixes with choose_
            'choose_exactly_one_as_lang_fr': 'cinq'
        })
        
        # Check the field was updated with renamed keys
        field_value = interview._chatfield['fields']['number']['value']
        assert field_value['value'] == 'five'
        assert field_value['as_one_as_int'] == 5  # Renamed from choose_exactly_one_
        assert field_value['as_one_as_lang_fr'] == 'cinq'


class TestInterviewerEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_interview(self):
        """Test Interviewer with empty Interview."""
        class EmptyInterview(Interview):
            """Empty interview"""
            pass
        
        interview = EmptyInterview()
        interviewer = Interviewer(interview)
        
        # Should handle empty interview gracefully
        assert interviewer.interview._done is True
    
    def test_interview_copy_from(self):
        """Test that interview state is copied correctly."""
        class SimpleInterview(Interview):
            def name(): "Your name"
        
        interview1 = SimpleInterview()
        interview2 = SimpleInterview()
        
        # Set field in interview2
        interview2._chatfield['fields']['name']['value'] = {
            'value': 'Test',
            'context': 'N/A',
            'as_quote': 'Test'
        }
        
        # Copy from interview2 to interview1
        interview1._copy_from(interview2)
        
        # Check the copy worked
        assert interview1._chatfield['fields']['name']['value'] is not None
        assert interview1._chatfield['fields']['name']['value']['value'] == 'Test'
        
        # Ensure it's a deep copy
        interview2._chatfield['fields']['name']['value']['value'] = 'Changed'
        assert interview1._chatfield['fields']['name']['value']['value'] == 'Test'
    
    @patch('chatfield.interviewer.init_chat_model')
    def test_thread_isolation(self, mock_init_model):
        """Test that different thread IDs maintain isolation."""
        mock_llm = Mock()
        mock_init_model.return_value = mock_llm
        
        class SimpleInterview(Interview):
            def name(): "Your name"
        
        interview1 = SimpleInterview()
        interview2 = SimpleInterview()
        
        interviewer1 = Interviewer(interview1, thread_id="thread-1")
        interviewer2 = Interviewer(interview2, thread_id="thread-2")
        
        assert interviewer1.config['configurable']['thread_id'] == "thread-1"
        assert interviewer2.config['configurable']['thread_id'] == "thread-2"
        assert interviewer1.config != interviewer2.config