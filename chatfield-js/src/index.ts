/**
 * Chatfield: Conversational data gathering powered by LLMs
 * TypeScript/JavaScript implementation
 */

// Primary decorator API
export { gather, field, must, reject, hint, user, agent } from './decorators'
export type { GathererClass } from './decorators'

// Core classes and types
export { FieldMeta, GathererMeta } from './core/metadata'
export { Gatherer, GathererInstance } from './core/gatherer'
export { Conversation } from './core/conversation'
export { LLMBackend, OpenAIBackend, MockLLMBackend } from './backends/llm-backend'

// Alternative builder API (secondary)
export { chatfield } from './builders/gatherer-builder'
export { createGatherer, schemaPresets } from './builders/schema-builder'

// Note: React integration available but not exported by default
// Import from '@chatfield/core/integrations/react' directly if needed

// Re-export types
export type {
  FieldMetaOptions,
  GathererSchema,
  ConversationMessage,
  ValidationResult,
  CollectedData,
  GathererOptions
} from './core/types'