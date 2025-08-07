"""Chatfield: Conversational data gathering powered by LLMs.

Transform rigid forms into natural conversations that help users express their needs.
"""

__version__ = "0.1.0"

from .decorators import gather, must, reject, hint, user, agent
from .presets import patient_teacher, quick_diagnosis, friendly_expert

__all__ = [
    "gather",
    "must", 
    "reject",
    "hint",
    "user",
    "agent",
    "patient_teacher",
    "quick_diagnosis", 
    "friendly_expert",
]