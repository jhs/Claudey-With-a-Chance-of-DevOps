/**
 * Core type definitions for Chatfield
 */

export interface FieldMetaOptions {
  name: string
  description: string
  mustRules?: string[]
  rejectRules?: string[]
  hint?: string
  when?: (data: Record<string, string>) => boolean
}

export interface GathererSchema {
  fields: Record<string, {
    description: string
    must?: string[]
    reject?: string[]
    hint?: string
    when?: (data: Record<string, string>) => boolean
  }>
  userContext?: string[]
  agentContext?: string[]
  docstring?: string
}

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: Date
}

export interface ValidationResult {
  isValid: boolean
  feedback: string
}

export interface GathererOptions {
  maxRetryAttempts?: number
  llmBackend?: any // Will be properly typed when LLMBackend is implemented
}

export interface CollectedData {
  [fieldName: string]: string
}