/**
 * LLM backend integrations for Chatfield
 */

import { GathererMeta, FieldMeta } from '../core/metadata'
import { ConversationMessage } from '../core/types'

/**
 * Abstract base class for LLM providers
 */
export abstract class LLMBackend {
  /**
   * Build the system and user prompts for conversation
   */
  abstract createConversationPrompt(
    meta: GathererMeta,
    field: FieldMeta,
    history: ConversationMessage[]
  ): string

  /**
   * Get LLM response to a prompt
   */
  abstract getResponse(prompt: string): Promise<string>

  /**
   * Validate a user response using the LLM
   */
  abstract validateResponse(validationPrompt: string): Promise<string>
}

/**
 * OpenAI GPT implementation
 */
export class OpenAIBackend extends LLMBackend {
  private client: any // OpenAI client
  private model: string
  private apiKey: string

  constructor(options: {
    model?: string
    apiKey?: string
  } = {}) {
    super()
    
    this.model = options.model || 'gpt-4'
    this.apiKey = options.apiKey || (typeof process !== 'undefined' ? process.env.OPENAI_API_KEY : undefined) || ''
    
    if (!this.apiKey) {
      throw new Error(
        'OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass apiKey parameter.'
      )
    }

    // Lazy load OpenAI to avoid import errors if not installed
    this.initializeClient()
  }

  private async initializeClient(): Promise<void> {
    try {
      const { OpenAI } = await import('openai')
      this.client = new OpenAI({
        apiKey: this.apiKey
      })
    } catch (error) {
      throw new Error(
        'OpenAI package not available. Install with: npm install openai'
      )
    }
  }

  /**
   * Build the conversation prompt with full context
   */
  createConversationPrompt(
    meta: GathererMeta,
    field: FieldMeta,
    history: ConversationMessage[]
  ): string {
    // Build system context
    const contextParts: string[] = []
    
    // Add main context from docstring
    if (meta.docstring) {
      contextParts.push(`Context: ${meta.docstring}`)
    }
    
    // Add user context
    if (meta.userContext.length > 0) {
      const userInfo = meta.userContext.join(' ')
      contextParts.push(`User: ${userInfo}`)
    }
    
    // Add agent behavior
    if (meta.agentContext.length > 0) {
      const agentInfo = meta.agentContext.join(' ')
      contextParts.push(`Behavior: ${agentInfo}`)
    }
    
    // Add field-specific information
    const fieldInfo: string[] = [`Current question: ${field.description}`]
    
    if (field.hint) {
      fieldInfo.push(`Helpful context: ${field.hint}`)
    }
    
    if (field.mustRules.length > 0) {
      fieldInfo.push(`Answer must include: ${field.mustRules.join(', ')}`)
    }
    
    if (field.rejectRules.length > 0) {
      fieldInfo.push(`Answer should avoid: ${field.rejectRules.join(', ')}`)
    }
    
    contextParts.push(...fieldInfo)
    
    // Add conversation history
    if (history.length > 0) {
      const historyText = 'Previous conversation:\n'
      const recentHistory = history.slice(-3) // Last 3 exchanges
        .map(msg => {
          const content = msg.content.length > 100 
            ? `${msg.content.substring(0, 100)}...` 
            : msg.content
          return `- ${msg.role}: ${content}`
        })
        .join('\n')
      
      contextParts.push(historyText + recentHistory)
    }
    
    return contextParts.join('\n\n')
  }

  /**
   * Get response from OpenAI
   */
  async getResponse(prompt: string): Promise<string> {
    if (!this.client) {
      await this.initializeClient()
    }

    try {
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: [
          {
            role: 'system',
            content: 'You are a helpful assistant conducting a conversational data gathering session. Ask clear questions and guide users to provide useful information.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 500,
        temperature: 0.7
      })

      return response.choices[0]?.message?.content?.trim() || 'No response generated'
    } catch (error: any) {
      throw new Error(`OpenAI API error: ${error.message}`)
    }
  }

  /**
   * Validate a response using OpenAI
   */
  async validateResponse(validationPrompt: string): Promise<string> {
    if (!this.client) {
      await this.initializeClient()
    }

    try {
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: [
          {
            role: 'system',
            content: (
              'You are a validator. Check if user responses meet specified requirements. ' +
              'If valid, respond "VALID". If not valid, explain what\'s missing in a helpful way.'
            )
          },
          {
            role: 'user',
            content: validationPrompt
          }
        ],
        max_tokens: 200,
        temperature: 0.1 // Low temperature for consistent validation
      })

      return response.choices[0]?.message?.content?.trim() || 'VALID'
    } catch (error: any) {
      throw new Error(`Validation error: ${error.message}`)
    }
  }
}

/**
 * Mock LLM backend for testing
 */
export class MockLLMBackend extends LLMBackend {
  private responses: string[]
  private validationResponses: string[]
  private callCount: number
  private validationCallCount: number

  constructor() {
    super()
    this.responses = []
    this.validationResponses = []
    this.callCount = 0
    this.validationCallCount = 0
  }

  /**
   * Add a mock response
   */
  addResponse(response: string): void {
    this.responses.push(response)
  }

  /**
   * Add a mock validation response
   */
  addValidationResponse(response: string): void {
    this.validationResponses.push(response)
  }

  /**
   * Reset mock state
   */
  reset(): void {
    this.responses = []
    this.validationResponses = []
    this.callCount = 0
    this.validationCallCount = 0
  }

  /**
   * Build conversation prompt (mock version)
   */
  createConversationPrompt(
    meta: GathererMeta,
    field: FieldMeta,
    history: ConversationMessage[]
  ): string {
    const parts: string[] = []
    
    if (meta.docstring) {
      parts.push(`Context: ${meta.docstring}`)
    }
    
    parts.push(`Field: ${field.description}`)
    
    if (field.hint) {
      parts.push(`Hint: ${field.hint}`)
    }
    
    return parts.join('\n')
  }

  /**
   * Return a mock response
   */
  async getResponse(prompt: string): Promise<string> {
    if (this.callCount < this.responses.length) {
      const response = this.responses[this.callCount]
      this.callCount++
      return response
    }
    return 'Mock response'
  }

  /**
   * Return a mock validation response
   */
  async validateResponse(validationPrompt: string): Promise<string> {
    if (this.validationCallCount < this.validationResponses.length) {
      const response = this.validationResponses[this.validationCallCount]
      this.validationCallCount++
      return response
    }
    return 'VALID'
  }
}

/**
 * Console-based backend for development/testing
 */
export class ConsoleLLMBackend extends LLMBackend {
  createConversationPrompt(
    meta: GathererMeta,
    field: FieldMeta,
    history: ConversationMessage[]
  ): string {
    return `Field: ${field.description}${field.hint ? `\nHint: ${field.hint}` : ''}`
  }

  async getResponse(prompt: string): Promise<string> {
    console.log('\n--- LLM Prompt ---')
    console.log(prompt)
    console.log('--- End Prompt ---\n')
    
    // For development, return a placeholder
    return 'Console backend response - integrate with actual LLM'
  }

  async validateResponse(validationPrompt: string): Promise<string> {
    console.log('\n--- Validation Prompt ---')
    console.log(validationPrompt)
    console.log('--- End Validation ---\n')
    
    // For development, assume valid
    return 'VALID'
  }
}