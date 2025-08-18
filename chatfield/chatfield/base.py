"""Base class for Chatfield gatherers."""

# import json
# import textwrap
from typing import Type, TypeVar, List, Dict, Any, Callable

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
        print(f'  - kwargs: {bool(kwargs)}')

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
            field = self._get_chat_field(field_name)
            fields[field_name] = field
        
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
    
    def _get_chat_field(self, field_name: str):
        """Get the chatfield metadata for a field in this interview."""
        if field_name.startswith('_'):
            raise ValueError(f'{self._name()}: Field name must not start with an underscore: {field_name!r}')

        try:
            attr = object.__getattribute__(self, field_name)
        except AttributeError:
            raise ValueError(f'{self._name()}: Field not defined: {field_name!r}')

        if not callable(attr):
            raise ValueError(f'{self._name()}: Not a field (not callable): {field_name!r}')
        
        method = attr
        if not hasattr(method, '_chatfield'):
            attr._chatfield = {}

            # TODO: Maybe it is sloppy to modify the state of method._chatfield
            if method.__doc__:
                attr._chatfield['desc'] = method.__doc__
            else:
                attr._chatfield['desc'] = method.__name__
        
        return attr._chatfield

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
                    chatfield = getattr(val, '_chatfield', {})
                    value = chatfield.get('value', None)
                    if not value:
                        # print(f'Field {name!r} is not yet valid; return None')
                        return None
                    
                    # print(f'Field {name!r} is valid: {value!r}')
                    primary_value = value['value']
                    proxy = FieldProxy(primary_value, chatfield)
                    return proxy
        return val
    
    def _pretty(self) -> str:
        """Return a pretty representation of this interview."""
        lines = [f'{self._name()}']

        for field_name in self._fields():
            field = getattr(self, field_name)
            chatfield = self._get_chat_field(field_name)
            # desc = chatfield.get('desc', None)

            if field is None:
                lines.append(f'  {field_name}: None')
                continue
        
            # field is a proxy
            lines.append(f'  {field_name}: {chatfield["value"]["value"]!r}')
            lines.append(field._pretty())
        
        return '\n'.join(lines)
    
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

class FieldProxy(str):
    """Proxy object that provides match attribute access to field values.
    
    This proxy allows field values to:
    1. Behave as a normal string with all string methods
    2. Access match rule evaluations via attributes (e.g., field.is_personal)
    3. Access type transformations via as_* attributes (e.g., field.as_int)
    
    Example:
        field = FieldValueProxy("100 dollars", chatfield)
        field == "100 dollars"  # Direct string comparison
        field.upper() == "100 DOLLARS"  # String methods work
        field.is_large == True  # Match evaluation
        field.as_int == 100  # Type transformation
    """
    
    def __new__(cls, value: str, chatfield: Dict[str, Any]):
        """Create a new string-based proxy instance.
        
        Args:
            value: The actual string value of the field
            chatfield: Metadata about the field including match rules
        """
        # Create the string instance with the value
        instance = str.__new__(cls, value)
        return instance
    
    def __init__(self, value: str, chatfield: Dict[str, Any]):
        """Initialize the field value proxy metadata.
        
        Note: The string value is already set in __new__, this just stores metadata.
        
        Args:
            value: The actual string value of the field (for compatibility)
            chatfield: Metadata about the field including match rules
        """

        # Don't call str.__init__ as it doesn't take arguments
        # Store metadata for the proxy functionality
        self._chatfield = chatfield
    
    def _pretty(self) -> str:
        """Return a representation of the proxy."""
        # Use self directly since we're now a string
        # limit = 100
        # value_preview = self[:limit] + '...' if len(self) > limit else self
        # lines = [value_preview]
        lines = []
        for key, val in self._chatfield['value'].items():
            if key != 'value':
                lines.append(f'    {key:<25}: {val!r}')
        return '\n'.join(lines)
    
    def __getattr__(self, attr_name: str):
        """Provide access to match rule evaluations and type transformations.
        
        Args:
            attr_name: The name of the match rule (e.g., 'is_personal') or 
                transformation (e.g., 'as_int')
            
        Returns:
            The evaluation/transformation result, or None if not evaluated
            
        Raises:
            AttributeError: If the attribute doesn't exist
        """
        # print(f'FieldProxy: __getattr__ {attr_name!r} for {self._chatfield!r}')
        llm_value = self._chatfield.get('value')
        if not llm_value or not isinstance(llm_value, dict):
            raise AttributeError(f"Field {attr_name} has no value set. Cannot access attributes.")

        if attr_name in llm_value:
            # If the attribute is a match rule, return its evaluation
            cast_value = llm_value[attr_name]
            return cast_value