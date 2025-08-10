"""Base class for Chatfield gatherers."""

from typing import Type, TypeVar, Dict, Optional
from .socrates import process_socrates_class, SocratesInstance, SocratesMeta
from .conversation import Conversation

T = TypeVar('T', bound='Gatherer')

# Global cache for metadata by class
_metadata_cache: Dict[type, SocratesMeta] = {}


class Gatherer:
    """Base class for creating Socratic dialogue interfaces.
    
    Inherit from this class to create a data gatherer that conducts
    conversations to collect information from users.
    
    Example:
        class TechHelp(Gatherer):
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
        meta = cls._get_meta()
        conversation = Conversation(meta, **kwargs)
        collected_data = conversation.conduct_conversation()
        # Use create_instance to properly include match evaluations
        return conversation.create_instance()
    
    # Property to expose metadata for advanced usage
    @classmethod
    @property
    def _chatfield_meta(cls) -> SocratesMeta:
        """Access to the processed metadata."""
        return cls._get_meta()