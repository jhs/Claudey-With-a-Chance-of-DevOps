"""Field proxy for providing match attribute access to field values."""

from typing import Dict, Optional, Any, Union
from .socrates import FieldMeta


class FieldValueProxy(str):
    """Proxy object that provides match attribute access to field values.
    
    This proxy allows field values to:
    1. Behave as a normal string with all string methods
    2. Access match rule evaluations via attributes (e.g., field.is_personal)
    3. Access type transformations via as_* attributes (e.g., field.as_int)
    
    Example:
        field = FieldValueProxy("100 dollars", meta, evaluations, transformations)
        field == "100 dollars"  # Direct string comparison
        field.upper() == "100 DOLLARS"  # String methods work
        field.is_large == True  # Match evaluation
        field.as_int == 100  # Type transformation
    """
    
    def __new__(cls, value: str, field_meta: FieldMeta,
                evaluations: Optional[Dict[str, Optional[bool]]] = None,
                transformations: Optional[Dict[str, Any]] = None):
        """Create a new string-based proxy instance.
        
        Args:
            value: The actual string value of the field
            field_meta: Metadata about the field including match rules
            evaluations: Dict mapping match names to their evaluated boolean values
            transformations: Dict mapping transformation names to their transformed values
        """
        # Create the string instance with the value
        instance = str.__new__(cls, value)
        return instance
    
    def __init__(self, value: str, field_meta: FieldMeta, 
                 evaluations: Optional[Dict[str, Optional[bool]]] = None,
                 transformations: Optional[Dict[str, Any]] = None):
        """Initialize the field value proxy metadata.
        
        Note: The string value is already set in __new__, this just stores metadata.
        
        Args:
            value: The actual string value of the field (for compatibility)
            field_meta: Metadata about the field including match rules
            evaluations: Dict mapping match names to their evaluated boolean values
            transformations: Dict mapping transformation names to their transformed values
        """
        # Don't call str.__init__ as it doesn't take arguments
        # Store metadata for the proxy functionality
        self._field_meta = field_meta
        self._evaluations = evaluations or {}
        self._transformations = transformations or {}
    
    def __repr__(self) -> str:
        """Return a representation of the proxy."""
        # Use self directly since we're now a string
        value_preview = self[:50] + '...' if len(self) > 50 else self
        return f"FieldValueProxy(field='{self._field_meta.name}', value='{value_preview}')"
    
    def __getattr__(self, name: str):
        """Provide access to match rule evaluations and type transformations.
        
        Args:
            name: The name of the match rule (e.g., 'is_personal') or 
                  transformation (e.g., 'as_int')
            
        Returns:
            The evaluation/transformation result, or None if not evaluated
            
        Raises:
            AttributeError: If the attribute doesn't exist
        """
        # Check if this is a transformation (as_* attributes)
        if name.startswith('as_'):
            if name in self._transformations:
                return self._transformations[name]
            # Check if transformation is defined but not evaluated yet
            if hasattr(self._field_meta, 'transformations') and name in self._field_meta.transformations:
                return None  # Transformation defined but not evaluated
            # If not a known transformation, raise AttributeError
            raise AttributeError(
                f"Field '{self._field_meta.name}' has no transformation '{name}'. "
                f"Available transformations: {[k for k in self._transformations.keys()]}"
            )
        
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
        
        # If not a match rule or transformation, raise AttributeError
        raise AttributeError(
            f"Field '{self._field_meta.name}' has no attribute '{name}'. "
            f"Available match rules: {[k for k in self._field_meta.match_rules.keys() if not k.startswith('_')]}, "
            f"Available transformations: {[k for k in self._transformations.keys()]}"
        )
    
    @property
    def value(self) -> str:
        """Get the raw string value."""
        # Return self since we ARE the string
        return str(self)
    
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