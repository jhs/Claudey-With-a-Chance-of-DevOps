# CLAUDE.md - Chatfield Implementation Guide

## Overview

Chatfield is a Python package that transforms data gathering from rigid forms into conversational dialogues powered by LLMs. It uses a decorator-based API to define fields and validation rules, then leverages LangGraph to orchestrate natural conversations that collect structured data.

## Core Architecture

### Key Design Principles

1. **Decorator-based API** - All configuration through decorators, no complex inheritance
2. **String-based fields** - All field values are strings with transformation access
3. **LLM-powered validation** - Validation through conversational guidance
4. **Stateful conversation** - LangGraph manages conversation state and flow
5. **Transformation proxies** - Field values provide transformed access via attributes

## Implementation Structure

```
chatfield/
├── __init__.py          # Main exports
├── interview.py         # Interview base class
├── interviewer.py       # Interviewer with LangGraph orchestration
├── decorators.py        # All decorator implementations
├── field_proxy.py       # FieldProxy string subclass (imported by interview.py)
└── presets.py           # Common preset decorators (future)
```

## Core Components

### 1. Interview Class (`interview.py`)

The `Interview` base class manages field definitions and collected data:

```python
class Interview:
    """Base class for conversational data collection."""
    
    def __init__(self, **kwargs):
        # Initialize _chatfield dictionary structure
        self._chatfield = {
            'type': self.__class__.__name__,
            'desc': self.__doc__,
            'roles': {
                'alice': {'type': None, 'traits': []},
                'bob': {'type': None, 'traits': []}
            },
            'fields': {
                # field_name: {
                #     'desc': field description,
                #     'specs': {category: [rules]},  # from @must, @reject, @hint
                #     'casts': {name: cast_info},    # from @as_* decorators
                #     'value': None or {value, context, as_quote, ...}
                # }
            }
        }
```

Key features:
- Discovers fields via method definitions
- Stores all metadata in `_chatfield` dictionary
- Provides `__getattribute__` override to return field values as `FieldProxy` instances
- Implements `_done` property to check completion
- Supports serialization via `model_dump()` for LangGraph state

### 2. FieldProxy Class (`interview.py`)

`FieldProxy` is a string subclass that provides transformation access:

```python
class FieldProxy(str):
    """String that provides transformation access via attributes."""
    
    def __new__(cls, value: str, chatfield: Dict):
        # Create string instance with the base value
        instance = str.__new__(cls, value)
        return instance
    
    def __getattr__(self, attr_name: str):
        # Return transformation values
        # e.g., field.as_int, field.as_lang_fr
        llm_value = self._chatfield.get('value')
        if attr_name in llm_value:
            return llm_value[attr_name]
```

This allows natural access patterns:
- `field` - base string value
- `field.as_int` - integer transformation
- `field.as_lang_fr` - French translation
- All string methods work normally

### 3. Interviewer Class (`interviewer.py`)

Manages conversation flow using LangGraph:

```python
class Interviewer:
    """Orchestrates conversational data collection."""
    
    def __init__(self, interview: Interview, thread_id: str = None):
        self.interview = interview
        self.llm = init_chat_model('openai:gpt-4')
        self.graph = self._build_graph()
        
    def _build_graph(self):
        # LangGraph state machine with nodes:
        # - initialize: Setup conversation
        # - think: LLM generates next message
        # - listen: Wait for user input (interrupt)
        # - tools: Process field updates
        # - teardown: Complete conversation
        
    def go(self, user_input: Optional[str]):
        # Process one conversation turn
        # Returns dict with 'messages' key
```

The Interviewer:
- Creates LangGraph workflow with conversation nodes
- Generates dynamic tools for each field
- Manages conversation state and checkpointing
- Returns messages for the UI to display

### 4. Decorator System (`decorators.py`)

Three main decorator types:

#### InterviewDecorator (Role decorators)
```python
class InterviewDecorator:
    """@alice and @bob decorators"""
    
alice = InterviewDecorator('alice')
bob = InterviewDecorator('bob')

# Usage:
# @alice("Senior Developer")
# @alice.trait("Direct communication")
```

#### FieldSpecificationDecorator (Validation)
```python
class FieldSpecificationDecorator:
    """@must, @reject, @hint decorators"""
    
must = FieldSpecificationDecorator('must')
reject = FieldSpecificationDecorator('reject')
hint = FieldSpecificationDecorator('hint')

# Stores rules in func._chatfield['specs']
```

#### FieldCastDecorator (Type transformations)
```python
class FieldCastDecorator:
    """Type transformation decorators"""
    
    def __init__(self, name, primitive_type, prompt, sub_only=False):
        # sub_only=True means can only be used as @decorator.sub_attr
        
as_int = FieldCastDecorator('as_int', int, 'parse as integer')
as_lang = FieldCastDecorator('as_lang', str, 'translate to {name}', sub_only=True)

# Stores in func._chatfield['casts']
```

#### FieldCastChoiceDecorator (Cardinality)
```python
class FieldCastChoiceDecorator(FieldCastDecorator):
    """Choice cardinality decorators"""
    
as_one = FieldCastChoiceDecorator('choose_exactly_one', ...)
as_maybe = FieldCastChoiceDecorator('choose_zero_or_one', ...)
as_multi = FieldCastChoiceDecorator('choose_one_or_more', ...)
as_any = FieldCastChoiceDecorator('choose_zero_or_more', ...)
```

## Data Flow

1. **Definition Phase**
   - User defines Interview subclass with decorated methods
   - Decorators attach metadata to methods

2. **Initialization Phase**
   - Interview.__init__ discovers all methods
   - Builds _chatfield structure from decorator metadata
   - Creates field definitions with specs and casts

3. **Conversation Phase**
   - Interviewer creates LangGraph workflow
   - Generates tools for field validation/collection
   - Orchestrates conversation via state machine

4. **Collection Phase**
   - User responses validated by LLM
   - Valid data stored in _chatfield['fields'][name]['value']
   - Includes base value and all transformations

5. **Access Phase**
   - Field access returns FieldProxy instances
   - FieldProxy provides string value and transformation attributes
   - All transformations computed by LLM during collection

## State Management

The system uses LangGraph's state management with custom reducers:

```python
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    interview: Annotated[Interview, merge_interviews]

def merge_interviews(a: Interview, b: Interview) -> Interview:
    # Custom reducer that merges Interview states
    # Handles field value updates
```

## Tool Generation

For each field, the Interviewer generates a Pydantic model for tool arguments:

```python
# For a field with @as_int and @as_lang.fr decorators:
class FieldModel(BaseModel):
    value: str = Field(description="Natural value")
    context: str = Field(description="Conversational context")
    as_quote: str = Field(description="Direct quote")
    as_int: int = Field(description="Parse as integer")
    as_lang_fr: str = Field(description="Translate to French")
```

## Key Implementation Details

### Field Discovery
Fields are discovered by examining class methods:
- Any method without leading underscore is a field
- Method docstring becomes field description
- Decorators add metadata to `method._chatfield`

### Transformation Naming
Transformations follow consistent naming:
- Simple: `as_int`, `as_float`
- Sub-attributes: `as_lang_fr`, `as_bool_even`
- Choices: `as_one_priority`, `as_multi_components`

### Thread Safety
Each Interviewer maintains its own:
- LangGraph checkpointer
- Thread ID for conversation isolation
- Independent state management

## Usage Patterns

### Basic Interview
```python
class SimpleInterview(Interview):
    def name(): "Your name"
    def email(): "Your email"

interview = SimpleInterview()
interviewer = Interviewer(interview)

while not interview._done:
    result = interviewer.go(user_input)
    # Display messages, get user input
```

### With Full Decorators
```python
@alice("Interviewer")
@bob("Candidate")
class JobInterview(Interview):
    @must("specific role")
    @as_int
    @as_lang.fr
    def years_experience(): "Years of experience"
```

### Accessing Data
```python
# After collection:
interview.years_experience          # "5" (string)
interview.years_experience.as_int   # 5
interview.years_experience.as_lang_fr # "cinq"
```

## Testing Strategy

1. **Unit tests** - Test individual components
2. **Integration tests** - Test component interactions
3. **Mock LLM tests** - Test without API calls
4. **Live API tests** - Test with real OpenAI API

## Future Enhancements

- Multiple LLM provider support
- Conversation resumption from checkpoints
- Parallel field collection
- Dynamic field generation
- Custom validation functions
- Webhook integrations