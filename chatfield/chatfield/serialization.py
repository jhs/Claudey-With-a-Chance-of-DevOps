"""Serialization support for Chatfield Interview objects.

This module provides functions to serialize and deserialize Interview instances
to/from msgpack-compatible dictionaries, preserving all metadata and field values.
"""

from typing import Dict, Any, List, Optional, Type
import inspect
from .interview import Interview
from .socrates import SocratesMeta, FieldMeta


def dialogue_to_msgpack_dict(dialogue: Interview) -> Dict[str, Any]:
    """Convert a Interview instance to a msgpack-compatible dictionary.
    
    This captures:
    1. The complete class definition metadata (decorators, fields, etc.)
    2. Current field values with their evaluations and transformations
    
    Args:
        dialogue: The Interview instance to serialize
        
    Returns:
        A dictionary containing only msgpack-serializable types
    """
    cls = dialogue.__class__
    meta = dialogue._meta
    
    # Serialize class metadata
    result = {
        "class_name": cls.__name__,
        "module_name": cls.__module__,
        "class_docstring": cls.__doc__ or "",
        "user_context": list(meta.user_context),
        "agent_context": list(meta.agent_context),
        "fields": [],
        "field_values": {}
    }
    
    # Serialize field definitions with their decorators in order
    for field_name, field_meta in meta.fields.items():
        field_def = {
            "name": field_name,
            "description": field_meta.description,
            "decorators": []
        }
        
        # Get the original function to access decorator metadata
        if hasattr(cls, field_name):
            field_func = getattr(cls, field_name)
            
            # Collect decorators in the order they were applied
            decorators = []
            
            # Hints
            if hasattr(field_func, '_chatfield_hints'):
                for hint in field_func._chatfield_hints:
                    decorators.append({"type": "hint", "value": hint})
            
            # Must rules (legacy and new)
            if hasattr(field_func, '_chatfield_must_rules'):
                for rule in field_func._chatfield_must_rules:
                    decorators.append({"type": "must", "value": rule})
            
            # Reject rules (legacy and new)
            if hasattr(field_func, '_chatfield_reject_rules'):
                for rule in field_func._chatfield_reject_rules:
                    decorators.append({"type": "reject", "value": rule})
            
            # Match rules (custom matches like @match.is_personal)
            if hasattr(field_func, '_chatfield_match_rules'):
                for match_name, match_data in field_func._chatfield_match_rules.items():
                    # Skip internal must/reject rules as they're handled above
                    if not match_name.startswith('_must_') and not match_name.startswith('_reject_'):
                        decorators.append({
                            "type": "match",
                            "name": match_name,
                            "criteria": match_data.get('criteria', '')
                        })
            
            # Type transformations (@as_int, @as_float, etc.)
            if hasattr(field_func, '_chatfield_transformations'):
                for trans_name, trans_data in field_func._chatfield_transformations.items():
                    if trans_name.startswith('as_'):
                        decorator_entry = {
                            "type": "transformation",
                            "name": trans_name,
                            "description": trans_data.get('description', '')
                        }
                        # Include any additional kwargs (like item_type for as_list)
                        for key, value in trans_data.items():
                            if key not in ['description', 'type', 'criteria']:
                                decorator_entry[key] = value
                        decorators.append(decorator_entry)
            
            field_def["decorators"] = decorators
        
        result["fields"].append(field_def)
    
    # Serialize field values with evaluations and transformations
    for field_name in meta.fields:
        field_value = dialogue._field_values.get(field_name)
        
        if field_value is not None:
            # Get the raw string value (FieldValueProxy is a string subclass)
            value_data = {
                "value": str(field_value),
                "evaluations": {},
                "transformations": {}
            }
            
            # If it's a FieldValueProxy, get evaluations and transformations
            if hasattr(field_value, '_evaluations'):
                value_data["evaluations"] = dict(field_value._evaluations)
            
            if hasattr(field_value, '_transformations'):
                # Only include actual transformation results, not metadata
                for trans_name, trans_value in field_value._transformations.items():
                    # Convert sets to lists for msgpack compatibility
                    if isinstance(trans_value, set):
                        value_data["transformations"][trans_name] = list(trans_value)
                    else:
                        value_data["transformations"][trans_name] = trans_value
            
            result["field_values"][field_name] = value_data
    
    return result


def msgpack_dict_to_dialogue(data: Dict[str, Any], dialogue_class: Optional[Type[Interview]] = None) -> Interview:
    """Reconstruct a Interview instance from a msgpack dictionary.
    
    Args:
        data: The msgpack-compatible dictionary created by dialogue_to_msgpack_dict
        dialogue_class: Optional class to use. If not provided, will attempt to 
                       dynamically recreate the class from metadata.
        
    Returns:
        A reconstructed Interview instance with all field values and evaluations
    """
    # If no class provided, try to find it or create it dynamically
    if dialogue_class is None:
        # Try to import the original class
        try:
            module_name = data.get("module_name", "__main__")
            class_name = data["class_name"]
            
            if module_name == "__main__":
                # For classes defined in __main__, we'll need to recreate them
                dialogue_class = _recreate_dialogue_class(data)
            else:
                # Try to import from the module
                import importlib
                module = importlib.import_module(module_name)
                dialogue_class = getattr(module, class_name)
        except (ImportError, AttributeError):
            # Fall back to recreating the class
            dialogue_class = _recreate_dialogue_class(data)
    
    # Create instance
    instance = dialogue_class()
    
    # Restore field values with evaluations and transformations
    for field_name, value_data in data.get("field_values", {}).items():
        if field_name in instance._meta.fields:
            evaluations = value_data.get("evaluations", {})
            transformations = value_data.get("transformations", {})
            
            # Convert lists back to sets where appropriate
            for trans_name, trans_value in transformations.items():
                if trans_name == "as_set" and isinstance(trans_value, list):
                    transformations[trans_name] = set(trans_value)
            
            instance._set_field_value(
                field_name,
                value_data["value"],
                evaluations=evaluations,
                transformations=transformations
            )
    
    return instance


def _recreate_dialogue_class(data: Dict[str, Any]) -> Type[Interview]:
    """Dynamically recreate a Interview class from serialized metadata.
    
    This is used when the original class is not available for import.
    
    Args:
        data: The serialized class metadata
        
    Returns:
        A dynamically created Interview class with all decorators applied
    """
    from . import decorators, match, types
    
    # Create class attributes dictionary
    class_attrs = {}
    
    # Add class docstring
    if data.get("class_docstring"):
        class_attrs['__doc__'] = data["class_docstring"]
    
    # Add user and agent context as class attributes
    if data.get("user_context"):
        class_attrs['_chatfield_user_context'] = data["user_context"]
    if data.get("agent_context"):
        class_attrs['_chatfield_agent_context'] = data["agent_context"]
    
    # Recreate field methods with their decorators
    for field_def in data.get("fields", []):
        # Create a function for the field
        def make_field_func(desc):
            def field_func():
                return desc
            field_func.__doc__ = desc
            return field_func
        
        field_func = make_field_func(field_def["description"])
        field_func.__name__ = field_def["name"]
        
        # Apply decorators (in reverse order since decorators are applied bottom-up)
        for decorator_def in reversed(field_def.get("decorators", [])):
            dec_type = decorator_def["type"]
            
            if dec_type == "hint":
                field_func = decorators.hint(decorator_def["value"])(field_func)
            elif dec_type == "must":
                field_func = decorators.must(decorator_def["value"])(field_func)
            elif dec_type == "reject":
                field_func = decorators.reject(decorator_def["value"])(field_func)
            elif dec_type == "match":
                # Use the match decorator dynamically
                match_decorator = getattr(match.match, decorator_def["name"])
                field_func = match_decorator(decorator_def["criteria"])(field_func)
            elif dec_type == "transformation":
                trans_name = decorator_def["name"]
                # Find the right transformation decorator
                if hasattr(types, trans_name):
                    trans_decorator = getattr(types, trans_name)
                    # Handle decorators that take arguments
                    if trans_name == "as_list" and "item_type" in decorator_def:
                        # For now, we'll use Any as the type since we can't reconstruct the actual type
                        field_func = trans_decorator()(field_func)
                    elif trans_name == "as_dict" and "keys" in decorator_def:
                        field_func = trans_decorator(*decorator_def["keys"])(field_func)
                    elif trans_name in ["as_choice", "as_choose_one", "as_choose_many"] and "choices" in decorator_def:
                        field_func = trans_decorator(*decorator_def["choices"])(field_func)
                    else:
                        field_func = trans_decorator(field_func)
        
        class_attrs[field_def["name"]] = field_func
    
    # Create the class dynamically
    class_name = data.get("class_name", "RestoredInterview")
    dialogue_class = type(class_name, (Interview,), class_attrs)
    
    # Apply class-level decorators
    for context in data.get("user_context", []):
        dialogue_class = decorators.user(context)(dialogue_class)
    for context in data.get("agent_context", []):
        dialogue_class = decorators.agent(context)(dialogue_class)
    
    return dialogue_class


def metadata_to_dict(meta: SocratesMeta) -> Dict[str, Any]:
    """Convert SocratesMeta to a msgpack-compatible dictionary.
    
    Args:
        meta: The metadata object to serialize
        
    Returns:
        A dictionary containing only msgpack-serializable types
    """
    result = {
        "user_context": list(meta.user_context),
        "agent_context": list(meta.agent_context),
        "docstring": meta.docstring,
        "fields": {}
    }
    
    for field_name, field_meta in meta.fields.items():
        result["fields"][field_name] = {
            "name": field_meta.name,
            "description": field_meta.description,
            "match_rules": dict(field_meta.match_rules),
            "transformations": dict(field_meta.transformations),
            "hints": list(field_meta.hints),
            "must_rules": list(field_meta.must_rules),
            "reject_rules": list(field_meta.reject_rules)
        }
    
    return result


def dict_to_metadata(data: Dict[str, Any]) -> SocratesMeta:
    """Reconstruct SocratesMeta from a dictionary.
    
    Args:
        data: Dictionary created by metadata_to_dict
        
    Returns:
        A reconstructed SocratesMeta object
    """
    meta = SocratesMeta()
    meta.user_context = data.get("user_context", [])
    meta.agent_context = data.get("agent_context", [])
    meta.docstring = data.get("docstring", "")
    
    for field_name, field_data in data.get("fields", {}).items():
        field_meta = FieldMeta(
            name=field_data["name"],
            description=field_data["description"]
        )
        field_meta.match_rules = field_data.get("match_rules", {})
        field_meta.transformations = field_data.get("transformations", {})
        field_meta.hints = field_data.get("hints", [])
        field_meta.must_rules = field_data.get("must_rules", [])
        field_meta.reject_rules = field_data.get("reject_rules", [])
        
        meta.fields[field_name] = field_meta
    
    return meta