# CLAUDE.md - Chatfield TypeScript/JavaScript Implementation Guide

## Overview

Chatfield JS/TS is the TypeScript/JavaScript implementation of conversational data gathering powered by LLMs. It provides a clean API for transforming rigid forms into natural conversations, with full React integration and CopilotKit support.

## Project Structure

```
chatfield-js/
├── package.json         # NPM package configuration (@chatfield/core v0.1.0)
├── tsconfig.json        # TypeScript configuration
├── jest.config.js       # Jest testing configuration
├── README.md            # Package documentation
├── src/
│   ├── index.ts         # Main exports
│   ├── decorators/      # Decorator-based API (primary)
│   │   └── index.ts
│   ├── core/            # Core classes and logic
│   │   ├── types.ts     # Type definitions
│   │   ├── metadata.ts  # Metadata management
│   │   ├── gatherer.ts  # Main gatherer logic
│   │   └── conversation.ts # Conversation state
│   ├── backends/        # LLM provider integrations
│   │   └── llm-backend.ts
│   ├── builders/        # Builder pattern APIs (secondary)
│   │   ├── gatherer-builder.ts
│   │   └── schema-builder.ts
│   └── integrations/    # Framework integrations
│       ├── react.ts     # React hooks and components
│       ├── react-components.tsx # UI components
│       └── copilotkit.tsx # CopilotKit integration
├── examples/            # Usage examples
│   ├── basic-usage.ts
│   ├── decorator-usage.ts
│   ├── decorator-react.tsx
│   └── schema-based.ts
├── tests/               # Test suite
│   ├── *.test.ts        # Unit and integration tests
│   └── ...
└── dist/                # Compiled output (generated)
```

## Core Architecture

### API Design Philosophy

Chatfield JS/TS provides multiple APIs to suit different preferences:

1. **Builder API (Primary)** - Fluent, chainable interface
2. **Decorator API** - Python-style decorators (secondary)
3. **Schema API** - JSON-based configuration

### Key Components

#### 1. Core Types (`src/core/types.ts`)

```typescript
interface FieldMetaOptions {
  name: string
  description: string
  mustRules?: string[]
  rejectRules?: string[]
  hint?: string
  when?: (data: Record<string, string>) => boolean
}

interface GathererSchema {
  fields: Record<string, FieldDefinition>
  userContext?: string[]
  agentContext?: string[]
  docstring?: string
}

interface ConversationMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: Date
}
```

#### 2. Builder API (`src/builders/gatherer-builder.ts`)

Primary API for creating gatherers:

```typescript
const BusinessPlan = chatfield()
  .field('concept', 'Your business concept')
  .must('include timeline')
  .hint('Be specific about milestones')
  .field('market', 'Target market description')
  .user('startup founder')
  .agent('patient advisor')
  .build()

const result = await BusinessPlan.gather()
```

#### 3. LLM Backend Integration (`src/backends/llm-backend.ts`)

```typescript
abstract class LLMBackend {
  abstract createConversationPrompt(meta: GathererMeta, field: FieldMeta, history: ConversationMessage[]): string
  abstract getResponse(prompt: string): Promise<string>
  abstract validateResponse(field: FieldMeta, response: string): Promise<ValidationResult>
}

class OpenAIBackend extends LLMBackend {
  // OpenAI GPT integration with retry logic
}

class MockLLMBackend extends LLMBackend {
  // Testing implementation
}
```

#### 4. React Integration (`src/integrations/react.ts`)

```typescript
// React hooks for conversational forms
export const useGatherer = (gatherer: GathererClass) => {
  // Returns state, methods for React components
}

// React component wrapper
export const GathererProvider = ({ children, gatherer }) => {
  // Context provider for gatherer state
}
```

#### 5. CopilotKit Integration (`src/integrations/copilotkit.tsx`)

```typescript
export const ChatfieldSidebar = ({ gatherer, onComplete }) => {
  // CopilotKit sidebar component for conversational data gathering
}
```

## Development Workflow

### Package Configuration

- **Package Name**: `@chatfield/core`
- **Version**: `0.1.0`
- **Main Entry**: `dist/index.js`
- **Types**: `dist/index.d.ts`
- **License**: Apache-2.0

### Build System

- **TypeScript**: Compiles to `dist/` directory
- **Target**: ES2020, CommonJS modules
- **Declaration files**: Generated for TypeScript consumers

### Testing Strategy

- **Jest**: Test runner with TypeScript support
- **Coverage**: Unit tests for all core components
- **Integration tests**: Real LLM testing (marked as slow)
- **Mock implementations**: Fast unit testing

### Development Commands

```bash
# Development
npm run dev          # TypeScript watch mode
npm run build        # Compile to dist/
npm run clean        # Remove dist/

# Testing  
npm test             # Run Jest test suite
npm run test:watch   # Watch mode testing

# Quality
npm run lint         # ESLint checks
```

## Key Implementation Details

### Field Validation

Validation is handled through LLM prompts rather than code:

```typescript
const validationPrompt = `
The user provided: "${response}"

For field "${field.description}", validate that the answer:
${field.mustRules?.map(rule => `- MUST include: ${rule}`).join('\n')}
${field.rejectRules?.map(rule => `- MUST NOT include: ${rule}`).join('\n')}

Respond "VALID" if valid, otherwise explain what's wrong.
`
```

### Conversation Flow

1. Initialize gatherer with schema/configuration
2. Determine next field to collect based on conditions
3. Generate conversational prompt with context
4. Get LLM response and validate against rules
5. Handle invalid responses with helpful feedback
6. Store valid data and continue until complete

### Framework Integrations

#### React Integration

- `useGatherer` hook for state management
- `GathererProvider` for context
- Form components that render as conversations
- Real-time validation and feedback

#### CopilotKit Integration

- Sidebar component for conversational UI
- Integration with CopilotKit's chat interface
- Streaming responses and progressive disclosure
- Context-aware suggestions

## Usage Patterns

### Basic Builder Pattern

```typescript
import { chatfield } from '@chatfield/core'

const ContactForm = chatfield()
  .field('name', 'Your full name')
  .field('email', 'Your email address')
  .must('valid email format')
  .field('message', 'Your message')
  .hint('Be specific about your needs')
  .build()

const data = await ContactForm.gather()
```

### React Component

```tsx
import { useGatherer, GathererProvider } from '@chatfield/core/integrations/react'

export function ContactPage() {
  const { isComplete, data, currentQuestion } = useGatherer(ContactForm)
  
  return (
    <GathererProvider gatherer={ContactForm}>
      {isComplete ? (
        <Results data={data} />
      ) : (
        <ConversationUI question={currentQuestion} />
      )}
    </GathererProvider>
  )
}
```

### CopilotKit Integration

```tsx
import { ChatfieldSidebar } from '@chatfield/core/integrations/copilotkit'

export function App() {
  return (
    <CopilotKit>
      <div className="flex">
        <main>Your app content</main>
        <ChatfieldSidebar 
          gatherer={ContactForm}
          onComplete={(data) => console.log('Gathered:', data)}
        />
      </div>
    </CopilotKit>
  )
}
```

## Dependencies

### Runtime Dependencies
- `openai`: ^4.70.0 - OpenAI API integration
- `reflect-metadata`: ^0.1.13 - Decorator support

### Development Dependencies
- `typescript`: ^5.0.0 - TypeScript compiler
- `jest`: ^29.0.0 - Testing framework
- `@types/*`: Type definitions
- `eslint`: Code linting
- `@typescript-eslint/*`: TypeScript-specific linting

### Peer Dependencies
- `react`: ^18.0.0 || ^19.0.0 (optional) - React integration

## Testing Configuration

Jest configuration supports:
- TypeScript compilation via `ts-jest`
- ES modules and decorators
- Coverage reporting
- Async/await testing patterns
- Mock LLM backends for fast testing

## Future Enhancements

- Multiple LLM provider support (Anthropic, local models)
- Voice input/output integration
- Advanced conversation state management
- Conversation save/resume functionality
- Integration with more UI frameworks (Vue, Svelte)
- Advanced validation patterns
- Conditional field logic improvements

## Integration Notes

This package is designed to work seamlessly with:
- **React applications**: Hooks and component patterns
- **CopilotKit**: Conversational AI interfaces
- **Next.js**: Full-stack React applications
- **Node.js backends**: Server-side data gathering
- **TypeScript projects**: Full type safety and IntelliSense