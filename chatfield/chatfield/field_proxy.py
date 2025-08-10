"""Field proxy for providing match attribute access to field values."""

from typing import Dict, Optional
from .socrates import FieldMeta


class FieldValueProxy:
    """Proxy object that provides match attribute access to field values.
    
    This allows field values to have dynamic attributes based on @match decorators.
    For example, if a field has @match.is_personal("..."), then the field value
    will have a .is_personal attribute that returns True/False/None.
    """
    
    def __init__(self, value: str, field_meta: FieldMeta, evaluations: Optional[Dict[str, Optional[bool]]] = None):
        """Initialize the field value proxy.
        
        Args:
            value: The actual string value of the field
            field_meta: Metadata about the field including match rules
            evaluations: Dict mapping match names to their evaluated boolean values
        """
        self._value = value
        self._field_meta = field_meta
        self._evaluations = evaluations or {}
    
    def __str__(self) -> str:
        """Return the string value when converted to string."""
        return self._value
    
    def __repr__(self) -> str:
        """Return a representation of the proxy."""
        value_preview = self._value[:50] + '...' if len(self._value) > 50 else self._value
        return f"FieldValueProxy(field='{self._field_meta.name}', value='{value_preview}')"
    
    def __eq__(self, other) -> bool:
        """Allow equality comparison with strings."""
        if isinstance(other, str):
            return self._value == other
        if isinstance(other, FieldValueProxy):
            return self._value == other._value
        return False
    
    def __len__(self) -> int:
        """Return the length of the underlying string value."""
        return len(self._value)
    
    def __bool__(self) -> bool:
        """Return True if the value is not empty."""
        return bool(self._value)
    
    def __getattr__(self, name: str):
        """Provide access to match rule evaluations.
        
        Args:
            name: The name of the match rule (e.g., 'is_personal')
            
        Returns:
            The boolean evaluation result, or None if not evaluated
            
        Raises:
            AttributeError: If the match rule doesn't exist
        """
        # Check if this is a match rule for this field
        if name in self._field_meta.match_rules:
            # Skip internal must/reject rules - they shouldn't be accessed directly
            # TODO: Is this necessary? Maybe allow it? - Jason
            if name.startswith('_must_') or name.startswith('_reject_'):
                raise AttributeError(
                    f"Internal validation rule '{name}' is not accessible as an attribute. "
                    f"Must/reject rules are used for validation only."
                )
            
            # Return the evaluation result (could be True, False, or None)
            return self._evaluations.get(name, None)
        
        # If not a match rule, raise AttributeError
        raise AttributeError(
            f"Field '{self._field_meta.name}' has no match rule '{name}'. "
            f"Available match rules: {[k for k in self._field_meta.match_rules.keys() if not k.startswith('_')]}"
        )
    
    @property
    def value(self) -> str:
        """Get the raw string value."""
        return self._value
    
    def get_match_evaluation(self, match_name: str) -> Optional[bool]:
        """Get the evaluation result for a specific match rule.
        
        Args:
            match_name: The name of the match rule
            
        Returns:
            True/False if evaluated, None if not evaluated or doesn't exist
        """
        return self._evaluations.get(match_name, None)
    
    def set_match_evaluation(self, match_name: str, result: bool) -> None:
        """Set the evaluation result for a match rule.
        
        Args:
            match_name: The name of the match rule
            result: The boolean evaluation result
        """
        if match_name in self._field_meta.match_rules:
            self._evaluations[match_name] = result