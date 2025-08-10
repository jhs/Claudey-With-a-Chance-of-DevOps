"""Base class for Chatfield gatherers."""

from typing import Type, TypeVar, Dict, Optional
from .socrates import process_socrates_class, SocratesInstance, SocratesMeta

T = TypeVar('T', bound='Dialogue')

# Global cache for metadata by class
_metadata_cache: Dict[type, SocratesMeta] = {}


class Dialogue:
    """Base class for creating Socratic dialogue interfaces.
    
    Inherit from this class to create a dialogue that conducts
    conversations to collect information from users.
    
    Example:
        class TechHelp(Dialogue):
            def problem(): "What's not working?"
            def tried(): "What have you tried?"
    """
    
    @classmethod
    def _get_meta(cls) -> SocratesMeta:
        """Get metadata, creating it if needed."""
        # Use the class itself as the cache key to handle inheritance properly
        if cls not in _metadata_cache:
            _metadata_cache[cls] = process_socrates_class(cls)
        return _metadata_cache[cls]
    
    @classmethod
    def gather(cls: Type[T], **kwargs) -> SocratesInstance:
        """Conduct a Socratic dialogue to gather data.
        
        Args:
            **kwargs: Additional arguments passed to the conversation handler.
            
        Returns:
            SocratesInstance with collected data accessible as attributes.
        """
        raise NotImplementedError(
            "The execution model for Dialogue.gather() has not been implemented yet. "
            "The conversation system is being redesigned. "
            "For now, use ChatfieldAgent directly if you need the underlying functionality."
        )
    
    # Property to expose metadata for advanced usage
    @classmethod
    @property
    def _chatfield_meta(cls) -> SocratesMeta:
        """Access to the processed metadata."""
        return cls._get_meta()