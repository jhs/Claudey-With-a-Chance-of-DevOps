"""Dynamic Socratic dialogue class creation utilities."""

from typing import Dict, List, Any, Type, Optional
from .decorators import gather, user, agent, must, reject, hint


class SocratesBuilder:
    """Builder for creating Socratic dialogue classes programmatically."""
    
    def __init__(self, name: str = "DynamicSocrates"):
        self.name = name
        self.docstring = ""
        self.user_contexts: List[str] = []
        self.agent_contexts: List[str] = []
        self.fields: Dict[str, Dict[str, Any]] = {}
    
    def set_docstring(self, docstring: str) -> 'SocratesBuilder':
        """Set the class docstring."""
        self.docstring = docstring
        return self
    
    def add_user_context(self, context: str) -> 'SocratesBuilder':
        """Add user context information."""
        self.user_contexts.append(context)
        return self
    
    def add_agent_context(self, behavior: str) -> 'SocratesBuilder':
        """Add agent behavior context."""
        self.agent_contexts.append(behavior)
        return self
    
    def add_field(
        self, 
        name: str, 
        description: str,
        must_rules: Optional[List[str]] = None,
        reject_rules: Optional[List[str]] = None,
        hint_text: Optional[str] = None
    ) -> 'SocratesBuilder':
        """Add a field with validation rules and hints."""
        self.fields[name] = {
            'description': description,
            'must_rules': must_rules or [],
            'reject_rules': reject_rules or [],
            'hint': hint_text
        }
        return self
    
    def build(self) -> Type:
        """Build and return the Socratic dialogue class."""
        # Create the class attributes dictionary
        class_attrs = {
            '__doc__': self.docstring,
            '__annotations__': {}
        }
        
        # Add field annotations
        for field_name, field_info in self.fields.items():
            class_attrs['__annotations__'][field_name] = field_info['description']
            
            # Create field attribute with metadata
            field_attr = field_info['description']
            
            # Add metadata to the field attribute
            if field_info.get('must_rules'):
                if not hasattr(field_attr, '_chatfield_must_rules'):
                    field_attr = type('FieldProxy', (), {
                        '_chatfield_must_rules': field_info['must_rules'],
                        '_chatfield_reject_rules': field_info.get('reject_rules', []),
                        '_chatfield_hint': field_info.get('hint')
                    })()
            
            class_attrs[field_name] = field_attr
        
        # Create the dynamic class
        cls = type(self.name, (), class_attrs)
        
        # Apply user contexts
        for context in self.user_contexts:
            cls = user(context)(cls)
        
        # Apply agent contexts
        for behavior in self.agent_contexts:
            cls = agent(behavior)(cls)
        
        # Apply the @gather decorator
        cls = gather(cls)
        
        return cls


def create_socrates_from_dict(config: Dict[str, Any]) -> Type:
    """Create a Socratic dialogue class from a configuration dictionary.
    
    Args:
        config: Dictionary with keys:
            - name (str): Class name
            - docstring (str): Class description
            - user_contexts (list): User context strings
            - agent_contexts (list): Agent behavior strings
            - fields (dict): Field definitions
    
    Returns:
        Socratic dialogue class ready to use
    """
    builder = SocratesBuilder(config.get('name', 'ConfigSocrates'))
    
    if 'docstring' in config:
        builder.set_docstring(config['docstring'])
    
    for context in config.get('user_contexts', []):
        builder.add_user_context(context)
    
    for behavior in config.get('agent_contexts', []):
        builder.add_agent_context(behavior)
    
    for field_name, field_config in config.get('fields', {}).items():
        if isinstance(field_config, str):
            # Simple field definition
            builder.add_field(field_name, field_config)
        elif isinstance(field_config, dict):
            # Complex field definition
            builder.add_field(
                field_name,
                field_config['description'],
                field_config.get('must_rules'),
                field_config.get('reject_rules'),
                field_config.get('hint')
            )
    
    return builder.build()


def create_socrates_from_template(
    template_name: str, 
    customizations: Optional[Dict[str, Any]] = None
) -> Type:
    """Create a Socratic dialogue class from a predefined template.
    
    Args:
        template_name: Name of the template to use
        customizations: Optional customizations to apply
    
    Returns:
        Socratic dialogue class ready to use
    """
    templates = {
        'tech_support': {
            'name': 'TechSupport',
            'docstring': 'Technical support request',
            'user_contexts': [
                'Has a technical problem that needs solving',
                'May not be technical, needs clear explanations'
            ],
            'agent_contexts': [
                'Helpful technical support specialist',
                'Ask clarifying questions to understand the issue',
                'Provide step-by-step solutions'
            ],
            'fields': {
                'problem': {
                    'description': 'What technical problem are you experiencing?',
                    'must_rules': ['specific problem description'],
                    'hint': 'Be specific - what exactly is not working?'
                },
                'when_started': 'When did this problem start?',
                'what_tried': 'What have you tried so far to fix it?',
                'system_info': {
                    'description': 'What type of device or system are you using?',
                    'hint': 'Computer, phone, software name, etc.'
                }
            }
        },
        
        'business_consultation': {
            'name': 'BusinessConsultation',
            'docstring': 'Business consultation and planning session',
            'user_contexts': [
                'Business owner or entrepreneur',
                'Making important business decisions',
                'Needs practical, actionable advice'
            ],
            'agent_contexts': [
                'Experienced business consultant',
                'Focus on practical, implementable solutions',
                'Ask about budget, timeline, and constraints'
            ],
            'fields': {
                'business_type': {
                    'description': 'What type of business do you have or want to start?',
                    'must_rules': ['specific business type or industry'],
                    'hint': 'e.g., restaurant, consulting, e-commerce, etc.'
                },
                'challenge': {
                    'description': 'What business challenge are you facing?',
                    'must_rules': ['specific business problem'],
                    'reject_rules': ['vague statements']
                },
                'timeline': 'What timeline are you working with?',
                'budget': {
                    'description': 'What budget do you have available?',
                    'must_rules': ['specific amount or range'],
                    'hint': 'Even a rough range helps - $1K, $10K, $100K+?'
                }
            }
        },
        
        'website_planning': {
            'name': 'WebsitePlanning',
            'docstring': 'Website planning and requirements gathering',
            'user_contexts': [
                'Needs a website for their business or project',
                'May not be technical',
                'Wants practical, implementable solution'
            ],
            'agent_contexts': [
                'Web development consultant',
                'Help clarify requirements and scope',
                'Focus on what\'s actually needed vs. nice-to-have'
            ],
            'fields': {
                'purpose': {
                    'description': 'What should your website accomplish?',
                    'must_rules': ['specific business goal'],
                    'hint': 'Sell products? Generate leads? Share information?'
                },
                'target_audience': {
                    'description': 'Who will be visiting your website?',
                    'must_rules': ['specific target audience'],
                    'hint': 'Your customers, not "everyone"'
                },
                'content': 'What content do you need on the website?',
                'budget': {
                    'description': 'What\'s your budget for building and maintaining the website?',
                    'must_rules': ['specific amount or range'],
                    'reject_rules': ['as cheap as possible', 'money is no object']
                }
            }
        }
    }
    
    if template_name not in templates:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(templates.keys())}")
    
    config = templates[template_name].copy()
    
    # Apply customizations if provided
    if customizations:
        config.update(customizations)
    
    return create_socrates_from_dict(config)