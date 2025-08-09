"""Core metadata classes for Chatfield Socratic dialogue system."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import inspect


@dataclass
class FieldMeta:
    """Metadata for a single field in a Socratic dialogue."""
    
    name: str
    description: str
    must_rules: List[str] = field(default_factory=list)
    reject_rules: List[str] = field(default_factory=list)
    hints: List[str] = field(default_factory=list)
    
    def add_must_rule(self, rule: str) -> None:
        """Add a validation requirement."""
        self.must_rules.append(rule)
    
    def add_reject_rule(self, rule: str) -> None:
        """Add a validation rejection rule."""
        self.reject_rules.append(rule)
    
    def add_hint(self, hint: str) -> None:
        """Add a hint tooltip."""
        self.hints.append(hint)
    
    def has_validation_rules(self) -> bool:
        """Check if this field has any validation rules."""
        return bool(self.must_rules or self.reject_rules)


@dataclass
class SocratesMeta:
    """Metadata for a Socratic dialogue class."""
    
    user_context: List[str] = field(default_factory=list)
    agent_context: List[str] = field(default_factory=list)
    docstring: str = ""
    fields: Dict[str, FieldMeta] = field(default_factory=dict)
    
    def add_user_context(self, context: str) -> None:
        """Add user context information."""
        self.user_context.append(context)
    
    def add_agent_context(self, context: str) -> None:
        """Add agent behavior context."""
        self.agent_context.append(context)
    
    def set_docstring(self, docstring: str) -> None:
        """Set the class docstring."""
        self.docstring = docstring.strip() if docstring else ""
    
    def add_field(self, name: str, description: str) -> FieldMeta:
        """Add a field and return its metadata object."""
        field_meta = FieldMeta(name=name, description=description)
        self.fields[name] = field_meta
        return field_meta
    
    def get_field(self, name: str) -> Optional[FieldMeta]:
        """Get field metadata by name."""
        return self.fields.get(name)
    
    def get_field_names(self) -> List[str]:
        """Get all field names in order."""
        return list(self.fields.keys())
    
    def has_context(self) -> bool:
        """Check if this gatherer has any context information."""
        return bool(self.user_context or self.agent_context or self.docstring)


class SocratesInstance:
    """Instance created after completing a Socratic dialogue conversation."""
    
    def __init__(self, meta: SocratesMeta, collected_data: Dict[str, str]):
        self._meta = meta
        self._data = collected_data.copy()
    
    def __getattr__(self, name: str) -> str:
        """Allow access to collected data as attributes."""
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"No field '{name}' was collected")
    
    def __repr__(self) -> str:
        """String representation of collected data."""
        fields = ", ".join(f"{k}='{v[:50]}...'" if len(v) > 50 else f"{k}='{v}'" 
                          for k, v in self._data.items())
        return f"SocratesInstance({fields})"
    
    def get_data(self) -> Dict[str, str]:
        """Get all collected data as a dictionary."""
        return self._data.copy()
    
    def get(self, field_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get field value with optional default."""
        return self._data.get(field_name, default)


def process_socrates_class(cls: type) -> SocratesMeta:
    """Extract all metadata from a decorated class for Socratic dialogue."""
    meta = SocratesMeta()
    
    # Get docstring
    if cls.__doc__:
        meta.set_docstring(cls.__doc__)
    
    # Get user/agent context from class metadata (set by decorators)
    if hasattr(cls, '_chatfield_user_context'):
        meta.user_context = getattr(cls, '_chatfield_user_context', [])
    if hasattr(cls, '_chatfield_agent_context'):
        meta.agent_context = getattr(cls, '_chatfield_agent_context', [])
    
    # Process fields from function definitions  
    # Look for functions that represent field definitions
    for attr_name in dir(cls):
        # Skip private attributes and built-in methods
        if attr_name.startswith('_'):
            continue
            
        attr_obj = getattr(cls, attr_name)
        
        # Check if this is a function with a docstring (our field definition)
        # Must be a regular function, not a method, static method, or class method
        if (inspect.isfunction(attr_obj) and 
            attr_obj.__doc__ and 
            not isinstance(inspect.getattr_static(cls, attr_name), staticmethod) and
            not isinstance(inspect.getattr_static(cls, attr_name), classmethod)):
            
            # Check function signature - should have no parameters (no self, no args)
            sig = inspect.signature(attr_obj)
            if len(sig.parameters) == 0:
                field_name = attr_name
                field_desc = attr_obj.__doc__.strip()
                
                # Create field metadata
                field_meta = meta.add_field(field_name, field_desc)
                
                # Get field metadata set by decorators
                if hasattr(attr_obj, '_chatfield_must_rules'):
                    field_meta.must_rules = getattr(attr_obj, '_chatfield_must_rules', [])
                if hasattr(attr_obj, '_chatfield_reject_rules'):
                    field_meta.reject_rules = getattr(attr_obj, '_chatfield_reject_rules', [])
                if hasattr(attr_obj, '_chatfield_hints'):
                    field_meta.hints = getattr(attr_obj, '_chatfield_hints', [])
    
    return meta