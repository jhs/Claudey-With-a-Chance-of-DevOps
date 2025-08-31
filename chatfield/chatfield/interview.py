"""Base class for Chatfield gatherers."""

import re
# import json
# import textwrap
import copy
import traceback
from typing import Type, TypeVar, List, Dict, Any, Callable
from types import SimpleNamespace

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

    # _chatfield_roles = {
    #     'alice': {'type': None, 'traits': []},
    #     'bob'  : {'type': None, 'traits': []},
    # }

    def __init__(self, **kwargs):
        try:
            self.__inner_init__(**kwargs)
        except Exception as er:
            # The LangGraph deserializer will silently catch any Exception and then just return
            # the value of kwargs here. For now at least log out any errors that happen.
            # print(f'Error initializing {self.__class__.__name__}: {er}')
            print(f'-----------------------------------------')
            traceback.print_exc()
            print(f'-----------------------------------------')
            raise er

    def __inner_init__(self, type=None, desc=None, roles=None, fields=None, **kwargs):
        # print(f'{self.__class__.__name__}: Init')
        if kwargs:
            raise Exception(f'Unknown kwargs to {self.__class__.__name__}(): {kwargs}')

        # I hope this is no longer needed.
        # self.__class__._ensure_roles()
        
        if not desc:
            if self.__class__ is not Interview:
                desc = self.__doc__ or self.__class__.__name__

        roles = roles or {
            'alice': {
                'type': 'Agent',
                'traits': [],
                'possible_traits': {},
            },
            'bob': {
                'type': 'User',
                'traits': [],
                'possible_traits': {},
            },
        }

        chatfield_interview = {
            'type': type,
            'desc': desc,
            'roles': roles,
            'fields': fields or {},
        }

        # field_def = {
        #     'desc': attr.__doc__ or attr.__name__,
        #     'specs': attr._chatfield.get('specs', {}),
        #     'casts': attr._chatfield.get('casts', {}),
        #     'value': None,  # This will be set by the LLM.
        # }
        # chatfield_interview['fields'][attr_name] = field_def

        # fields = kwargs.get('fields', {})
        # for field_name, field_value in fields.items():
        #     value = field_value.get('value', None)
        #     if value is None:
        #         # print(f'{self.__class__.__name__} field not yet present: {field_name!r}')
        #         pass
        #     else:
        #         print(f'{self.__class__.__name__} value of field {field_name!r}: {value!r}')
        #         chatfield = chatfield_interview['fields'][field_name]
        #         if chatfield.get('value'):
        #             raise Exception(f'{self.__class__.__name__} field {field_name!r} already has a value: {chatfield["value"]!r}')
        #         else:
        #             print(f'- fine to set value for {field_name!r}')
        #         chatfield['value'] = value
        
        self._chatfield = copy.deepcopy(chatfield_interview)

    @classmethod
    def _init_field(cls, func: Callable):
        if not hasattr(func, '_chatfield'):
            func._chatfield = {
                'specs': {},
                'casts': {},
            }
    
    @classmethod
    def _ensure_roles(cls):
        raise Exception(f'This might be a bug because everything is re-using the Interview class again')
        if not hasattr(cls, '_chatfield_roles'):
            cls._chatfield_roles = {}

        if 'alice' not in cls._chatfield_roles:
            cls._chatfield_roles['alice'] = {
                'type': None,
                'traits': [],
            }
        
        if 'bob' not in cls._chatfield_roles:
            cls._chatfield_roles['bob'] = {
                'type': None,
                'traits': [],
            }

    # This must take kwargs to support langsmith calling it.
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        # print(f'model_dump: kwargs={kwargs!r}')
        result = copy.deepcopy(self._chatfield)
        return result
    
    def _copy_from(self, source):
        """
        Copy from an interview into this object
        """

        # The current implementation is very minimal.
        self._chatfield = copy.deepcopy(source._chatfield)
    
    def _name(self) -> str:
        """Return a human-readable label representing this interview data type"""
        return self._chatfield['type']
    
    def _id(self) -> str:
        """Return this interview data type as a valid identifier (lowercase, underscores)"""
        name = self._name()
        # name = name.lower()
        name = re.sub(r'\s+', '_', name)          # Replace whitespace with underscores
        name = re.sub(r'[^a-zA-Z0-9_]', '', name) # Remove non-alphanumeric/underscore characters
        name = re.sub(r'_+', '_', name)           # Collapse multiple underscores
        name = name.strip('_')                    # Remove leading/trailing underscores
        name = name or 'interview'
        return name
    
    def _get_role_info(self, role_name: str):
        """Get role information as an object with type and traits.
        
        Args:
            role_name: Either 'alice' or 'bob'
            
        Returns:
            SimpleNamespace with type and traits properties
        """
        role = self._chatfield.get('roles', {}).get(role_name, {})
        
        # Start with explicit traits
        traits = set(role.get('traits', []))
        
        # Add possible traits that have been activated
        possible_traits = role.get('possible_traits', {})
        for trait_name, trait_info in possible_traits.items():
            if trait_info.get('active', False):
                traits.add(trait_name)
        
        return SimpleNamespace(
            type=role.get('type'),
            traits=list(traits)
        )
    
    @property
    def _alice(self):
        """Return alice role as an object with traits property."""
        return self._get_role_info('alice')
    
    @property
    def _bob(self):
        """Return bob role as an object with traits property."""
        return self._get_role_info('bob')
    
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
        role_type = role.get('type') or default
        return role_type
    
    def _get_role(self, role_name: str):
        roles = self._chatfield['roles']
        role = roles[role_name]
        # role = roles.get(role_name, {})
        return role
    
    def _get_chat_field(self, field_name: str):
        """Get the chatfield metadata for a field in this interview."""
        try:
            return self._chatfield['fields'][field_name]
        except KeyError:
            print(f'{self._name()}: Not a field: {field_name!r}, must be {self._chatfield["fields"].keys()!r}')
            # print(f'Available fields: {self._fields()}')
            raise KeyError(f'{self._name()}: Not a field: {field_name!r}')

    def _fields(self) -> List[str]:
        """Return a list of field names defined in this interview."""
        return self._chatfield['fields'].keys()

    def __getattr__(self, name: str):
        """Get field values or other attributes.
        
        For defined fields, returns either None or a FieldValueProxy.
        Overrides the method access to return field values instead.
        """
        # I'm not sure why this can happen, usually in the thread workers.
        if '_chatfield' not in self.__dict__:
            raise AttributeError(f'{self.__class__.__name__}: No such attribute: {name!r} (no _chatfield yet)')

        self_chatfield = self.__dict__['_chatfield']
        fields = self_chatfield['fields']
        chatfield = fields.get(name, None) # if fields else None
        if chatfield is None:
            raise AttributeError(f'{self.__class__.__name__}: No such attribute: {name!r}')

        # At this point, chatfield is definitely a field.
        llm_value = chatfield['value']
        if llm_value is None:
            # print(f'Return None to represent unpopulated field: {name!r}')
            return None
        
        # print(f'Valid field {name!r}: {llm_value!r}')
        primary_value = llm_value['value']
        proxy = FieldProxy(primary_value, chatfield)
        return proxy
    
    def _pretty(self) -> str:
        """Return a pretty representation of this interview."""
        lines = [f'{self._name()}']

        for field_name, chatfield in self._chatfield['fields'].items():
            proxy = getattr(self, field_name)
            if proxy is None:
                lines.append(f'  {field_name}: None')
            else:
                # field is a proxy
                # llm_value = chatfield['value']
                lines.append(f'  {field_name}: {proxy!r}')
                lines.append(proxy._pretty())
        return '\n'.join(lines)
    
    @property
    def _done(self):
        """Return whether all fields have been collected.
        
        Returns True when all fields have been populated with values.
        """
        fields = self._chatfield['fields']
        if not fields:
            raise Exception(f'{self._name()} has no fields defined, cannot be done.')

        chatfields = fields.values()
        all_values = [ chatfield['value'] for chatfield in chatfields ]
        return all(value is not None for value in all_values)
    
    @property
    def _enough(self):
        """Return whether all non-confidential, non-conclude fields have been
        collected, i.e. enough to wrap up the interview.
        
        Returns True when all fields which have confidential and conclude set to False are populated.
        """
        fields = self._chatfield['fields']
        for field_name, chatfield in fields.items():
            specs = chatfield['specs']
            if not specs['confidential']:
                if not specs['conclude']:
                    # This is a "normal" field.
                    if chatfield['value'] is None:
                        return False
        return True


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