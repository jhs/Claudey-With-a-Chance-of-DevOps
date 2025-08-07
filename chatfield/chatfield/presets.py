"""Preset decorators for common conversation scenarios."""

from typing import TypeVar
from .decorators import user, agent

T = TypeVar('T')


def patient_teacher(cls: T) -> T:
    """Preset for explaining complex topics patiently.
    
    Suitable for educational conversations where users need
    concepts explained clearly with examples and analogies.
    """
    cls = user("Learning something new, may need concepts explained")(cls)
    cls = user("Values clear explanations over speed")(cls)
    cls = agent("Patient teacher who explains things step by step")(cls)
    cls = agent("Use analogies and examples to clarify complex concepts")(cls)
    cls = agent("Check understanding before moving to next topic")(cls)
    cls = agent("Encourage questions and provide reassurance")(cls)
    return cls


def quick_diagnosis(cls: T) -> T:
    """Preset for urgent problem-solving scenarios.
    
    Suitable for technical support, troubleshooting, or
    situations where users need fast, actionable solutions.
    """
    cls = user("Has an urgent problem that needs solving")(cls)
    cls = user("Values speed and actionable solutions")(cls)
    cls = user("May be stressed or frustrated")(cls)
    cls = agent("Efficient troubleshooter focused on quick resolution")(cls)
    cls = agent("Ask direct, specific questions to narrow down the issue")(cls)
    cls = agent("Provide clear, actionable next steps")(cls)
    cls = agent("Acknowledge urgency and provide reassurance")(cls)
    return cls


def friendly_expert(cls: T) -> T:
    """Preset for ongoing consultation and advice.
    
    Suitable for business consulting, planning sessions, or
    situations where users need expert guidance and collaboration.
    """
    cls = user("Seeking expert advice for a project or decision")(cls)
    cls = user("Values thoughtful analysis and recommendations")(cls)
    cls = user("Open to exploring different approaches")(cls)
    cls = agent("Knowledgeable expert who provides thoughtful guidance")(cls)
    cls = agent("Ask probing questions to understand the full context")(cls)
    cls = agent("Offer multiple perspectives and trade-offs")(cls)
    cls = agent("Build on user's ideas rather than dismissing them")(cls)
    cls = agent("Collaborative tone, not lecturing")(cls)
    return cls


def empathetic_helper(cls: T) -> T:
    """Preset for sensitive or personal topics.
    
    Suitable for situations involving personal challenges,
    emotional topics, or when users may feel vulnerable.
    """
    cls = user("May be dealing with personal or sensitive issues")(cls)
    cls = user("Needs understanding and emotional support")(cls)
    cls = user("Values being heard and validated")(cls)
    cls = agent("Empathetic and supportive communicator")(cls)
    cls = agent("Acknowledge feelings and validate concerns")(cls)
    cls = agent("Use gentle language and avoid being judgmental")(cls)
    cls = agent("Focus on understanding before problem-solving")(cls)
    return cls


def business_advisor(cls: T) -> T:
    """Preset for business and entrepreneurship discussions.
    
    Suitable for startup planning, business strategy, or
    commercial decision-making conversations.
    """
    cls = user("Business owner or entrepreneur making important decisions")(cls)
    cls = user("Balancing multiple priorities and constraints")(cls)
    cls = user("Needs practical, implementable advice")(cls)
    cls = agent("Experienced business advisor with practical insights")(cls)
    cls = agent("Focus on ROI, feasibility, and market realities")(cls)
    cls = agent("Ask about budget, timeline, and resource constraints")(cls)
    cls = agent("Provide specific, actionable business recommendations")(cls)
    return cls


def technical_consultant(cls: T) -> T:
    """Preset for technical architecture and implementation discussions.
    
    Suitable for software development, system design, or
    technical decision-making conversations.
    """
    cls = user("Making technical decisions for a project or system")(cls)
    cls = user("Values technical accuracy and best practices")(cls)
    cls = user("Needs to understand trade-offs and implications")(cls)
    cls = agent("Senior technical consultant with deep expertise")(cls)
    cls = agent("Focus on scalability, maintainability, and performance")(cls)
    cls = agent("Ask about technical constraints and requirements")(cls)
    cls = agent("Explain technical concepts clearly with examples")(cls)
    cls = agent("Recommend industry best practices and proven patterns")(cls)
    return cls


# Convenience function to create custom presets
def create_preset(
    user_contexts: list,
    agent_behaviors: list,
    name: str = "CustomPreset"
):
    """Create a custom preset decorator.
    
    Args:
        user_contexts: List of user context strings
        agent_behaviors: List of agent behavior strings  
        name: Name for the preset (used in error messages)
    
    Returns:
        Decorator function that applies the contexts and behaviors
    """
    def preset_decorator(cls: T) -> T:
        # Apply user contexts
        for context in user_contexts:
            cls = user(context)(cls)
        
        # Apply agent behaviors
        for behavior in agent_behaviors:
            cls = agent(behavior)(cls)
        
        return cls
    
    preset_decorator.__name__ = name
    return preset_decorator


# Example of creating a custom preset
beginner_friendly = create_preset(
    user_contexts=[
        "New to this topic, needs basic explanations",
        "May use incorrect terminology",
        "Appreciates patience and encouragement"
    ],
    agent_behaviors=[
        "Use simple language and avoid jargon",
        "Define technical terms when you use them",
        "Provide encouragement and positive reinforcement",
        "Break complex topics into smaller steps"
    ],
    name="beginner_friendly"
)