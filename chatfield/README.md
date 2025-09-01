# Chatfield: Conversational Data Collection

Transform data collection from rigid forms into natural conversations powered by LLMs.

## Quick Start

```python
from chatfield import chatfield, Interviewer

# Build your interview using the fluent builder API
bug_report = (chatfield()
    .type("Bug Report")
    .desc("Collecting bug report details")
    
    .field("steps")
        .desc("Steps to reproduce")
    
    .field("expected")
        .desc("What should happen")
    
    .field("actual")
        .desc("What actually happens")
    
    .build())

# Conduct the interview
interviewer = Interviewer(bug_report)

user_input = None
while not bug_report._done:
    message = interviewer.go(user_input) # Provide user input. The interviewer returns what to say.
    print(message)                       # Show it to the user.
    user_input = input("Your input > ")  # Receive user input.

# Access collected data
print("Tried", bug_report.steps)
print("Expected", bug_report.expected)
print("Actual", bug_report.actual)
```

## Installation

```bash
pip install .
```

Set your OpenAI API key:
```bash
export OPENAI_API_KEY=your-api-key
```

## Examples

The `examples/` directory contains complete working examples demonstrating various Chatfield features:

- **`restaurant_order.py`** - Dynamic trait activation, selection fields, confidential tracking
- **`job_interview.py`** - Professional interview flow with confidential assessments
- **`favorite_number.py`** - Extensive transformation system demonstration
- **`tech_request.py`** - Real-world business requirement gathering

Run any example interactively:
```bash
python examples/restaurant_order.py
```

Or with automated demo inputs:
```bash
python examples/restaurant_order.py --auto
```

See `examples/README.md` for detailed documentation of each example.

## Adding Validation

```python
from chatfield import chatfield

api_key_request = (chatfield()
    .type("API Key Request")
    .desc("API key request form")
    
    .field("email")
        .desc("Work email address")
        .hint("Your company email, not personal")
        .must("company domain")
        .reject("gmail.com, yahoo.com, hotmail.com")
    
    .field("purpose")
        .desc("What you'll build with the API")
        .must("specific use case")
        .must("at least 20 words describing the project")
    
    .field("volume")
        .desc("Expected API call volume")
        .hint("Expected requests per day")
        .must("realistic estimate")
    
    .build())
```

## Type Transformations

Convert free-form responses into structured data:

```python
from chatfield import chatfield

project_estimate = (chatfield()
    .type("Project Estimate")
    .desc("Project estimation")
    
    .field("team_size")
        .desc("Number of developers")
        .as_int()
        .must("between 1 and 50")
    
    .field("confidence")
        .desc("Confidence in timeline")
        .as_percent()
        .hint("Your confidence level from 0-100%")
    
    .field("technologies")
        .desc("Tech stack you'll use")
        .as_list()
        .hint("List all major technologies")
    
    .field("needs_design")
        .desc("Need design resources?")
        .as_bool()
    
    .build())

# After collection:
project_estimate.team_size.as_int      # 5 (int)
project_estimate.confidence.as_percent # 0.75 (float, from "75%")
project_estimate.technologies.as_list  # ["Python", "React", "PostgreSQL"]
project_estimate.needs_design.as_bool  # True (bool)
```

## Advanced Transformations

Fields can have multiple transformations accessible via attributes:

```python
from chatfield import chatfield

feature_request = (chatfield()
    .type("Feature Request")
    .desc("Feature request details")
    
    .field("affected_users")
        .desc("Number of users impacted")
        .as_int()
        .as_lang.fr()
        .as_lang.es()
        .as_bool.even("True if even number of users")
        .as_bool.critical("True if affects more than 100 users")
        .as_str.uppercase("In all caps")
        .as_set.factors("Prime factors of the number")
    
    .field("description")
        .desc("Detailed description")
        .hint("Describe the issue in detail")
    
    .build())

# After collection, if user said "two hundred":
feature_request.affected_users                  # "200" (base string)
feature_request.affected_users.as_int           # 200
feature_request.affected_users.as_lang_fr       # "deux cents"
feature_request.affected_users.as_lang_es       # "doscientos"
feature_request.affected_users.as_bool_even     # True
feature_request.affected_users.as_bool_critical # True
feature_request.affected_users.as_str_uppercase # "TWO HUNDRED"
feature_request.affected_users.as_set_factors   # {2, 5}
```

## Choice Cardinality

Control how many options can be selected:

```python
from chatfield import chatfield

task_assignment = (chatfield()
    .type("Task Assignment")
    .desc("Task assignment details")
    
    .field("task_type")
        .desc("Type of task")
        .as_one.selection("bug", "feature", "enhancement", "documentation")
    
    .field("priority")
        .desc("Priority level (if known)")
        .as_maybe.selection("low", "medium", "high", "critical")
    
    .field("components")
        .desc("Affected system components")
        .as_multi.selection("frontend", "backend", "database", "infrastructure", "testing")
    
    .field("reviewers")
        .desc("Optional reviewers")
        .as_any.selection("Alice", "Bob", "Charlie", "Diana", "Eve")
    
    .build())

# After collection:
task_assignment.task_type.as_one_selection       # "bug"
task_assignment.priority.as_maybe_selection      # "high" or None
task_assignment.components.as_multi_selection    # {"frontend", "backend"}
task_assignment.reviewers.as_any_selection       # {"Alice", "Diana"} or set()
```

## Persona Customization

Define the conversational roles and traits:

```python
from chatfield import chatfield

architecture_review = (chatfield()
    .type("Architecture Review")
    .desc("Architecture review session")
    
    .alice()
        .type("Senior Technical Interviewer")
        .trait("Direct and technical")
        .trait("Focuses on architecture decisions")
    
    .bob()
        .type("Software Architect")
        .trait("10+ years experience")
        .trait("Prefers detailed technical discussions")
    
    .field("stack")
        .desc("Proposed technology stack")
        .must("specific technology choices")
    
    .field("scale")
        .desc("Expected scale and performance requirements")
        .must("quantifiable metrics")
    
    .field("decisions")
        .desc("Key architecture decisions")
        .must("clear trade-offs discussed")
    
    .build())
```

### Dynamic Traits

Traits can be dynamically activated based on user responses:

```python
from chatfield import chatfield

restaurant_order = (chatfield()
    .type("Restaurant Order")
    
    .bob()
        .trait("First-time visitor")
        .trait.possible("Vegan", "needs vegan, plant-based, non animal product")
    
    .field("main_course")
        .desc("Main course selection")
        .as_one.selection("Grilled salmon", "Veggie pasta", "Beef tenderloin")
    
    .build())

# If the user mentions being vegan, the "Vegan" trait activates
# and the AI adapts its suggestions accordingly
```

## Confidential and Conclude Fields

### Confidential Fields

Confidential fields are tracked silently during the conversation without being directly asked:

```python
from chatfield import chatfield

job_interview = (chatfield()
    .type("Job Interview")
    .desc("Technical interview")
    
    .field("experience")
        .desc("Years of relevant experience")
        .as_int()
    
    .field("mentoring")
        .desc("Has mentoring experience")
        .confidential()  # Noted if mentioned, not directly asked
        .as_bool()
    
    .build())

# After interview:
print(f"Experience: {job_interview.experience.as_int} years")
print(f"Mentions mentoring: {job_interview.mentoring.as_bool}")
```

### Conclude Fields

Conclude fields are evaluated only after all other fields are collected. They're automatically confidential:

```python
from chatfield import chatfield

interview = (chatfield()
    .type("Technical Interview")
    .desc("Evaluate the entire conversation for technical aptitude and communication")
    
    .field("technical_skills")
        .desc("Technical competencies")
    
    .field("project_experience")
        .desc("Relevant project background")
    
    .field("communication_skill")
        .desc("Communication clarity and effectiveness throughout the entire conversation")
        .conclude()  # Evaluated at the end based on entire conversation
        .as_percent()
    
    .build())

# The conclude fields are filled after the conversation ends,
# based on the full context of all responses
```

## Complex Example

Combining all features:

```python
from chatfield import chatfield, Interviewer

product_launch = (chatfield()
    .type("Product Launch")
    .desc("Product launch planning")
    
    .alice()
        .type("Product Manager")
        .trait("Focuses on user value and business impact")
    
    .bob()
        .type("Startup Founder")
        .trait("First-time founder, enthusiastic but inexperienced")
    
    .field("product")
        .desc("Product description and target market")
        .must("clear value proposition")
        .must("target audience defined")
        .reject("everything for everyone")
        .hint("Who specifically will pay for this?")
    
    .field("first_year_users")
        .desc("First year user target")
        .as_int()
        .as_lang.ja()
        .must("realistic for MVP")
        .must("between 1000 and 100000")
    
    .field("market_share")
        .desc("Expected market share")
        .as_percent()
        .hint("Be realistic, most startups capture <5% initially")
    
    .field("competitors")
        .desc("Direct competitors")
        .as_list()
        .must("at least 3 competitors")
    
    .field("unique_value")
        .desc("Unique value proposition")
        .as_dict()
        .hint("Feature: Fast delivery, Value: Same-day, Differentiator: Only one in region")
    
    .field("model")
        .desc("Business model")
        .as_one.selection("B2B", "B2C", "B2B2C", "marketplace")
    
    .field("channels")
        .desc("Marketing channels")
        .as_multi.selection("organic", "paid_ads", "content", "partnerships", "social")
        .must("at least 2 channels")
        .must("no more than 3 to start")
    
    .field("ready")
        .desc("Ready to launch?")
        .as_bool()
        .as_bool.funded("True if you have funding")
        .as_bool.technical("True if you have technical co-founder")
    
    .field("enthusiasm")
        .desc("Level of founder enthusiasm")
        .confidential()  # Assessed during conversation
        .as_percent()
    
    .field("viability")
        .desc("Overall business viability assessment")
        .conclude()  # Evaluated at the end
        .as_percent()
    
    .build())

# Conduct the interview
interviewer = Interviewer(product_launch)

# Run the conversational loop
user_input = None
while not product_launch._done:
    ai_message = interviewer.go(user_input)
    if ai_message:
        print(f"\nAI: {ai_message}")
    if not product_launch._done:
        user_input = input("\n> ")

# Access the collected data
print(f"Product: {product_launch.product}")
print(f"Target users: {product_launch.first_year_users.as_int:,}")
print(f"Target users (Japanese): {product_launch.first_year_users.as_lang_ja}")
print(f"Market share: {product_launch.market_share.as_percent:.1%}")
print(f"Competitors: {', '.join(product_launch.competitors.as_list)}")
print(f"Business model: {product_launch.model.as_one_selection}")
print(f"Marketing: {', '.join(product_launch.channels.as_multi_selection)}")
print(f"Has funding: {product_launch.ready.as_bool_funded}")
print(f"Has technical co-founder: {product_launch.ready.as_bool_technical}")
print(f"Enthusiasm: {product_launch.enthusiasm.as_percent:.0%}")
print(f"Viability: {product_launch.viability.as_percent:.0%}")
```

## Builder API Reference

The builder API provides a fluent interface for creating interviews:

### Core Builder Methods

- `chatfield()` - Start building a new interview
- `.type(name)` - Set the interview type name
- `.desc(description)` - Set the interview description
- `.build()` - Build the final Interview object

### Role Configuration

- `.alice()` - Configure the interviewer role
- `.bob()` - Configure the interviewee role
- `.type(role_type)` - Set role type (after .alice() or .bob())
- `.trait(trait)` - Add a trait
- `.trait.possible(name, trigger)` - Add a conditional trait

### Field Definition

- `.field(name)` - Start defining a field
- `.desc(description)` - Set field description
- `.must(rule)` - Add a requirement
- `.reject(rule)` - Add a rejection rule
- `.hint(tip)` - Add helpful guidance
- `.confidential()` - Mark as silently tracked
- `.conclude()` - Evaluate only at end

### Type Transformations

Apply transformations with method calls:

- `.as_int()` - Parse as integer
- `.as_float()` - Parse as float
- `.as_bool()` - Parse as boolean
- `.as_str()` - String format
- `.as_percent()` - Parse as 0.0-1.0
- `.as_list()` - Parse as list
- `.as_set()` - Parse as unique set
- `.as_dict()` - Parse as dictionary
- `.as_lang.{code}()` - Translate to language

### Custom Transformations

Add sub-attributes for custom transformations:

- `.as_bool.{predicate}(description)` - Custom boolean check
- `.as_int.{transform}(description)` - Custom integer transform
- `.as_str.{format}(description)` - Custom string format
- `.as_set.{operation}(description)` - Set operation

### Choice Cardinality

Control selection from choices:

- `.as_one.selection(choices...)` - Exactly one choice required
- `.as_maybe.selection(choices...)` - Zero or one choice
- `.as_multi.selection(choices...)` - One or more choices required
- `.as_any.selection(choices...)` - Zero or more choices

## API Reference

### Core Classes

- `Interview` - Base class for defining conversational data structures
- `Interviewer` - Manages the conversation flow using LangGraph
- `FieldProxy` - String subclass providing transformation access

### Key Methods

- `Interviewer.go(user_input)` - Process one conversation turn, returns AI message as string
- `Interview._done` - Check if all fields are collected  
- `Interview._pretty()` - Get formatted representation of collected data

### Legacy Decorator API

The original decorator-based API is still available for backward compatibility:

```python
from chatfield import Interview, alice, bob, must, as_int

@alice("Interviewer")
class MyInterview(Interview):
    @must("specific answer")
    @as_int
    def age(): "Your age"
```

However, the builder API is now recommended for new projects as it provides better IDE support and a more intuitive interface.

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies: langchain, langgraph, pydantic, openai

## License

Apache 2.0 - see LICENSE file for details.