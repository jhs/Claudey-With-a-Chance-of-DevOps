"""Tests for complete conversation flows with prefab user messages using real OpenAI API."""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root .env file
project_root = Path(__file__).parent.parent.parent
env_file = project_root / '.env'
load_dotenv(env_file)

from chatfield import Interview, Interviewer, chatfield
from chatfield import alice, bob, must, hint, reject
from chatfield import as_int, as_bool, as_percent, as_one, as_maybe


@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="Requires OPENAI_API_KEY for live API tests"
)
class TestRestaurantOrderConversation:
    """Test restaurant order conversation flow with real API."""
    
    def create_restaurant_order(self):
        """Create restaurant order interview."""
        return (chatfield()
            .type("Restaurant Order")
            .desc("Taking your order for tonight")
            
            .alice()
                .type("Server")
                .trait("Friendly and attentive")
            
            .bob()
                .type("Diner")
                .trait("First-time visitor")
                .trait.possible("Vegan", "needs vegan, plant-based, non animal product")
            
            .field("starter")
                .desc("starter or appetizer")
                .as_one.selection("Sir Digby Chicken Caesar", "Shrimp cocktail", "Garden salad")
            
            .field("main_course")
                .desc("Main course")
                .hint("Choose from: Grilled salmon, Veggie pasta, Beef tenderloin, Chicken parmesan")
                .as_one.selection("Grilled salmon", "Veggie pasta", "Beef tenderloin", "Chicken parmesan")
            
            .field("dessert")
                .desc("Mandatory dessert; choices: Cheesecake, Chocolate mousse, Fruit sorbet")
                .as_one.selection("Cheesecake", "Chocolate mousse", "Fruit sorbet")
            
            .build())
    
    def test_vegan_adaptation_flow(self):
        """Test that vegan mention adapts the conversation and collects proper data."""
        order = self.create_restaurant_order()
        interviewer = Interviewer(order, thread_id="test-vegan-order")
        
        # Prefab inputs for vegan customer
        prefab_inputs = [
            'I am vegan, so I need plant-based options only.',
            'Garden salad please',
            'Veggie pasta sounds perfect',
            'Fruit sorbet would be great'
        ]
        
        # Initial AI message
        ai_message = interviewer.go(None)
        assert ai_message is not None
        
        # Process each input
        for user_input in prefab_inputs:
            if order._done:
                break
            ai_message = interviewer.go(user_input)
        
        # Verify the order was completed correctly
        assert order._done, "Order should be complete"
        assert order.starter == "Garden salad", f"Expected 'Garden salad', got {order.starter}"
        assert order.main_course == "Veggie pasta", f"Expected 'Veggie pasta', got {order.main_course}"
        assert order.dessert == "Fruit sorbet", f"Expected 'Fruit sorbet', got {order.dessert}"
        
        # Check that vegan trait was activated
        traits = order._chatfield['roles']['bob'].get('possible_traits', {})
        assert 'Vegan' in traits, "Vegan trait should be tracked"
        assert traits.get('Vegan', {}).get('active') == True, "Vegan trait should be active"
    
    def test_regular_order_flow(self):
        """Test regular order without dietary restrictions."""
        order = self.create_restaurant_order()
        interviewer = Interviewer(order, thread_id="test-regular-order")
        
        prefab_inputs = [
            'The Caesar salad sounds good',
            'I\'ll have the grilled salmon',
            'Chocolate mousse for dessert'
        ]
        
        # Initial message
        ai_message = interviewer.go(None)
        assert ai_message is not None
        
        # Process inputs
        for user_input in prefab_inputs:
            if order._done:
                break
            ai_message = interviewer.go(user_input)
        
        # Verify completion
        assert order._done, "Order should be complete"
        assert order.starter in ["Sir Digby Chicken Caesar", "Garden salad"], f"Starter should be valid, got {order.starter}"
        assert order.main_course == "Grilled salmon", f"Expected 'Grilled salmon', got {order.main_course}"
        assert order.dessert == "Chocolate mousse", f"Expected 'Chocolate mousse', got {order.dessert}"


@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="Requires OPENAI_API_KEY for live API tests"
)
class TestJobInterviewConversation:
    """Test job interview conversation flow with real API."""
    
    def create_job_interview(self):
        """Create job interview."""
        return (chatfield()
            .type("JobInterview")
            .desc("Software Engineer position interview")
            
            .alice()
                .type("Hiring Manager")
            
            .bob()
                .type("Candidate")
                .trait.possible("career-changer", "mentions different industry or transferable skills")
            
            .field("experience")
                .desc("Tell me about your relevant experience")
                .must("specific examples")
            
            .field("has_mentored")
                .desc("Gives specific evidence of professionally mentoring junior colleagues")
                .confidential()
                .as_bool()
            
            .build())
    
    def test_career_changer_detection(self):
        """Test that career change is detected from conversation."""
        interview = self.create_job_interview()
        interviewer = Interviewer(interview, thread_id="test-career-change")
        
        prefab_inputs = [
            "I spent 5 years in finance but taught myself programming. "
            "I built a trading algorithm in Python that automated our daily reports, "
            "saving the team 20 hours per week. I also created a dashboard using React.",
            
            "In my finance role, I regularly mentored junior analysts on Python programming "
            "and helped them understand data structures and algorithms."
        ]
        
        # Start conversation
        ai_message = interviewer.go(None)
        assert ai_message is not None
        
        # Process inputs
        for user_input in prefab_inputs:
            if interview._done:
                break
            ai_message = interviewer.go(user_input)
        
        # Verify data collection
        assert interview.experience is not None, "Experience should be collected"
        assert "finance" in interview.experience.lower(), "Should capture finance background"
        assert "python" in interview.experience.lower(), "Should capture Python experience"
        
        # Check confidential field
        assert interview.has_mentored is not None, "Mentoring should be detected"
        assert interview.has_mentored.as_bool == True, "Should detect mentoring activity"
        
        # Check career-changer trait
        traits = interview._chatfield['roles']['bob'].get('possible_traits', {})
        if 'career-changer' in traits:
            assert traits['career-changer'].get('active') == True, "Career changer trait should be active"
    
    def test_technical_interview_flow(self):
        """Test standard technical interview."""
        interview = self.create_job_interview()
        interviewer = Interviewer(interview, thread_id="test-technical")
        
        prefab_inputs = [
            "I have 8 years of experience as a full-stack developer. "
            "Most recently, I led the redesign of our e-commerce platform, "
            "improving load times by 40% and increasing conversion rates.",
            
            "I've been a tech lead for 3 years, mentoring a team of 5 developers "
            "through code reviews, pair programming, and weekly learning sessions."
        ]
        
        # Start conversation
        ai_message = interviewer.go(None)
        assert ai_message is not None
        
        # Process inputs
        for user_input in prefab_inputs:
            if interview._done:
                break
            ai_message = interviewer.go(user_input)
        
        # Verify experience was captured
        assert interview.experience is not None, "Experience should be collected"
        assert "e-commerce" in interview.experience or "platform" in interview.experience, "Should capture project details"
        
        # Check mentoring detection
        assert interview.has_mentored is not None, "Mentoring should be detected"
        assert interview.has_mentored.as_bool == True, "Should detect mentoring activity"


@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="Requires OPENAI_API_KEY for live API tests"
)
class TestNumberConversation:
    """Test number conversation with transformations using real API."""
    
    def create_number_interview(self):
        """Create number interview with transformations."""
        return (chatfield()
            .type("FavoriteNumber")
            .desc("Let's talk about your favorite number")
            
            .alice()
                .type("Mathematician")
            
            .bob()
                .type("Number Enthusiast")
            
            .field("number")
                .desc("Your favorite number between 1 and 100")
                .must("a number between 1 and 100")
                .as_int()
                .as_bool.even("True if even, False if odd")
                .as_one.parity("even", "odd")
            
            .build())
    
    def test_number_collection_with_transformations(self):
        """Test that number is collected with proper transformations."""
        interview = self.create_number_interview()
        interviewer = Interviewer(interview, thread_id="test-number")
        
        prefab_inputs = ["My favorite number is 42"]
        
        # Start conversation
        ai_message = interviewer.go(None)
        assert ai_message is not None
        
        # Process input
        for user_input in prefab_inputs:
            if interview._done:
                break
            ai_message = interviewer.go(user_input)
        
        # Verify number was collected with transformations
        assert interview._done, "Interview should be complete"
        assert interview.number == "42", f"Expected '42', got {interview.number}"
        assert interview.number.as_int == 42, f"Integer transformation should be 42, got {interview.number.as_int}"
        assert interview.number.as_bool_even == True, "42 should be detected as even"
        assert interview.number.as_one_parity == "even", "Parity should be 'even'"
    
    def test_odd_number_transformations(self):
        """Test odd number with transformations."""
        interview = self.create_number_interview()
        interviewer = Interviewer(interview, thread_id="test-odd-number")
        
        prefab_inputs = ["I like the number 17"]
        
        # Start conversation
        ai_message = interviewer.go(None)
        assert ai_message is not None
        
        # Process input
        for user_input in prefab_inputs:
            if interview._done:
                break
            ai_message = interviewer.go(user_input)
        
        # Verify odd number transformations
        assert interview._done, "Interview should be complete"
        assert interview.number == "17", f"Expected '17', got {interview.number}"
        assert interview.number.as_int == 17, f"Integer transformation should be 17, got {interview.number.as_int}"
        assert interview.number.as_bool_even == False, "17 should be detected as odd"
        assert interview.number.as_one_parity == "odd", "Parity should be 'odd'"


@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="Requires OPENAI_API_KEY for live API tests"
)
class TestSimpleConversations:
    """Test simple conversation patterns with real API."""
    
    def test_name_email_collection(self):
        """Test simple name and email collection."""
        interview = (chatfield()
            .type("ContactInfo")
            .desc("Collecting contact information")
            
            .field("name")
                .desc("Your full name")
            
            .field("email")
                .desc("Your email address")
                .must("valid email format")
            
            .build())
        
        interviewer = Interviewer(interview, thread_id="test-contact")
        
        prefab_inputs = ["John Doe", "john.doe@example.com"]
        
        # Initial message
        ai_message = interviewer.go(None)
        assert ai_message is not None
        
        # Process inputs
        for user_input in prefab_inputs:
            if interview._done:
                break
            ai_message = interviewer.go(user_input)
        
        # Verify completion
        assert interview._done, "Interview should be complete"
        assert interview.name == "John Doe", f"Expected 'John Doe', got {interview.name}"
        assert interview.email == "john.doe@example.com", f"Expected 'john.doe@example.com', got {interview.email}"
    
    def test_boolean_field_collection(self):
        """Test boolean field collection."""
        interview = (chatfield()
            .type("Preferences")
            .desc("Learning about your preferences")
            
            .field("likes_coffee")
                .desc("Do you like coffee?")
                .as_bool()
            
            .build())
        
        interviewer = Interviewer(interview, thread_id="test-bool")
        
        prefab_inputs = ["Yes, I love coffee!"]
        
        # Start conversation
        ai_message = interviewer.go(None)
        assert ai_message is not None
        
        # Process input
        for user_input in prefab_inputs:
            if interview._done:
                break
            ai_message = interviewer.go(user_input)
        
        # Verify boolean was collected
        assert interview._done, "Interview should be complete"
        assert interview.likes_coffee.as_bool == True, "Should detect positive response"