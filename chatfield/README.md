# Chatfield: The Socratic Method for Data Gathering

Transform rigid forms into thoughtful Socratic dialogues powered by LLMs and LangGraph agents. Through careful questioning and guided exploration, Chatfield helps users articulate their needs clearly and completely.

## The Socratic Approach

Just as Socrates used thoughtful questioning to help people discover truth and understanding, Chatfield employs a Socratic dialogue method to gather information. Rather than presenting users with intimidating forms or technical jargon, it engages them in natural conversation that:

- **Guides discovery** - Questions that help users explore and clarify their own thoughts
- **Encourages reflection** - Validation that prompts users to think more deeply about their answers  
- **Builds understanding** - Each question builds on previous answers, creating coherent understanding
- **Adapts naturally** - The conversation adjusts to the user's level and responses

```python
from chatfield import Dialogue, must, reject, hint

class TechHelp(Dialogue):
    """Your technical challenges"""
    
    @hint("Be specific - 'computer is slow' vs 'Excel takes 5 minutes to open'")
    @must("specific problem you're facing")
    def problem(): "What's not working?"

    def tried(): "What you've already tried"
    
    @hint("This helps me explain things at the right level for you")
    def experience(): "Your comfort level with technology"
```

## Why Chatfield?

Traditional forms frustrate users with rigid structures and technical terminology. Chatfield's Socratic method creates intelligent conversational interfaces that:

- **Teach through dialogue** - Like a patient teacher using the Socratic method to guide understanding
- **Validate through exploration** - Help users refine their thinking through thoughtful questioning
- **Build clarity** - Each exchange helps users express their needs more precisely
- **Feel natural** - Like discussing your needs with a thoughtful mentor

## Installation

```bash
pip install .
```

For development:
```bash
pip install -e .[dev]
```

### Requirements

- Python 3.8+
- OpenAI API key (set as `OPENAI_API_KEY` environment variable)

## Quick Start

### Simplest Example

Help someone fix their computer issue:

```python
from chatfield import Dialogue

class ComputerHelp(Dialogue):
    """A Socratic dialogue to understand your computer issues"""
    
    def problem(): "What's happening with your computer?"
    def when_started(): "When did this start?"
    def tried_solutions(): "What have you tried so far?"

# Start the Socratic dialogue
help_session = ComputerHelp.gather()

# Access the insights gathered through dialogue
print(help_session.problem)
print(help_session.when_started)
```

### Adding Validation

Ensure you get useful information:

```python
from chatfield import Dialogue, must, reject, hint

class WebsiteHelp(Dialogue):
    """A Socratic exploration of your website needs"""
    
    @must("specific purpose or goal clear enough to protoype by a web developer")
    @reject("data reglation environment e.g. HIPAA, SOC2")
    def purpose(): "What will your website do?"
    
    @must("main sections identified")
    def scope(): "What pages do you need?"

    @must("at least 1")
    @must("no more than 10")
    def pages(): "Approximate page count"
    
    @hint("Shopping cart? Contact forms? Photo galleries? Calendars?")
    def technical_needs(): "Any special features?"  # Optional field
```

### Easy Field Comprehension

Use `@match` to tell Chatfield how fields do or don't match your criteria or predicate.

```python
from chatfield import Dialogue, match

class WebsiteHelp(Dialogue):
    """A Socratic exploration of your website needs"""
    
    @match.personal("is a personal project")
    @match.work("is a project for work")
    def purpose(): "What will your website do?"
    
    def scope(): "What pages do you need?"

web_help = WebsiteHelp()
print(web_help.purpose.personal) # Output: None [since chat has not begun]
print(web_help.purpose.work) # Output: None [since chat has not begun]

# ... after some chatting wherein the user says it's a small project for his dog.

print(web_help.purpose.personal) # True
print(web_help.purpose.work) # False
```

### Personalizing the Socratic Dialogue

Adapt tone and approach to your users:

```python
from chatfield import Dialogue, must, user, agent, hint

@user("Small business owner, not technical")
@user("Probably frustrated with tech complexity")
#@agent("Socratic questioner, patient and thoughtful")
@agent("Grouchy but insightful Socratic questioner")
@agent("Use analogies to explain technical concepts")
class BusinessWebsite(Dialogue):
    """A Socratic journey to discover your business's online needs"""
    
    @hint("Examples: bakery, accounting firm, yoga studio, plumbing service")
    @must("specific business type")
    @must("main customer action")
    def business(): "Tell me about your business"
    
    @hint("The words they use, not what you think sounds professional")
    @must("actual customer words, not marketing speak")
    def customers(): "How do customers describe what you do?"
    
    @hint("Facebook page? Google listing? Old website? Nothing is fine too!")
    @reject("social media links only")
    def online_presence(): "What online presence do you have now?"
```

## Intermediate Examples

### Multi-Context Guidance

```python
@user("Non-technical person setting up home office")
@user("Budget conscious, needs practical advice")
@user("Overwhelmed by options")
@agent("Patient teacher, not a salesperson")
@agent("Suggest specific products when appropriate")
@agent("Always explain the 'why' behind recommendations")
class HomeOfficeSetup(Dialogue):
    """
    Setting up a functional home office
    
    We'll figure out exactly what equipment and setup you need to be 
    productive at home, without overspending on things you don't need.
    Focus is on practical solutions that real people use, not perfect
    magazine-worthy setups.
    """
    
    @hint("Video calls? Writing? Design? Coding? Be specific about daily tasks")
    @must("specific work tasks")
    @must("hours per day")
    def work_type(): "What kind of work will you be doing?"
    
    @hint("Spare bedroom? Kitchen table? Corner of living room? Mention windows")
    @must("actual room or area")
    @must("mention lighting situation")
    def space(): "Where will you be working?"
    
    @hint("Include everything: desk, chair, computer, accessories. $500? $2000?")
    @must("specific dollar amount or range")
    @reject("no budget" or "whatever it takes")
    def budget(): "What's your total budget?"
    
    @hint("Computer? Monitor? Desk? Chair? Even if it's just a laptop")
    def current_equipment(): "What equipment do you already have?"
```

## Advanced Usage

### Dynamic Dialogues from User Data

```python
def create_tech_helper(user_profile):
    """Create a personalized dialogue based on user profile"""
    
    tech_level = user_profile.get('tech_level', 'beginner')
    industry = user_profile.get('industry', 'general')
    
    @user(f"{tech_level} user in {industry}")
    @user(f"Primary concern: {user_profile.get('pain_point')}")
    @agent(f"Adjust explanations for {tech_level} level")
    @agent("Provide industry-specific examples")
    class PersonalizedHelper(Dialogue):
        f"""
        Solving your {industry} technology challenges
        
        Based on your profile, we'll focus on practical solutions that make
        sense for your {tech_level} technical background and {industry} needs.
        """
        
        @must(f"relevant to {industry}")
        def challenge(): "What technical challenge are you facing?"
        
        @must("realistic timeline")
        def timeline(): "When do you need this solved?"
        
        def resources(): "What resources do you have available?"
    
    return PersonalizedHelper

# Use it
user = load_user_profile()
Helper = create_tech_helper(user)
session = Helper.gather()
```

### Presets for Common Scenarios

```python
from chatfield import patient_teacher, quick_diagnosis, friendly_expert, hint

# Patient teacher for complex topics
@patient_teacher
class DatabaseExplained(Dialogue):
    """Understanding databases for your business"""
    
    @hint("Customer list? Inventory? Sales records? What info matters most?")
    @must("specific business need")
    def need(): "What information do you need to track?"
    
    @hint("Spreadsheets? Paper? Sticky notes? Your current system")
    @must("current method mentioned")
    def current(): "How do you track this now?"

# Quick diagnosis for urgent issues  
@quick_diagnosis
class EmailNotWorking(Dialogue):
    """Let's get your email working again"""
    
    @hint("Error messages? Can't send? Can't receive? Wrong password?")
    @must("specific error or symptom")
    def issue(): "What exactly is happening?"
    
    @hint("Gmail? Outlook? Yahoo? Company email?")
    @must("email provider")
    def provider(): "Who's your email provider?"

# Friendly expert for ongoing help
@friendly_expert  
class DigitalTransformation(Dialogue):
    """Modernizing your business processes"""
    
    @hint("Invoice generation? Inventory tracking? Customer communication?")
    @must("specific process or workflow")
    def process(): "Which process should we tackle first?"
```

### Validation Rules as Context

```python
@user("Non-technical founder needing a website")
@agent("Guide away from over-engineering")
class WebsiteRequirements(Dialogue):
    """
    Planning a website that actually gets built
    
    We'll focus on what you need to launch, not every possible feature.
    A simple site that exists beats a perfect site that doesn't.
    """
    
    @hint("Sell products? Generate leads? Share information? Book appointments?")
    @must("specific business goal implementable by a developer")
    @must("how website helps achieve it")
    @reject("vague or unclear")
    def purpose(): "What should your website accomplish?"
    
    @hint("What do they say when they call? How do they find you now?")
    @must("actual phrases customers use")
    @reject("marketing buzzwords")
    @reject("we do everything")
    def customer_message(): "What do customers need to know?"
    
    @must("specific number or range")
    @hint("$500 for DIY? $5,000 for professional? Include ongoing costs")
    @hint("The most cheap is about $500 USD")
    @reject("as cheap as possible")
    @reject("money is no object")
    def build_budget(): "Website budget for initial build"
    
    @must("specific number or range per a specific time frame (e.g. X USD per month)")
    @hint("$500 for DIY? $5,000 for professional? Include ongoing costs")
    @hint("As cheap as possible is at least $100 per month")
    @must("specific number or range for a specific time duration")
    @reject("as cheap as possible")
    @reject("money is no object")
    def maintenance_budget(): "Website budget for long-term maintenance"
    
    # These fields are optional because they have no @must decorator.
    @hint("Links to sites you like the look or feel of")
    def examples(): "Websites you like"
    
    @hint("Launch date? Important deadline? Or just 'soon'?")
    def timeline(): "When do you need this?"
```

## Best Practices

### 1. Write docstrings that set context

Describe the data. Do not write the prompt or Agent script.

```python
class TechHelp(Dialogue):
    """
    Tech support request
    
    One specific problem for one specific user. The problem
    should be about their technology.
    """
```

### 2. Use `@user` and `@agent` to shape the conversation

`@agent` influences the agent's behavior, tone of voice, etc.

`@user` influences the agent's understanding of the users's situation.

```python
@user("Busy parent working from home")
@user("Limited tech budget")
@agent("Empathetic problem-solver")
@agent("Suggest free/cheap solutions first")
```

### 4. Use field descriptions to describe the data, not a prompt

```python

# Good
def problem(): "User's primary problem"
def impact(): "Specific, ideally quantifiable, cost of this problem to the user"

# Bad  
def issue_description(): "Tell me what your problem is?"
```

## API Reference

### Core Classes

- `Dialogue` - Base class for creating Socratic dialogue interfaces (inherit from this)

### Decorators

- `@user(context)` - Information about who you're helping
- `@agent(behavior)` - How the agent should behave
- `@hint(tooltip)` - Helpful context shown when users need clarification
- `@must(rule)` - What the answer must include
- `@reject(rule)` - What to avoid in answers
- `@match.<name>(criteria)` - Define custom match criteria for field comprehension

### Presets

- `@patient_teacher` - For explaining complex topics
- `@quick_diagnosis` - For urgent problem-solving  
- `@friendly_expert` - For ongoing consultation

### Advanced Configuration

Chatfield uses LangGraph agents to orchestrate Socratic dialogues:

```python
# Pass custom LLM settings for your Socratic dialogue
result = MySocraticDialogue.gather(
    model="gpt-4",
    temperature=0.5,
    max_retries=5
)
```

Features:
- Stateful Socratic dialogue management with LangGraph
- Thoughtful retry logic that guides users to better answers
- Natural conversational flow following Socratic principles
- Streaming support (coming soon)
- Multi-agent capabilities (coming soon)

## License

Apache 2.0 - see LICENSE file for details.

# Whiteboard - Random development notes

If you can hot-swap a data model mid-conversation, it's easy to be dynamic:

```py
class TechSupport(Gatherer):
    def problem(): "your computer's problem"
    def age(): "age of your computer"

support = TechSupport.gather()
# ...
age_in_years = some_function()

if age_in_years > 3:
    class NewTechSupport(TechSupport):
        def dusted(): "Have you dusted it recently?"
    support = NewTechSupport()
```

Or maybe

```py
while True:
    support = TechSupport.gather()
    if support.__done:
        break
```

Features
- Pre-populate values based on ongoing conversation and/or propose some recommended possible answers to upcoming questions
- Must have some kind of builder API to build these objects during runtime, not in source code.