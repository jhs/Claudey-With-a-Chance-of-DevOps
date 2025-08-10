"""Base class for Chatfield gatherers."""

from typing import Type, TypeVar, Dict, Any
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
    
    def __init__(self):
        """Initialize the dialogue with all fields set to None."""
        # Get metadata for this class
        meta = self._get_meta()
        
        # Store metadata reference for instance use (must be before field init)
        # Use object.__setattr__ to bypass our custom __setattr__
        object.__setattr__(self, '_meta', meta)
        object.__setattr__(self, '_collected_data', {})
        object.__setattr__(self, '_match_evaluations', {})
        object.__setattr__(self, '_transformations', {})
        object.__setattr__(self, '_field_values', {})
        
        # Initialize all fields to None
        for field_name in meta.fields:
            self._field_values[field_name] = None
    
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
    
    def __getattribute__(self, name: str):
        """Get field values or other attributes.
        
        For defined fields, returns either None or a FieldValueProxy.
        Overrides the method access to return field values instead.
        """
        # First check if we have _meta initialized (during __init__)
        try:
            meta = object.__getattribute__(self, '_meta')
            field_values = object.__getattribute__(self, '_field_values')
        except AttributeError:
            # Not initialized yet, use default behavior
            return object.__getattribute__(self, name)
        
        # Check if this is a known field
        if name in meta.fields:
            return field_values.get(name)
        
        # Not a field, use normal attribute access
        return object.__getattribute__(self, name)
    
    def __setattr__(self, name: str, value):
        """Set attributes with field protection.
        
        Fields defined in the dialogue are read-only and cannot be set directly.
        """
        # Allow setting of private attributes
        if name.startswith('_'):
            object.__setattr__(self, name, value)
            return
        
        # Check if this is a field - if so, it's read-only
        if hasattr(self, '_meta') and name in self._meta.fields:
            raise AttributeError(
                f"Cannot set field '{name}' directly - fields are read-only. "
                f"Fields should only be populated through the dialogue process."
            )
        
        # Allow setting other attributes normally
        object.__setattr__(self, name, value)
    
    def _set_field_value(self, field_name: str, value, evaluations=None, transformations=None):
        """Internal method to set field values with FieldValueProxy.
        
        This is used internally by the dialogue system to populate fields.
        """
        if field_name not in self._meta.fields:
            raise ValueError(f"Unknown field: {field_name}")
        
        if value is None:
            self._field_values[field_name] = None
        else:
            # Import here to avoid circular dependency
            from .field_proxy import FieldValueProxy
            
            field_meta = self._meta.get_field(field_name)
            field_evaluations = evaluations or {}
            field_transformations = transformations or {}
            
            proxy = FieldValueProxy(
                value,
                field_meta,
                field_evaluations,
                field_transformations
            )
            self._field_values[field_name] = proxy
            
            # Also update internal tracking
            self._collected_data[field_name] = value
            if evaluations:
                self._match_evaluations[field_name] = evaluations
            if transformations:
                self._transformations[field_name] = transformations
    
    @property
    def done(self):
        """Check if all required fields have been collected.
        
        Returns True when all fields have been populated with values.
        Fields are only populated when they pass validation, so checking
        for non-None values is sufficient.
        """
        if not hasattr(self, '_meta'):
            return False
        return all(
            self._field_values.get(field_name) is not None 
            for field_name in self._meta.fields
        )

    def __repr__(self):
        if hasattr(self, '_meta'):
            field_status = []
            for field_name in self._meta.fields:
                value = self._field_values.get(field_name)
                if value is None:
                    field_status.append(f"{field_name}=None")
                else:
                    field_status.append(f"{field_name}=<set>")
            fields_str = ", ".join(field_status)
            return f'<{self.__class__.__name__} {fields_str}>'
        return f'<{self.__class__.__name__}>'
    
    def to_msgpack_dict(self) -> Dict[str, Any]:
        """Convert this Dialogue instance to a msgpack-compatible dictionary.
        
        This captures both the class definition metadata and current field values
        with their evaluations and transformations.
        
        Returns:
            A dictionary containing only msgpack-serializable types
        """
        from .serialization import dialogue_to_msgpack_dict
        return dialogue_to_msgpack_dict(self)
    
    @classmethod
    def from_msgpack_dict(cls, data: Dict[str, Any]) -> 'Dialogue':
        """Reconstruct a Dialogue instance from a msgpack dictionary.
        
        Args:
            data: Dictionary created by to_msgpack_dict()
            
        Returns:
            A reconstructed Dialogue instance with all field values
        """
        from .serialization import msgpack_dict_to_dialogue
        return msgpack_dict_to_dialogue(data, dialogue_class=cls)