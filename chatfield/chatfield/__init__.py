"""Chatfield: Socratic dialogue for data gathering powered by LLMs.

Transform rigid forms into thoughtful Socratic conversations that guide users to express their needs clearly.
"""

__version__ = "0.2.0"

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