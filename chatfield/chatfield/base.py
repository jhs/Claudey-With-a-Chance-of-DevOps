"""Base class for Chatfield gatherers."""

import json
# import textwrap
from typing import Type, TypeVar, List, Dict, Any

T = TypeVar('T', bound='Interview')

# class Interview(BaseModel):
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

    def __init__(self, *args, **kwargs):
        print(f'Initializing Interview: {self.__class__.__name__}')
        if not kwargs:
            print(f'  - no kwargs')
        else:
            print(f'  - kwargs: {kwargs!r}')

        # pass
        # super().__init__(*args, **kwargs)
        super().__init__()
    
    # This must take kwargs to support langsmith calling it.
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        print(f'Interview model_dump called: kwargs={kwargs!r}')
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
            else:
                chatfield['desc'] = field.__name__
            fields[field_name] = chatfield
        
        return dict(type=type_name, desc=desc, roles=roles, fields=fields)
    
    @classmethod
    def _fromdict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Reconstruct an Interview object from a dictionary.
        
        Args:
            data: Dictionary as returned by _asdict(), containing:
                - type: The class name
                - desc: The class docstring
                - roles: Role definitions (if any)
                - fields: Field definitions with their metadata
        Returns:
            A new instance of the Interview subclass with the given structure.
        
        Raises:
            ValueError: If the type name doesn't match the class name.
        """
        # Validate type matches
        if data.get('type') != cls.__name__:
            raise ValueError(f"Type mismatch: expected {cls.__name__}, got {data.get('type')}")
        
        # Create new instance - it already has all methods from class definition
        instance = cls()
        
        # Restore instance state if provided
        # if state:
        #     # Store field values in _state or wherever the instance keeps them
        #     if not hasattr(instance, '_state'):
        #         instance._state = {}
        #     instance._state.update(state)
        
        # Note: We don't need to recreate methods or set _roles since
        # those are already part of the class definition that cls() uses
        
        return instance
    
    def _fields(self) -> List[str]:
        """Return a list of field names defined in this interview."""
        return ['favorite_number']
        result = []
        for attr_name in dir(self):
            if not attr_name.startswith('_') and attr_name not in ('model_dump', 'dumps_typed', 'loads_typed'):
                attr = object.__getattribute__(self, attr_name)
                if callable(attr):
                    result.append(attr_name)
        return result
    
    # def dumps_typed(self, obj: Any) -> tuple[str, bytes]:
    #     print(f'XXX is this working?')
    #     return type(obj).__name__, self.serde.dumps(obj)

    # def loads_typed(self, data: tuple[str, bytes]) -> Any:
    #     print(f'XXX is this working?')
    #     return self.serde.loads(data[1])

    def __getattribute__(self, name: str):
        """Get field values or other attributes.
        
        For defined fields, returns either None or a FieldValueProxy.
        Overrides the method access to return field values instead.
        """
        # First check if we have _meta initialized (during __init__)
        __class = object.__getattribute__(self, '__class__')
        __name = __class.__name__
        # print(f'__getattribute__: {__name}.{name!r}')
        # print(f'__getattribute__: {name!r}')

        val = object.__getattribute__(self, name)
        if not name.startswith('_'):
            if callable(val):
                # print(f'Special field {__name}.{name!r} is callable, returning as is.')
                if name in ('model_dump', 'dumps_typed', 'loads_typed'):
                    # These methods are special and should not be treated as fields
                    # print(f'  > Returning method {__name}.{name!r} as is.')
                    return val
                else:
                    # print(f'  > Override None for callable {__name}.{name!r}.')
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
    def _done(self):
        """Check if all required fields have been collected.
        
        Returns True when all fields have been populated with values.
        Fields are only populated when they pass validation, so checking
        for non-None values is sufficient.
        """
        states = []
        for field_name in self._fields():
            field = getattr(self, field_name, None)
            states.append(field is not None)
            # field = object.__getattribute__(self, field_name)
            # chatfield = field and getattr(field, '_chatfield', None)
        return all(states)

    # def __repr__(self):
    #     as_dict = self._asdict()
    #     return repr(as_dict)
    
    # def __str__(self) -> str:
    #     return f'Interview: {self.__class__.__name__} - {self._done}'
    #     # as_dict = self._asdict()
    #     # return json.dumps(as_dict)