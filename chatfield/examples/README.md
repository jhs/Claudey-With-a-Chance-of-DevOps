# Chatfield Examples

This directory contains example implementations demonstrating various features of the Chatfield conversational data gathering system.

## Running Examples

All examples can be run in two modes:

1. **Interactive Mode** - Have a real conversation with the AI interviewer
2. **Automated Demo Mode** - Watch a pre-scripted conversation with sample inputs

### Prerequisites

Before running any example, ensure you have:

1. Set up your OpenAI API key in a `.env` file:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

2. Installed the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running an Example

```bash
# Interactive mode
python examples/restaurant_order.py

# Automated demo mode
python examples/restaurant_order.py --auto
```

## Available Examples

### 1. Restaurant Order (`restaurant_order.py`)

A fun example of taking a restaurant order with dynamic adaptation based on dietary preferences.

**Features demonstrated:**
- Dynamic trait activation (detects and adapts to vegan preferences)
- Selection fields with multiple choices
- Confidential fields (tracks if customer is in a hurry)
- Conclusion fields (assesses politeness level)
- Alice personality traits (server speaks in limericks)

**Try saying:** "I'm vegan" to see how the conversation adapts!

### 2. Job Interview (`job_interview.py`)

A professional job interview for a software engineer position.

**Features demonstrated:**
- Possible traits that activate based on conversation content
- Multiple confidential fields (mentoring, leadership)
- Conclusion fields for final assessments
- Field validation with `@must` decorator
- Professional conversation flow

**Interesting aspects:**
- Detects career changers automatically
- Tracks mentoring and leadership qualities silently
- Provides comprehensive assessment summary

### 3. Favorite Number (`favorite_number.py`)

An extensive demonstration of Chatfield's transformation system.

**Features demonstrated:**
- Basic transformations (`@as_int`, `@as_float`, `@as_percent`)
- Language translations (`@as_lang.fr`, `@as_lang.ja`, etc.)
- Boolean properties with sub-attributes (`@as_bool.prime`)
- Set transformations (`@as_set.factors`)
- All cardinality decorators:
  - `@as_one` - exactly one choice
  - `@as_maybe` - zero or one choice
  - `@as_multi` - one or more choices
  - `@as_any` - zero or more choices

**Try asking about:** The number 42 to see all transformations!

### 4. Tech Work Request (`tech_request.py`)

A realistic business conversation between a Product Owner and Technology Consultant.

**Features demonstrated:**
- Complex role definitions with multiple traits
- Multiple validation rules (`@must`, `@reject`, `@hint`)
- Integer transformations for numeric fields
- Real-world project requirement gathering
- Professional consulting conversation flow

**Useful for:** Understanding how Chatfield handles business requirements gathering.

## Example Output

When you run an example in automated mode, you'll see output like:

```
Running automated demo (thread: tech-demo-12345)
============================================================

Consultant: Hello! I'm here to help you with your technical project. Let's start 
by giving it a name. What should we call this project?

Product Owner: CustomerConnect Portal

Consultant: Great name! Now, could you tell me what you'd like to build with 
CustomerConnect Portal? Please be specific about the functionality you need.

Product Owner: We need a customer self-service portal where they can view their 
orders, download invoices, and submit support tickets...

[conversation continues...]

============================================================
PROJECT REQUIREMENTS SUMMARY
------------------------------------------------------------
Project Name: CustomerConnect Portal
Scope of Work: Customer self-service portal with order viewing...
[summary continues...]
```

## Creating Your Own Examples

To create a new example:

1. Copy one of the existing examples as a template
2. Define your Interview structure using the builder pattern
3. Implement both interactive and automated modes
4. Add prefab inputs that demonstrate your features
5. Create a display function to show results

## Tips for Best Results

1. **Be specific** - The AI responds better to specific requirements
2. **Use hints** - Guide users toward the type of answer you need
3. **Test edge cases** - Try unexpected inputs in interactive mode
4. **Watch traits** - See how possible traits activate based on conversation
5. **Check transformations** - Explore the rich transformation system

## Troubleshooting

If you encounter issues:

1. **No API Key**: Ensure `OPENAI_API_KEY` is set in your `.env` file
2. **Import Errors**: Run from the chatfield root directory
3. **Conversation Stuck**: Use Ctrl+C to exit and try again
4. **Unexpected Behavior**: Check the LangSmith trace URL printed at startup

## Advanced Usage

For debugging and development:

- The thread ID printed at startup can be used to find traces in LangSmith
- Set `LANGCHAIN_TRACING_V2=true` in your `.env` for detailed tracing
- Modify prefab inputs to test different conversation flows
- Use the mock interviewer pattern from tests for unit testing