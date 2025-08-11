"""Base class for Chatfield gatherers."""

# import json
# import textwrap
from typing import Type, TypeVar, List, Dict, Any
# from .socrates import process_socrates_class, SocratesInstance, SocratesMeta

T = TypeVar('T', bound='Interview')

class Interview:
    """Base class for creating Socratic dialogue interfaces.
    
    Inherit from this class to create a dialogue that conducts
    conversations to collect information from users.
    
    Example:
        class TechHelp(Interview):
            def problem(): "What's not working?"
            def tried(): "What have you tried?"
    """

    # This will be built by any @alice or @bob decorators.
    # _roles: Dict[str, Dict[str, Any]] = {
    #     'alice': {'role': None, 'traits': []},
    #     'bob'  : {'role': None, 'traits': []},
    # }

    def __init__(self):
        pass
    
    def _asdict(self) -> Dict[str, Any]:
        type_name = self.__class__.__name__
        roles = getattr(self, '_roles', None)

        # desc = textwrap.dedent(self.__doc__).strip() if self.__doc__ else None
        desc = self.__doc__ if self.__doc__ else None

        fields = {}
        for field_name in self._fields():
            field = object.__getattribute__(self, field_name)
            chatfield = getattr(field, '_chatfield', {})
            if field.__doc__:
                chatfield['desc'] = field.__doc__
            fields[field_name] = chatfield
        
        return dict(type=type_name, desc=desc, roles=roles, fields=fields)
    
    def _fields(self) -> List[str]:
        """Return a list of field names defined in this interview."""
        result = []
        for attr_name in dir(self):
            if not attr_name.startswith('_'):
                attr = object.__getattribute__(self, attr_name)
                if callable(attr):
                    result.append(attr_name)
        return result
    
    # @classmethod
    # def _get_meta(cls) -> SocratesMeta:
    #     """Get metadata, creating it if needed."""
    #     # Use the class itself as the cache key to handle inheritance properly
    #     if cls not in _metadata_cache:
    #         _metadata_cache[cls] = process_socrates_class(cls)
    #     return _metadata_cache[cls]
    
    # @classmethod
    # def gather(cls: Type[T], **kwargs) -> SocratesInstance:
    #     """Conduct a Socratic dialogue to gather data.
        
    #     Args:
    #         **kwargs: Additional arguments passed to the conversation handler.
            
    #     Returns:
    #         SocratesInstance with collected data accessible as attributes.
    #     """
    #     raise NotImplementedError(
    #         "The execution model for Interview.gather() has not been implemented yet. "
    #         "The conversation system is being redesigned. "
    #         "For now, use ChatfieldAgent directly if you need the underlying functionality."
    #     )
    
    # Property to expose metadata for advanced usage
    # @classmethod
    # @property
    # def _chatfield_meta(cls) -> SocratesMeta:
    #     """Access to the processed metadata."""
    #     return cls._get_meta()
    
    def __getattribute__(self, name: str):
        """Get field values or other attributes.
        
        For defined fields, returns either None or a FieldValueProxy.
        Overrides the method access to return field values instead.
        """
        # First check if we have _meta initialized (during __init__)
        # print(f'__getattribute__: {name!r}')
        val = object.__getattribute__(self, name)
        if callable(val) and not name.startswith('_'):
            return None
        return val

        # return object.__getattribute__(self, name)
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
        raise Exception(f'XXX')
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
        raise Exception(f'XXX')
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
        as_dict = self._asdict()
        return repr(as_dict)