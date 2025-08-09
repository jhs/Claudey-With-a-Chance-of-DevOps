# CLAUDE.md - Chatfield Implementation Guide

## Overview

Chatfield is a Python package that transforms data gathering from rigid forms into natural conversations. It uses decorators to define fields and validation rules, then leverages LLMs to have helpful conversations that collect structured data.

## Core Architecture

### Key Design Principles

1. **Decorator-based API** - All configuration through decorators, not inheritance
2. **String-only data** - All fields are strings, no complex types
3. **LLM-powered validation** - Validation rules are prompts, not code
4. **Conversational UX** - Natural dialogue, not step-by-step forms
5. **Minimal magic** - Use Python's existing features cleverly

### The Clever Syntax Trick

We abuse Python's type annotation syntax to store field descriptions:

```python
concept: "Your business concept"  # This becomes __annotations__['concept'] = "Your business concept"
```

This is syntactically valid Python that gives us clean field definitions without requiring string type declarations.

## Implementation Structure

```
chatfield/
├── __init__.py          # Main exports
├── decorators.py        # Core decorators (@gather, @must, etc.)
├── gatherer.py          # Gatherer class and metadata
├── conversation.py      # LangGraph-based conversation management
├── agent.py             # LangGraph agent implementation
├── builder.py           # GathererBuilder for dynamic creation
└── presets.py           # Common preset decorators
```

## Core Components to Implement

### 1. Decorators (`decorators.py`)

```python
# @gather decorator
def gather(cls):
    """Transform a class into a conversational gatherer"""
    # 1. Store original class metadata
    # 2. Process __annotations__ to find fields
    # 3. Collect decorators from each field
    # 4. Add gather() class method
    # 5. Return enhanced class

# Field decorators that stack metadata
def must(rule: str):
    """Mark what answer must include"""
    # Store rule in field metadata
    
def reject(rule: str):
    """Mark what to avoid in answers"""
    # Store rule in field metadata

def hint(tooltip: str):
    """Helpful context for users"""
    # Store tooltip in field metadata

# Class-level decorators
def user(context: str):
    """Information about the user"""
    # Store in class metadata

def agent(behavior: str):
    """How agent should behave"""
    # Store in class metadata
```

### 2. Gatherer Base Logic (`gatherer.py`)

```python
class GathererMeta:
    """Metadata for a gatherer class"""
    def __init__(self):
        self.user_context = []
        self.agent_context = []
        self.docstring = ""
        self.fields = {}  # name -> FieldMeta

class FieldMeta:
    """Metadata for a single field"""
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.must_rules = []
        self.reject_rules = []
        self.hint = None
        self.when_condition = None

def process_gatherer_class(cls):
    """Extract all metadata from decorated class"""
    # 1. Get docstring
    # 2. Get user/agent context from class decorators
    # 3. Process each field in __annotations__
    # 4. Extract decorators from each field
    # 5. Build GathererMeta object
    # 6. Add gather() method to class
```

### 3. Conversation Management (`conversation.py`)

```python
class Conversation:
    """Manages conversations using LangGraph agents."""
    def __init__(self, meta: GathererMeta, **kwargs):
        self.meta = meta
        self.agent = ChatfieldAgent(meta, **kwargs)
        self.collected_data = {}
        
    def conduct_conversation(self):
        """Run the conversation to collect all data."""
        # Uses LangGraph agent to manage conversation flow
        # Returns collected data dictionary
```

### 4. LangGraph Agent (`agent.py`)

```python
class ChatfieldAgent:
    """LangGraph-based conversational agent for data gathering."""
    
    def __init__(self, meta: GathererMeta, llm=None, **kwargs):
        self.meta = meta
        self.llm = llm or ChatOpenAI()  # Default to OpenAI
        self.graph = self._build_graph()
        
    def _build_graph(self):
        """Build the LangGraph workflow."""
        # Creates state machine with nodes for:
        # - Field selection
        # - Question asking
        # - Response validation
        # - Data collection
        
    def run(self, initial_data=None):
        """Run the conversation and collect data."""
        # Execute the graph and return collected data
```

### 5. The Main gather() Method

```python
def gather(self) -> 'GathererInstance':
    """Main entry point - conducts the conversation"""
    # 1. Create Conversation instance
    # 2. Build initial prompt with context
    # 3. Start conversation loop:
    #    a. Get next field to collect
    #    b. Ask about it conversationally
    #    c. Validate response
    #    d. Handle invalid responses gracefully
    #    e. Store valid data
    # 4. Return instance with all collected data
```

## Key Implementation Details

### Decorator Stacking

Fields can have multiple decorators that build up metadata:

```python
@hint("Be specific")
@must("includes timeline")
@reject("vague promises")
project: "Your project description"
```

These stack in reverse order (hint processes last), building up the field's metadata.

### Processing __annotations__

After decorators run, scan `cls.__annotations__` to find field descriptions:

```python
for field_name, field_desc in cls.__annotations__.items():
    if isinstance(field_desc, str):
        # This is one of our fields
        # Get metadata that decorators attached
        # Build FieldMeta object
```

### Validation Prompts

Build clear prompts for the LLM to validate responses:

```python
prompt = f"""
The user provided this answer: {response}

For the field "{field.description}", validate that the answer:
- MUST include: {', '.join(field.must_rules)}
- MUST NOT include: {', '.join(field.reject_rules)}

If valid, respond "VALID".
If not valid, explain what's missing or wrong in a helpful way.
"""
```

## Usage Patterns to Support

### Basic Usage
```python
@gather
class Simple:
    name: "Your name"
    email: "Your email"

result = Simple.gather()
```

### With Validation
```python
@gather
class Validated:
    @must("specific problem")
    @hint("What's broken?")
    issue: "Describe your issue"
```

### Dynamic Creation
```python
def create_gatherer(user_info):
    @gather
    @user(f"User age: {user_info.age}")
    class Dynamic:
        need: "What do you need?"
    return Dynamic
```

## Testing Strategy

1. **Unit tests** for decorator behavior
2. **Integration tests** with real OpenAI API (requires API key)
3. **Conversation flow tests** for complex scenarios
4. Tests use `@pytest.mark.skipif` when API key not available

## Error Handling

- Invalid decorator usage (helpful error messages)
- LLM failures (retry with backoff)
- Validation loops (max retries, helpful guidance)
- Missing API keys (clear setup instructions)

## Future Considerations

- Multiple LLM backends (Anthropic, local models)
- Conversation saving/resuming
- Parallel field gathering
- Voice input/output
- Integration with existing form libraries

## Initial MVP Scope

Focus on:
1. Core decorators working
2. Basic conversation flow
3. OpenAI integration
4. Simple validation
5. Clear error messages

Skip for now:
- Dynamic gatherers
- Complex conditional logic
- Multiple LLM providers
- Advanced conversation management