# Chatfield Implementation Plan

## Overview
Implement the initial Chatfield Python package based on the comprehensive README.md and CLAUDE.md specifications. The package uses a clever decorator-based API to transform classes into conversational data gatherers powered by LLMs.

## Core Architecture

### Package Structure
```
chatfield/
├── __init__.py          # Main exports and version
├── decorators.py        # Core decorators (@gather, @must, @reject, @hint, @user, @agent)
├── gatherer.py          # GathererMeta and FieldMeta classes
├── conversation.py      # Conversation state management
├── llm_backend.py       # LLM integration (OpenAI backend)
├── presets.py           # Preset decorators (@patient_teacher, etc.)
├── builder.py           # GathererBuilder for dynamic creation
├── pyproject.toml       # Modern Python packaging
└── tests/               # Comprehensive test suite
    ├── __init__.py
    ├── test_decorators.py
    ├── test_gatherer.py
    ├── test_conversation.py
    └── test_integration.py
```

### Key Design Principles

1. **Decorator-based API** - All configuration through decorators, not inheritance
2. **String-only data** - All fields are strings, no complex types
3. **LLM-powered validation** - Validation rules are prompts, not code
4. **Conversational UX** - Natural dialogue, not step-by-step forms
5. **Minimal magic** - Use Python's existing features cleverly

### The Clever Syntax Trick

Abuse Python's type annotation syntax to store field descriptions:
```python
concept: "Your business concept"  # This becomes __annotations__['concept'] = "Your business concept"
```

This is syntactically valid Python that gives us clean field definitions without requiring string type declarations.

## Core Components

### 1. Metadata Classes (`gatherer.py`)

**GathererMeta**: Store all metadata for a gatherer class
- User context declarations
- Agent behavior context
- Docstring description
- Field definitions and metadata

**FieldMeta**: Store metadata for individual fields
- Field name and description
- Must/reject validation rules
- Hint tooltips
- No conditional logic (@when removed from design)

### 2. Core Decorators (`decorators.py`)

**@gather**: Transform a class into a conversational gatherer
- Process __annotations__ to find field descriptions
- Collect metadata from field and class decorators
- Add gather() class method
- Return enhanced class

**Field Decorators** that stack metadata:
- `@must(rule)` - Validation requirements
- `@reject(rule)` - What to avoid in answers
- `@hint(tooltip)` - Helpful context for users

**Class-level Decorators**:
- `@user(context)` - Information about the user
- `@agent(behavior)` - How agent should behave

### 3. Conversation Management (`conversation.py`)

**Conversation Class**:
- Track collected data
- Manage conversation history
- Determine which field to ask about next
- Validate responses using LLM
- Handle validation failures gracefully

**Flow Logic**:
1. Get next uncollected field
2. Build conversation prompt with context
3. Get user response
4. Validate against must/reject rules
5. Store valid data or retry on failure

### 4. LLM Integration (`llm_backend.py`)

**LLMBackend Abstract Base**:
- Create conversation prompts
- Get LLM responses
- Handle streaming and retries

**OpenAIBackend Implementation**:
- Use GPT-4 for best results
- Include all context (docstring, user/agent, field rules)
- Build clear validation prompts
- Handle API errors gracefully

### 5. Preset Decorators (`presets.py`)

Common behavior patterns:
- `@patient_teacher` - For explaining complex topics
- `@quick_diagnosis` - For urgent problem-solving
- `@friendly_expert` - For ongoing consultation

These combine multiple @user/@agent decorators into reusable presets.

### 6. Dynamic Creation (`builder.py`)

Support for creating gatherers programmatically:
```python
def create_tech_helper(user_profile):
    @gather
    @user(f"Tech level: {user_profile.tech_level}")
    class PersonalizedHelper:
        challenge: "What technical challenge are you facing?"
    return PersonalizedHelper
```

## Implementation Details

### Decorator Stacking

Fields can have multiple decorators that build up metadata:
```python
@hint("Be specific")
@must("includes timeline")
@reject("vague promises")
project: "Your project description"
```

These stack in reverse order, building up the field's metadata.

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

### The Main gather() Method

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

## Usage Patterns to Support

### Basic Usage
```python
@gather
class Simple:
    name: "Your name"
    email: "Your email"

result = Simple.gather()
print(result.name)  # Access collected data
```

### With Validation
```python
@gather
class Validated:
    @must("specific problem")
    @hint("What's broken?")
    issue: "Describe your issue"
```

### Multiple Context
```python
@gather
@user("Small business owner, not technical")
@user("Probably frustrated with tech complexity")
@agent("Friendly neighborhood tech expert")
@agent("Use analogies to explain technical concepts")
class BusinessHelp:
    business: "Tell me about your business"
```

### Dynamic Creation
```python
def create_gatherer(user_info):
    @gather
    @user(f"User age: {user_info.age}")
    class Dynamic:
        need: "What do you need?"
    return Dynamic

Helper = create_gatherer(user_data)
result = Helper.gather()
```

## Testing Strategy

### Unit Tests
- Decorator behavior and stacking
- Metadata extraction from classes
- Field processing and validation
- Error handling for invalid usage

### Integration Tests
- Complete conversation flows with mock LLM
- Validation logic with various responses
- Multiple context handling
- Dynamic gatherer creation

### Real LLM Tests (Optional/Slow)
- End-to-end conversations with OpenAI
- Validation behavior in practice
- Error recovery and retry logic

## Error Handling

- Invalid decorator usage (helpful error messages)
- LLM failures (retry with backoff)
- Validation loops (max retries, helpful guidance)
- Missing API keys (clear setup instructions)
- Malformed class definitions

## Dependencies

- **openai** - For LLM integration
- **pydantic** - For data validation (optional)
- **pytest** - For testing
- **python-dotenv** - For environment variables

## Future Considerations

- Multiple LLM backends (Anthropic, local models)
- Conversation saving/resuming
- Voice input/output
- Integration with existing form libraries
- Parallel field gathering
- Advanced conversation management

## Implementation Phases

### Phase 1: Core MVP
1. Package structure and dependencies
2. Basic decorators and metadata classes
3. Simple conversation flow
4. OpenAI integration
5. Basic validation

### Phase 2: Advanced Features
1. Preset decorators
2. Dynamic gatherer creation
3. Comprehensive error handling
4. Advanced conversation management

### Phase 3: Testing & Polish
1. Comprehensive unit tests
2. Integration tests with mock LLM
3. Real LLM tests
4. Documentation and examples
5. Performance optimization

This plan provides a roadmap for implementing Chatfield as a robust, well-tested Python package that delivers on the conversational data gathering vision outlined in the README.