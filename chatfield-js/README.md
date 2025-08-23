# Chatfield JS/TS

Transform rigid forms into natural conversations with LLMs - TypeScript/JavaScript implementation.

## Short term plan

1. Use `npm run min` and get two things working
    1. The interrupt system to get user input
    2. The tool calling
2. Go back to defining details: alice ID, alice traits, bob ID, bob traits, and especially the decorators and the casts.

## Installation

```bash
npm install @chatfield/core
```

## Quick Start

```typescript
import { chatfield } from '@chatfield/core'

const BusinessPlan = chatfield()
  .field('concept', 'Your business concept')
  .must('include timeline')
  .hint('Be specific about milestones')
  .field('market', 'Target market description')
  .user('startup founder')
  .agent('patient advisor')
  .build()

const result = await BusinessPlan.gather()
console.log(result.concept, result.market)
```

## Development

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Run tests
npm test

# Watch mode
npm run dev
```

## API Reference

Coming soon...

## License

Apache-2.0