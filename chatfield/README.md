# Chatfield: Conversational Data Collection

Transform data collection from rigid forms into natural conversations powered by LLMs.

## Quick Start

```python
from chatfield import Interview, Interviewer

class BugReport(Interview):
    """Bug report from user"""
    def title(): "Brief bug description"
    def steps(): "Steps to reproduce"
    def expected(): "What should happen"
    def actual(): "What actually happens"

# Conduct the interview
report = BugReport()
interviewer = Interviewer(report)
user_input = None

while not report._done:
    result = interviewer.go(user_input)
    # result['messages'] contains what to say
    for msg in result['messages']:
        print(f"{msg.__class__.__name__}: {msg.content}")
    user_input = input("> ")

# Access collected data
print(report.title)  # "Login button not working"
print(report.steps)  # "1. Go to homepage\n2. Click login..."
```

## Installation

```bash
pip install .
```

Set your OpenAI API key:
```bash
export OPENAI_API_KEY=your-api-key
```

## Adding Validation

```python
from chatfield import Interview, must, reject, hint

class APIKeyRequest(Interview):
    """API key request form"""
    
    @hint("Your company email, not personal")
    @must("company domain")
    @reject("gmail.com, yahoo.com, hotmail.com")
    def email(): "Work email address"
    
    @must("specific use case")
    @must("at least 20 words describing the project")
    def purpose(): "What you'll build with the API"
    
    @hint("Expected requests per day")
    @must("realistic estimate")
    def volume(): "Expected API call volume"
```

## Type Transformations

Convert free-form responses into structured data:

```python
from chatfield import Interview, as_int, as_bool, as_list, as_percent

class ProjectEstimate(Interview):
    """Project estimation"""
    
    @as_int
    @must("between 1 and 50")
    def team_size(): "Number of developers"
    
    @as_percent
    @hint("Your confidence level from 0-100%")
    def confidence(): "Confidence in timeline"
    
    @as_list
    @hint("List all major technologies")
    def technologies(): "Tech stack you'll use"
    
    @as_bool
    def needs_design(): "Need design resources?"

# After collection:
estimate.team_size      # 5 (int)
estimate.confidence     # 0.75 (float, from "75%")
estimate.technologies   # ["Python", "React", "PostgreSQL"]
estimate.needs_design   # True (bool)
```

## Advanced Transformations

Fields can have multiple transformations accessible via attributes:

```python
from chatfield import Interview, as_int, as_lang, as_bool, as_str, as_set

class FeatureRequest(Interview):
    """Feature request details"""
    
    # Multiple transformations on same field
    @as_int
    @as_lang.fr
    @as_lang.es
    @as_bool.even("True if even number of users")
    @as_bool.critical("True if affects more than 100 users")
    @as_str.uppercase("In all caps")
    @as_set.factors("Prime factors of the number")
    def affected_users(): "Number of users impacted"
    
    @hint("Describe the issue in detail")
    def description(): "Detailed description"

# After collection, if user said "two hundred":
request.affected_users                  # "200" (base string)
request.affected_users.as_int           # 200
request.affected_users.as_lang_fr       # "deux cents"
request.affected_users.as_lang_es       # "doscientos"
request.affected_users.as_bool_even     # True
request.affected_users.as_bool_critical # True
request.affected_users.as_str_uppercase # "TWO HUNDRED"
request.affected_users.as_set_factors   # {2, 5}
```

## Choice Cardinality

Control how many options can be selected:

```python
from chatfield import Interview, as_one, as_maybe, as_multi, as_any

class TaskAssignment(Interview):
    """Task assignment details"""
    
    @as_one("bug", "feature", "enhancement", "documentation")
    def task_type(): "Type of task"
    
    @as_maybe("low", "medium", "high", "critical")
    def priority(): "Priority level (if known)"
    
    @as_multi("frontend", "backend", "database", "infrastructure", "testing")
    def components(): "Affected system components"
    
    @as_any("Alice", "Bob", "Charlie", "Diana", "Eve")
    def reviewers(): "Optional reviewers"

# After collection:
assignment.task_type.as_one_task_type       # "bug"
assignment.priority.as_maybe_priority        # "high" or None
assignment.components.as_multi_components    # {"frontend", "backend"}
assignment.reviewers.as_any_reviewers        # {"Alice", "Diana"} or set()
```

## Persona Customization

Define the conversational roles and traits:

```python
from chatfield import Interview, alice, bob

@alice("Senior Technical Interviewer")
@alice.trait("Direct and technical")
@alice.trait("Focuses on architecture decisions")
@bob("Software Architect")
@bob.trait("10+ years experience")
@bob.trait("Prefers detailed technical discussions")
class ArchitectureReview(Interview):
    """Architecture review session"""
    
    @must("specific technology choices")
    def stack(): "Proposed technology stack"
    
    @must("quantifiable metrics")
    def scale(): "Expected scale and performance requirements"
    
    @must("clear trade-offs discussed")
    def decisions(): "Key architecture decisions"
```

## Complex Example

Combining all features:

```python
from chatfield import (
    Interview, Interviewer,
    alice, bob, must, reject, hint,
    as_int, as_float, as_percent, as_bool, as_list, as_dict, as_lang,
    as_one, as_maybe, as_multi, as_any
)

@alice("Product Manager")
@alice.trait("Focuses on user value and business impact")
@bob("Startup Founder")
@bob.trait("First-time founder, enthusiastic but inexperienced")
class ProductLaunch(Interview):
    """Product launch planning"""
    
    @must("clear value proposition")
    @must("target audience defined")
    @reject("everything for everyone")
    @hint("Who specifically will pay for this?")
    def product(): "Product description and target market"
    
    @as_int
    @as_lang.ja
    @must("realistic for MVP")
    @must("between 1000 and 100000")
    def first_year_users(): "First year user target"
    
    @as_percent
    @hint("Be realistic, most startups capture <5% initially")
    def market_share(): "Expected market share"
    
    @as_list
    @must("at least 3 competitors")
    def competitors(): "Direct competitors"
    
    @as_dict
    @hint("Feature: Fast delivery, Value: Same-day, Differentiator: Only one in region")
    def unique_value(): "Unique value proposition"
    
    @as_one("B2B", "B2C", "B2B2C", "marketplace")
    def model(): "Business model"
    
    @as_multi("organic", "paid_ads", "content", "partnerships", "social")
    @must("at least 2 channels")
    @must("no more than 3 to start")
    def channels(): "Marketing channels"
    
    @as_bool
    @as_bool.funded("True if you have funding")
    @as_bool.technical("True if you have technical co-founder")
    def ready(): "Ready to launch?"

# Conduct the interview
launch = ProductLaunch()
interviewer = Interviewer(launch)

# Run the conversational loop
user_input = None
while not launch._done:
    result = interviewer.go(user_input)
    for msg in result.get('messages', []):
        if hasattr(msg, 'content'):
            print(f"\n{msg.__class__.__name__}: {msg.content}")
    if not launch._done:
        user_input = input("\n> ")

# Access the collected data
print(f"Product: {launch.product}")
print(f"Target users: {launch.first_year_users.as_int:,}")
print(f"Target users (Japanese): {launch.first_year_users.as_lang_ja}")
print(f"Market share: {launch.market_share.as_percent:.1%}")
print(f"Competitors: {', '.join(launch.competitors.as_list)}")
print(f"Business model: {launch.model.as_one_model}")
print(f"Marketing: {', '.join(launch.channels.as_multi_channels)}")
print(f"Has funding: {launch.ready.as_bool_funded}")
print(f"Has technical co-founder: {launch.ready.as_bool_technical}")
```

## All Available Decorators

### Role Decorators
- `@alice(role)` - Set interviewer role
- `@alice.trait(trait)` - Add interviewer characteristic
- `@bob(role)` - Set interviewee role  
- `@bob.trait(trait)` - Add interviewee characteristic

### Validation Decorators
- `@must(rule)` - Content that must be included
- `@reject(rule)` - Content that must be avoided
- `@hint(tip)` - Helpful guidance for the user

### Type Cast Decorators
- `@as_int` - Parse as integer ("five" → 5)
- `@as_float` - Parse as float ("1.5k" → 1500.0)
- `@as_bool` - Parse as boolean ("yes" → True)
- `@as_str` - String with custom prompt
- `@as_percent` - Parse as 0.0-1.0 ("50%" → 0.5)
- `@as_list` - Parse as list
- `@as_set` - Parse as unique set
- `@as_dict` - Parse as dictionary
- `@as_lang` - Translate to language

### Sub-attribute Decorators

Type decorators can have sub-attributes for custom transformations:

- `@as_bool.{predicate}(description)` - Custom boolean check
- `@as_int.{transform}(description)` - Custom integer transform
- `@as_str.{format}(description)` - Custom string format
- `@as_lang.{code}` - Specific language (fr, es, ja, etc.)
- `@as_set.{operation}(description)` - Set operation

### Cardinality Decorators

Control selection from choices:

- `@as_one(choices...)` - Exactly one choice required
- `@as_maybe(choices...)` - Zero or one choice
- `@as_multi(choices...)` - One or more choices required
- `@as_any(choices...)` - Zero or more choices

## API Reference

### Core Classes

- `Interview` - Base class for defining conversational data structures
- `Interviewer` - Manages the conversation flow using LangGraph
- `FieldProxy` - String subclass providing transformation access

### Key Methods

- `Interviewer.go(user_input)` - Process one conversation turn
- `Interview._done` - Check if all fields are collected
- `Interview._pretty()` - Get formatted representation of collected data

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies: langchain, langgraph, pydantic, openai

## License

Apache 2.0 - see LICENSE file for details.