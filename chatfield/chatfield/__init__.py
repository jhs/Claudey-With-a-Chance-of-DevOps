"""Chatfield: Socratic dialogue for data gathering powered by LLMs.

Transform rigid forms into thoughtful Socratic conversations that guide users to express their needs clearly.
"""

__version__ = "0.2.0"

from .builder import chatfield

from .interview import Interview
from .interviewer import Interviewer

from .decorators import alice, bob
from .decorators import must, reject, hint
from .decorators import (
    as_int,
    as_obj,
    as_set,
    as_str,
    as_bool,
    as_dict,
    as_lang,
    as_list,
    as_float,
    as_percent,

    as_any,
    as_one,
    as_maybe,
    as_multi,
)

# __all__ = [
#     # TODO
# ]