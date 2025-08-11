"""Chatfield: Socratic dialogue for data gathering powered by LLMs.

Transform rigid forms into thoughtful Socratic conversations that guide users to express their needs clearly.
"""

__version__ = "0.2.0"

from .base import Interview

from .decorators import alice, bob
from .decorators import must, reject, hint
from .decorators import (
    as_int,
    as_bool,
)

# from .match import match
# from .types import (
#     as_int, as_float, as_percent,
#     as_list, as_set, as_dict,
#     as_choice, as_choose_one, as_choose_many,
#     as_date, as_duration, as_timezone, as_lang,
#     get_field_transformations, build_transformation_prompt
# )
# from .presets import patient_teacher, quick_diagnosis, friendly_expert
# from .visualization import (
#     get_agent_graph,
#     get_graph_from_class,
#     visualize_graph,
#     get_graph_metadata,
#     display_graph_in_notebook
# )
# from .socrates import SocratesMeta, FieldMeta, SocratesInstance, process_socrates_class
from .interviewer import Interviewer

# __all__ = []
# __all__ = [
#     # Core base class
#     "Interview",
#     # Core decorators
#     "must", 
#     "reject",
#     "hint",
#     "user",
#     "agent",
#     "match",
#     # Type transformation decorators
#     "as_int",
#     "as_float", 
#     "as_percent",
#     "as_list",
#     "as_set",
#     "as_dict",
#     "as_choice",
#     "as_choose_one",
#     "as_choose_many",
#     "as_date",
#     "as_duration",
#     "as_timezone",
#     "as_lang",
#     "get_field_transformations",
#     "build_transformation_prompt",
#     # Presets
#     "patient_teacher",
#     "quick_diagnosis", 
#     "friendly_expert",
#     # Visualization
#     "get_agent_graph",
#     "get_graph_from_class",
#     "visualize_graph",
#     "get_graph_metadata",
#     "display_graph_in_notebook",
#     # Core classes
#     "SocratesMeta",
#     "FieldMeta",
#     "SocratesInstance",
#     "process_socrates_class",
#     "ChatfieldAgent",
#     "Interviewer",
# ]