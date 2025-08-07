"""Integration tests for Chatfield using mock LLM."""

import pytest
from unittest.mock import patch, Mock
from chatfield import gather, must, reject, hint, user, agent
from chatfield import patient_teacher, quick_diagnosis, friendly_expert
from chatfield.llm_backend import MockLLMBackend
from chatfield.builder import GathererBuilder, create_gatherer_from_dict, create_gatherer_from_template


class TestBasicIntegration:
    """Test basic end-to-end functionality."""
    
    @patch('builtins.input', return_value='John Doe')
    @patch('builtins.print')
    def test_simple_gatherer(self, mock_print, mock_input):
        """Test a simple gatherer end-to-end."""
        @gather
        class Simple:
            def name(): "Your name"
        
        # Mock the LLM backend
        with patch('chatfield.conversation.OpenAIBackend', MockLLMBackend):
            result = Simple.gather()
        
        assert hasattr(result, 'name')
        assert result.name == 'John Doe'
        assert result.get('name') == 'John Doe'
    
    @patch('builtins.input', side_effect=['John Doe', 'john@example.com'])
    @patch('builtins.print')
    def test_multiple_fields(self, mock_print, mock_input):
        """Test gatherer with multiple fields."""
        @gather
        class MultiField:
            """Contact information"""
            def name(): "Your name"
            def email(): "Your email"
        
        with patch('chatfield.conversation.OpenAIBackend', MockLLMBackend):
            result = MultiField.gather()
        
        assert result.name == 'John Doe'
        assert result.email == 'john@example.com'
        
        data = result.get_data()
        assert data == {'name': 'John Doe', 'email': 'john@example.com'}


class TestValidationIntegration:
    """Test validation functionality integration."""
    
    @patch('builtins.input', return_value='detailed project description with specific requirements')
    @patch('builtins.print')
    def test_field_with_validation(self, mock_print, mock_input):
        """Test field with must/reject rules."""
        @gather
        class WithValidation:
            """Project planning"""
            @must("specific requirements")
            def description(): "Project description"
        
        # Mock LLM backend that validates successfully
        mock_llm = MockLLMBackend()
        mock_llm.add_validation_response("VALID")
        
        with patch('chatfield.conversation.OpenAIBackend', return_value=mock_llm):
            result = WithValidation.gather()
        
        assert result.description == 'detailed project description with specific requirements'
    
    @patch('builtins.input', side_effect=['vague description', 'detailed specific requirements'])
    @patch('builtins.print')
    def test_validation_retry(self, mock_print, mock_input):
        """Test validation with retry on failure."""
        @gather
        class WithRetry:
            @must("specific requirements")
            def description(): "Project description"
        
        # Mock LLM responses: first invalid, then valid
        mock_llm = MockLLMBackend()
        mock_llm.add_validation_response("Invalid: too vague, please be more specific")
        mock_llm.add_validation_response("VALID")
        
        with patch('chatfield.conversation.OpenAIBackend', return_value=mock_llm):
            result = WithRetry.gather()
        
        assert result.description == 'detailed specific requirements'


class TestContextIntegration:
    """Test user and agent context integration."""
    
    @patch('builtins.input', return_value='I need help with my computer')
    @patch('builtins.print')
    def test_user_agent_context(self, mock_print, mock_input):
        """Test gatherer with user and agent context."""
        @user("Small business owner")
        @user("Not very technical")
        @agent("Friendly tech support")
        @agent("Use simple language")
        @gather
        class TechSupport:
            """Technical support request"""
            def problem(): "What's the problem with your computer?"
        
        with patch('chatfield.conversation.OpenAIBackend', MockLLMBackend):
            result = TechSupport.gather()
        
        # Verify the context is stored in metadata
        meta = TechSupport._chatfield_meta
        assert "Small business owner" in meta.user_context
        assert "Not very technical" in meta.user_context
        assert "Friendly tech support" in meta.agent_context
        assert "Use simple language" in meta.agent_context
        
        assert result.problem == 'I need help with my computer'


class TestPresetIntegration:
    """Test preset decorator integration."""
    
    @patch('builtins.input', return_value='My email is not working')
    @patch('builtins.print')
    def test_patient_teacher_preset(self, mock_print, mock_input):
        """Test patient_teacher preset."""
        @patient_teacher
        @gather
        class Learning:
            """Learning about email"""
            def issue(): "What email issue are you having?"
        
        with patch('chatfield.conversation.OpenAIBackend', MockLLMBackend):
            result = Learning.gather()
        
        # Verify preset contexts are applied
        meta = Learning._chatfield_meta
        assert any("Learning something new" in ctx for ctx in meta.user_context)
        assert any("Patient teacher" in ctx for ctx in meta.agent_context)
        
        assert result.issue == 'My email is not working'
    
    @patch('builtins.input', return_value='Server is down, need immediate help')
    @patch('builtins.print')  
    def test_quick_diagnosis_preset(self, mock_print, mock_input):
        """Test quick_diagnosis preset."""
        @quick_diagnosis
        @gather
        class UrgentIssue:
            """Urgent technical issue"""
            def problem(): "What's the urgent problem?"
        
        with patch('chatfield.conversation.OpenAIBackend', MockLLMBackend):
            result = UrgentIssue.gather()
        
        # Verify preset contexts are applied
        meta = UrgentIssue._chatfield_meta
        assert any("urgent problem" in ctx for ctx in meta.user_context)
        assert any("Efficient troubleshooter" in ctx for ctx in meta.agent_context)
        
        assert result.problem == 'Server is down, need immediate help'
    
    @patch('builtins.input', return_value='Need advice on technology strategy')
    @patch('builtins.print')
    def test_friendly_expert_preset(self, mock_print, mock_input):
        """Test friendly_expert preset."""
        @friendly_expert
        @gather
        class Consultation:
            """Expert consultation"""
            def topic(): "What do you need advice on?"
        
        with patch('chatfield.conversation.OpenAIBackend', MockLLMBackend):
            result = Consultation.gather()
        
        # Verify preset contexts are applied
        meta = Consultation._chatfield_meta
        assert any("expert advice" in ctx for ctx in meta.user_context)
        assert any("Knowledgeable expert" in ctx for ctx in meta.agent_context)
        
        assert result.topic == 'Need advice on technology strategy'


class TestBuilderIntegration:
    """Test dynamic gatherer builder integration."""
    
    @patch('builtins.input', side_effect=['John Doe', 'Software issue'])
    @patch('builtins.print')
    def test_gatherer_builder(self, mock_print, mock_input):
        """Test creating gatherer with builder."""
        builder = GathererBuilder("CustomGatherer")
        builder.set_docstring("Custom support request")
        builder.add_user_context("Needs help with software")
        builder.add_agent_context("Technical support specialist")
        builder.add_field("name", "Your name")
        builder.add_field("issue", "Describe the issue", 
                         must_rules=["specific problem"],
                         hint="Be as specific as possible")
        
        GathererClass = builder.build()
        
        # Mock validation to pass
        mock_llm = MockLLMBackend()
        mock_llm.add_validation_response("VALID")  # For name (no rules)
        mock_llm.add_validation_response("VALID")  # For issue (has rules)
        
        with patch('chatfield.conversation.OpenAIBackend', return_value=mock_llm):
            result = GathererClass.gather()
        
        assert result.name == 'John Doe'
        assert result.issue == 'Software issue'
    
    @patch('builtins.input', side_effect=['Bakery', 'Need website for customers'])
    @patch('builtins.print')
    def test_create_from_dict(self, mock_print, mock_input):
        """Test creating gatherer from dictionary."""
        config = {
            'name': 'BusinessGatherer',
            'docstring': 'Business consultation',
            'user_contexts': ['Small business owner'],
            'agent_contexts': ['Business consultant'],
            'fields': {
                'business_type': 'What type of business do you have?',
                'need': {
                    'description': 'What do you need help with?',
                    'must_rules': ['specific need'],
                    'hint': 'Be specific about what you want to achieve'
                }
            }
        }
        
        GathererClass = create_gatherer_from_dict(config)
        
        mock_llm = MockLLMBackend()
        mock_llm.add_validation_response("VALID")  # business_type
        mock_llm.add_validation_response("VALID")  # need
        
        with patch('chatfield.conversation.OpenAIBackend', return_value=mock_llm):
            result = GathererClass.gather()
        
        assert result.business_type == 'Bakery'
        assert result.need == 'Need website for customers'
    
    @patch('builtins.input', side_effect=['Computer won\'t start', '2 days ago', 'Nothing yet'])
    @patch('builtins.print')
    def test_create_from_template(self, mock_print, mock_input):
        """Test creating gatherer from template."""
        GathererClass = create_gatherer_from_template('tech_support')
        
        mock_llm = MockLLMBackend()
        # Add validation responses for fields with rules
        mock_llm.add_validation_response("VALID")  # problem
        mock_llm.add_validation_response("VALID")  # when_started
        mock_llm.add_validation_response("VALID")  # what_tried
        mock_llm.add_validation_response("VALID")  # system_info
        
        with patch('chatfield.conversation.OpenAIBackend', return_value=mock_llm):
            result = GathererClass.gather()
        
        assert hasattr(result, 'problem')
        assert result.problem == 'Computer won\'t start'


class TestErrorHandling:
    """Test error handling in integration scenarios."""
    
    def test_missing_openai_key(self):
        """Test handling of missing OpenAI API key."""
        @gather
        class RequiresAPI:
            def field(): "Test field"
        
        # Mock OpenAI to raise ValueError for missing key
        with patch('chatfield.llm_backend.OpenAI') as mock_openai:
            mock_openai.side_effect = ValueError("OpenAI API key not found")
            
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                RequiresAPI.gather()
    
    @patch('builtins.input', return_value='test input')
    @patch('builtins.print')
    def test_llm_api_error(self, mock_print, mock_input):
        """Test handling of LLM API errors."""
        @gather
        class WithAPIError:
            def field(): "Test field"
        
        # Mock LLM to raise API error
        mock_llm = Mock()
        mock_llm.validate_response.side_effect = Exception("API Error")
        
        with patch('chatfield.conversation.OpenAIBackend', return_value=mock_llm):
            # Should handle gracefully and continue
            result = WithAPIError.gather()
            assert result.field == 'test input'


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    @patch('builtins.input', side_effect=[
        'John Doe',
        'We need a website for our bakery',
        '$5000',
        'In the next 3 months'
    ])
    @patch('builtins.print')
    def test_website_consultation(self, mock_print, mock_input):
        """Test a realistic website consultation scenario."""
        @friendly_expert
        @user("Small business owner wanting a website")
        @agent("Web development consultant")
        @gather
        class WebsiteConsultation:
            """Website planning consultation
            
            We'll gather requirements for your business website to ensure
            we build something that actually helps your business grow.
            """
            def contact_name(): "Your name"
            def business_description(): "Tell me about your business"
            def budget(): "What's your budget for this project?"
            def timeline(): "When do you need this completed?"
        
        mock_llm = MockLLMBackend()
        # Add validation responses
        for _ in range(4):  # 4 fields
            mock_llm.add_validation_response("VALID")
        
        with patch('chatfield.conversation.OpenAIBackend', return_value=mock_llm):
            result = WebsiteConsultation.gather()
        
        # Verify all data collected
        assert result.contact_name == 'John Doe'
        assert result.business_description == 'We need a website for our bakery'
        assert result.budget == '$5000'
        assert result.timeline == 'In the next 3 months'
        
        # Verify metadata structure
        meta = WebsiteConsultation._chatfield_meta
        assert "Website planning consultation" in meta.docstring
        assert len(meta.user_context) > 0  # From preset + manual
        assert len(meta.agent_context) > 0  # From preset + manual
        assert len(meta.fields) == 4