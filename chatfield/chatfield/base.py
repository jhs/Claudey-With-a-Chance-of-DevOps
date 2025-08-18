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

    # At this time, .model_dump() is needed by langgraph's checkpointer serializer.
    # Just explicitly track it. For now it's not defined what happens if the caller
    # defines a field that collides with these names.
    # - Jason Sun Aug 17 03:19:08 PM CDT 2025
    not_field_names = {'model_dump'}

    def __init__(self, **kwargs): # TODO: Bring back *args if any serialization or tracing errors happen.
        print(f'Initializing Interview: {self.__class__.__name__}')
        if not kwargs:
            print(f'  - no kwargs')
        else:
            print(f'  - kwargs: {kwargs!r}')

        # pass
        # super().__init__(*args, **kwargs)
        super().__init__()
    
    @classmethod
    def _init_field(cls, func: Callable):
        if not hasattr(func, '_chatfield'):
            func._chatfield = {
                'desc': func.__doc__ or func.__name__,
                'specs': {},
                'casts': {},
            }
    
    # This must take kwargs to support langsmith calling it.
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        # print(f'model_dump: kwargs={kwargs!r}')
        type_name = self.__class__.__name__
        roles = getattr(self, '_roles', None)

        # desc = textwrap.dedent(self.__doc__).strip() if self.__doc__ else None
        desc = self.__doc__ if self.__doc__ else None

        fields = {}
        for field_name in self._fields():
            method = object.__getattribute__(self, field_name)
            # TODO: Maybe it is sloppy to modify the state of method._chatfield
            chatfield = getattr(method, '_chatfield', {})
            if method.__doc__:
                chatfield['desc'] = method.__doc__
            else:
                chatfield['desc'] = method.__name__
            fields[field_name] = chatfield
        
        return dict(type=type_name, desc=desc, roles=roles, fields=fields)
    
    def _name(self) -> str:
        """Return a human-readable label representing this interview data type"""
        return self.__class__.__name__
    
    def _alice_role(self):
        return self._get_role('alice')
    
    def _bob_role(self):
        return self._get_role('bob')

    def _alice_role_name(self) -> str:
        return self._get_role_name(f'alice', f'Agent')
    
    def _bob_role_name(self) -> str:
        return self._get_role_name(f'bob', f'User')
    
    def _get_role_name(self, role_name: str, default: str) -> str:
        role = self._get_role(role_name)
        role_type = role.get('type', default)
        return role_type
    
    def _get_role(self, role_name: str):
        roles = getattr(self, '_roles', {})
        role = roles.get(role_name, {})
        return role

    def _fields(self) -> List[str]:
        """Return a list of field names defined in this interview."""
        result = []

        for attr_name in dir(self):
            if not attr_name.startswith('_'):
                if attr_name not in self.not_field_names:
                    attr = object.__getattribute__(self, attr_name)
                    if callable(attr):
                        result.append(attr_name) # All methods are fields.
        return result

    def __getattribute__(self, name: str):
        """Get field values or other attributes.
        
        For defined fields, returns either None or a FieldValueProxy.
        Overrides the method access to return field values instead.
        """
        # __class = object.__getattribute__(self, '__class__')
        # __name = __class.__name__

        val = object.__getattribute__(self, name)
        if not name.startswith('_'):
            if callable(val):
                if name not in self.not_field_names:
                    raise NotImplementedError(f'Need to return None or a proxy')
                    return None
        return val
    
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