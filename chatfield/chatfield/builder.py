"""Builder API for creating Chatfield interviews."""

import copy
from typing import Optional, List, Dict, Any, TYPE_CHECKING

# if TYPE_CHECKING:
from .interview import Interview


class TraitBuilder:
    """Builder for trait.possible() pattern."""
    
    def __init__(self, parent: 'RoleBuilder', role: str):
        self.parent = parent
        self.role = role
    
    def __call__(self, trait: str):
        """Add a regular trait."""
        self.parent._add_trait(self.role, trait)
        return self.parent
    
    def possible(self, name: str, trigger: str = ""):
        """Add a possible trait with optional trigger guidance."""
        self.parent._add_possible_trait(self.role, name, trigger)
        return self.parent


class RoleBuilder:
    """Builder for alice/bob role configuration."""
    
    def __init__(self, parent: 'ChatfieldBuilder', role: str):
        self.parent = parent
        self.role = role
        self._ensure_role()
        # Set context for subsequent calls
        self.parent._current_role = role
        self.trait = TraitBuilder(self, role)
    
    def _ensure_role(self):
        """Ensure role exists in chatfield structure."""
        if self.role not in self.parent._chatfield['roles']:
            self.parent._chatfield['roles'][self.role] = {
                'type': None,
                'traits': [],
                'possible_traits': {}
            }
    
    def type(self, role_type: str):
        """Set the role type."""
        self.parent._chatfield['roles'][self.role]['type'] = role_type
        return self
    
    def _add_trait(self, role: str, trait: str):
        """Add a regular trait."""
        if trait not in self.parent._chatfield['roles'][role]['traits']:
            self.parent._chatfield['roles'][role]['traits'].append(trait)
    
    def _add_possible_trait(self, role: str, name: str, trigger: str):
        """Add a possible trait."""
        self.parent._chatfield['roles'][role]['possible_traits'][name] = {
            'active': False,
            'desc': trigger
        }
    
    def field(self, name: str):
        """Start defining a new field."""
        return self.parent.field(name)
    
    def alice(self):
        """Switch to alice configuration."""
        return self.parent.alice()
    
    def bob(self):
        """Switch to bob configuration."""
        return self.parent.bob()
    
    def build(self):
        """Build the final Interview."""
        return self.parent.build()


class CastBuilder:
    """Builder for cast decorators with sub-attributes."""
    
    def __init__(self, parent: 'FieldBuilder', base_name: str, primitive_type: type, base_prompt: str):
        self.parent = parent
        self.base_name = base_name
        self.primitive_type = primitive_type
        self.base_prompt = base_prompt
    
    def __call__(self, prompt: Optional[str] = None):
        """Apply the base cast."""
        cast_info = {
            'type': self.primitive_type.__name__,
            'prompt': prompt or self.base_prompt
        }
        self.parent._chatfield_field['casts'][self.base_name] = cast_info
        return self.parent
    
    def __getattr__(self, name: str):
        """Handle sub-attributes like as_lang.fr."""
        if name.startswith('_'):
            raise AttributeError(f"No attribute {name}")
        
        compound_name = f'{self.base_name}_{name}'
        compound_prompt = self.base_prompt.format(name=name) if '{name}' in self.base_prompt else f'{self.base_prompt} for {name}'
        
        def sub_cast(prompt: Optional[str] = None):
            cast_info = {
                'type': self.primitive_type.__name__,
                'prompt': prompt or compound_prompt
            }
            self.parent._chatfield_field['casts'][compound_name] = cast_info
            return self.parent
        
        return sub_cast


class ChoiceBuilder:
    """Builder for choice cardinality decorators."""
    
    def __init__(self, parent: 'FieldBuilder', base_name: str, null: bool, multi: bool):
        self.parent = parent
        self.base_name = base_name
        self.null = null
        self.multi = multi
    
    def __getattr__(self, name: str):
        """Handle sub-attributes like as_one.parity."""
        if name.startswith('_'):
            raise AttributeError(f"No attribute {name}")
        
        compound_name = f'{self.base_name}_{name}'
        
        def choice_cast(*choices):
            cast_info = {
                'type': 'choice',
                'prompt': f"Choose for {name}",
                'choices': list(choices),
                'null': self.null,
                'multi': self.multi
            }
            self.parent._chatfield_field['casts'][compound_name] = cast_info
            return self.parent
        
        return choice_cast


class FieldBuilder:
    """Builder for individual fields."""
    
    def __init__(self, parent: 'ChatfieldBuilder', name: str):
        self.parent = parent
        self.name = name
        self._chatfield_field = {
            'desc': name,  # Default to field name
            'specs': {
                'must': [],
                'reject': [],
                'hint': [],
                'confidential': False,
                'conclude': False
            },
            'casts': {},
            'value': None
        }
        # Add to parent's fields
        self.parent._chatfield['fields'][name] = self._chatfield_field
        self.parent._current_field = name
        
        # Initialize cast builders
        self.as_int = CastBuilder(self, 'as_int', int, 'Parse as integer')
        self.as_float = CastBuilder(self, 'as_float', float, 'Parse as floating point number')
        self.as_bool = CastBuilder(self, 'as_bool', bool, 'Parse as boolean')
        self.as_str = CastBuilder(self, 'as_str', str, 'Format as string')
        self.as_percent = CastBuilder(self, 'as_percent', float, 'Parse as percentage (0.0 to 1.0)')
        self.as_list = CastBuilder(self, 'as_list', list, 'Parse as list/array')
        self.as_set = CastBuilder(self, 'as_set', set, 'Parse as unique set')
        self.as_dict = CastBuilder(self, 'as_dict', dict, 'Parse as key-value dictionary')
        self.as_obj = self.as_dict  # Alias
        self.as_lang = CastBuilder(self, 'as_lang', str, 'Translate to {name}')
        
        # Choice builders
        self.as_one = ChoiceBuilder(self, 'as_one', null=False, multi=False)
        self.as_maybe = ChoiceBuilder(self, 'as_maybe', null=True, multi=False)
        self.as_multi = ChoiceBuilder(self, 'as_multi', null=False, multi=True)
        self.as_any = ChoiceBuilder(self, 'as_any', null=True, multi=True)
    
    def desc(self, description: str):
        """Set field description."""
        self._chatfield_field['desc'] = description
        return self
    
    def must(self, rule: str):
        """Add a validation requirement."""
        self._chatfield_field['specs']['must'].append(rule)
        return self
    
    def reject(self, rule: str):
        """Add a rejection rule."""
        self._chatfield_field['specs']['reject'].append(rule)
        return self
    
    def hint(self, tooltip: str):
        """Add helpful context."""
        if not self._chatfield_field['specs'].get('hint'):
            self._chatfield_field['specs']['hint'] = []
        self._chatfield_field['specs']['hint'].append(tooltip)
        return self
    
    def confidential(self):
        """Mark field as confidential (tracked silently)."""
        self._chatfield_field['specs']['confidential'] = True
        return self
    
    def conclude(self):
        """Mark field for evaluation only after conversation ends (automatically confidential)."""
        self._chatfield_field['specs']['conclude'] = True
        self._chatfield_field['specs']['confidential'] = True  # Implied
        return self
    
    def optional(self):
        """Mark field as optional (future feature)."""
        # TODO: Implement optional field handling
        return self
    
    def when(self, condition):
        """Set conditional visibility (future feature)."""
        # TODO: Implement conditional field logic
        return self
    
    def field(self, name: str):
        """Start defining a new field."""
        return self.parent.field(name)
    
    def alice(self):
        """Switch to alice configuration."""
        return self.parent.alice()
    
    def bob(self):
        """Switch to bob configuration."""
        return self.parent.bob()
    
    def build(self):
        """Build the final Interview."""
        return self.parent.build()


class ChatfieldBuilder:
    """Main builder for creating Chatfield interviews."""
    
    def __init__(self):
        self._chatfield = {
            'type': '',
            'desc': '',
            'roles': {},
            'fields': {}
        }
        self._current_field: Optional[str] = None
        self._current_role: Optional[str] = None
    
    def type(self, name: str):
        """Set the interview type name."""
        self._chatfield['type'] = name
        return self
    
    def desc(self, description: str):
        """Set the interview description."""
        self._chatfield['desc'] = description
        return self
    
    def alice(self):
        """Configure alice (interviewer) role."""
        return RoleBuilder(self, 'alice')
    
    def bob(self):
        """Configure bob (interviewee) role."""
        return RoleBuilder(self, 'bob')
    
    def field(self, name: str):
        """Define a new field."""
        return FieldBuilder(self, name)
    
    def build(self):
        """Build the final Interview object."""
        # Create Interview instance with the built structure and override its _chatfield.
        interview = Interview()
        interview._chatfield = copy.deepcopy(self._chatfield)
        
        # Ensure roles are properly initialized
        if 'alice' not in interview._chatfield['roles']:
            interview._chatfield['roles']['alice'] = {
                'type': None,
                'traits': [],
                'possible_traits': {}
            }
        if 'bob' not in interview._chatfield['roles']:
            interview._chatfield['roles']['bob'] = {
                'type': None, 
                'traits': [],
                'possible_traits': {}
            }
        
        # Ensure possible_traits dict exists for each role
        for role in interview._chatfield['roles'].values():
            if 'possible_traits' not in role:
                role['possible_traits'] = {}
        
        return interview


def chatfield():
    """Create a new Chatfield builder."""
    return ChatfieldBuilder()


# Preset builders for common patterns
def patient_gatherer():
    """Create a patient, thorough gatherer."""
    return (chatfield()
        .alice()
            .trait("patient and thorough")
            .trait("asks follow-up questions when answers seem incomplete")
            .trait("provides helpful examples when users seem confused"))


def quick_gatherer():
    """Create a quick, efficient gatherer."""
    return (chatfield()
        .alice()
            .trait("concise and efficient")
            .trait("accepts brief answers when they meet requirements")
            .trait("moves quickly through fields"))


def expert_gatherer():
    """Create an expert consultation gatherer."""
    return (chatfield()
        .alice()
            .trait("assumes domain expertise")
            .trait("asks detailed technical questions")
            .trait("expects comprehensive, specific answers"))