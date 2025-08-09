"""Chatfield: Socratic dialogue for data gathering powered by LLMs.

Transform rigid forms into thoughtful Socratic conversations that guide users to express their needs clearly.
"""

__version__ = "0.2.0"

from .decorators import gather, must, reject, hint, user, agent
from .presets import patient_teacher, quick_diagnosis, friendly_expert
from .visualization import (
    get_agent_graph,
    get_graph_from_class,
    visualize_graph,
    get_graph_metadata,
    display_graph_in_notebook
)
from .socrates import SocratesMeta, FieldMeta, SocratesInstance, process_socrates_class
from .agent import ChatfieldAgent

__all__ = [
    # Core decorators
    "gather",
    "must", 
    "reject",
    "hint",
    "user",
    "agent",
    # Presets
    "patient_teacher",
    "quick_diagnosis", 
    "friendly_expert",
    # Visualization
    "get_agent_graph",
    "get_graph_from_class",
    "visualize_graph",
    "get_graph_metadata",
    "display_graph_in_notebook",
    # Core classes
    "SocratesMeta",
    "FieldMeta",
    "SocratesInstance",
    "process_socrates_class",
    "ChatfieldAgent",
]