/**
 * Conversation management for Chatfield
 */

import { GathererMeta, FieldMeta } from './metadata'
import { ConversationMessage, ValidationResult, CollectedData } from './types'
import { LLMBackend } from '../backends/llm-backend'

export interface ConversationOptions {
  maxRetryAttempts?: number
  llmBackend?: LLMBackend
}

/**
 * Manages the conversation state and flow
 */
export class Conversation {
  private meta: GathererMeta
  private collectedData: CollectedData
  private conversationHistory: ConversationMessage[]
  private llmBackend?: LLMBackend
  private maxRetryAttempts: number
  private onMessage?: (message: ConversationMessage) => void
  private onFieldStart?: (field: FieldMeta) => void
  private onFieldComplete?: (field: FieldMeta, value: string) => void
  private onValidationError?: (field: FieldMeta, error: string) => void

  constructor(meta: GathererMeta, options: ConversationOptions = {}) {
    this.meta = meta
    this.collectedData = {}
    this.conversationHistory = []
    this.llmBackend = options.llmBackend
    this.maxRetryAttempts = options.maxRetryAttempts ?? 3
  }

  /**
   * Set event handlers
   */
  setEventHandlers(handlers: {
    onMessage?: (message: ConversationMessage) => void
    onFieldStart?: (field: FieldMeta) => void
    onFieldComplete?: (field: FieldMeta, value: string) => void
    onValidationError?: (field: FieldMeta, error: string) => void
  }): void {
    this.onMessage = handlers.onMessage
    this.onFieldStart = handlers.onFieldStart
    this.onFieldComplete = handlers.onFieldComplete
    this.onValidationError = handlers.onValidationError
  }

  /**
   * Determine which field to ask about next
   */
  getNextField(): FieldMeta | null {
    const visibleFields = this.meta.getVisibleFields(this.collectedData)
    
    for (const field of visibleFields) {
      if (!(field.name in this.collectedData)) {
        return field
      }
    }
    
    return null
  }

  /**
   * Get list of fields that haven't been collected yet
   */
  getUncollectedFields(): string[] {
    return this.meta.getFieldNames().filter(name => !(name in this.collectedData))
  }

  /**
   * Get all visible uncollected fields
   */
  getVisibleUncollectedFields(): FieldMeta[] {
    const visibleFields = this.meta.getVisibleFields(this.collectedData)
    return visibleFields.filter(field => !(field.name in this.collectedData))
  }

  /**
   * Check if response meets field requirements
   */
  async validateResponse(field: FieldMeta, response: string): Promise<ValidationResult> {
    if (!field.hasValidationRules()) {
      return { isValid: true, feedback: '' }
    }

    if (!this.llmBackend) {
      // If no LLM backend, be permissive
      return { isValid: true, feedback: '' }
    }

    try {
      const validationPrompt = this.buildValidationPrompt(field, response)
      const validationResult = await this.llmBackend.validateResponse(validationPrompt)
      
      // Parse the LLM's validation response
      if (validationResult.trim().toUpperCase().startsWith('VALID')) {
        return { isValid: true, feedback: '' }
      } else {
        return { isValid: false, feedback: validationResult }
      }
    } catch (error) {
      console.warn('Validation error:', error)
      // If validation fails, be permissive and allow the response
      return { isValid: true, feedback: '' }
    }
  }

  /**
   * Build a prompt for the LLM to validate a response
   */
  private buildValidationPrompt(field: FieldMeta, response: string): string {
    const rules: string[] = []
    
    if (field.mustRules.length > 0) {
      rules.push(...field.mustRules.map(rule => `- MUST include: ${rule}`))
    }
    
    if (field.rejectRules.length > 0) {
      rules.push(...field.rejectRules.map(rule => `- MUST NOT include: ${rule}`))
    }
    
    const rulesText = rules.length > 0 ? rules.join('\n') : 'No specific validation rules.'
    
    return `The user provided this answer: "${response}"

For the field "${field.description}", validate that the answer follows these rules:
${rulesText}

If the answer is valid, respond with "VALID".
If the answer is not valid, explain what's missing or wrong in a helpful way that will guide the user to provide a better answer.`
  }

  /**
   * Conduct the full conversation to collect all data
   */
  async conductConversation(): Promise<CollectedData> {
    // Add opening message
    const openingMessage = this.getOpeningMessage()
    if (openingMessage) {
      const msg: ConversationMessage = {
        role: 'assistant',
        content: openingMessage,
        timestamp: new Date()
      }
      this.conversationHistory.push(msg)
      this.onMessage?.(msg)
    }

    while (true) {
      const nextField = this.getNextField()
      if (!nextField) {
        break
      }

      const success = await this.askAboutField(nextField)
      if (!success) {
        console.warn(`Failed to collect field '${nextField.name}' after maximum attempts`)
        break
      }
    }

    const totalFields = this.meta.getVisibleFields(this.collectedData).length
    const collectedFields = Object.keys(this.collectedData).length
    
    if (collectedFields === totalFields && totalFields > 0) {
      const completionMsg: ConversationMessage = {
        role: 'assistant',
        content: "Great! I've collected all the information I need.",
        timestamp: new Date()
      }
      this.conversationHistory.push(completionMsg)
      this.onMessage?.(completionMsg)
    }

    return { ...this.collectedData }
  }

  /**
   * Generate the opening message for the conversation
   */
  private getOpeningMessage(): string {
    const messages: string[] = []
    
    if (this.meta.docstring) {
      messages.push(this.meta.docstring)
    }
    
    if (messages.length === 0) {
      messages.push("Let me ask you a few questions to gather the information I need.")
    }
    
    return messages.join('\n')
  }

  /**
   * Ask about a specific field and collect the response
   */
  private async askAboutField(field: FieldMeta): Promise<boolean> {
    this.onFieldStart?.(field)
    
    let attempts = 0
    
    while (attempts < this.maxRetryAttempts) {
      try {
        // Build the prompt for this field
        const prompt = this.buildFieldPrompt(field)
        
        // Create the question message
        const questionMsg: ConversationMessage = {
          role: 'assistant',
          content: prompt,
          timestamp: new Date()
        }
        this.conversationHistory.push(questionMsg)
        this.onMessage?.(questionMsg)

        // In a real implementation, this would wait for user input
        // For now, we'll need to integrate with the UI layer
        // This method should be called by the UI when user provides input
        
        return true // Placeholder - actual implementation depends on UI integration
        
      } catch (error) {
        console.error('Error during field collection:', error)
        attempts++
      }
    }
    
    return false
  }

  /**
   * Process user response for the current field
   */
  async processUserResponse(response: string): Promise<{ 
    success: boolean
    needsRetry?: boolean
    feedback?: string 
  }> {
    const currentField = this.getNextField()
    if (!currentField) {
      return { success: false, feedback: 'No active field to collect' }
    }

    if (!response.trim()) {
      return { 
        success: false, 
        needsRetry: true, 
        feedback: 'Please provide an answer.' 
      }
    }

    // Add user message to history
    const userMsg: ConversationMessage = {
      role: 'user',
      content: response,
      timestamp: new Date()
    }
    this.conversationHistory.push(userMsg)
    this.onMessage?.(userMsg)

    // Validate the response
    const validation = await this.validateResponse(currentField, response)
    
    if (validation.isValid) {
      this.collectedData[currentField.name] = response
      this.onFieldComplete?.(currentField, response)
      return { success: true }
    } else {
      this.onValidationError?.(currentField, validation.feedback)
      return { 
        success: false, 
        needsRetry: true, 
        feedback: validation.feedback 
      }
    }
  }

  /**
   * Build a conversational prompt for asking about a field
   */
  private buildFieldPrompt(field: FieldMeta): string {
    let prompt = field.description
    
    // Make it conversational if it doesn't end with a question mark
    if (!prompt.trim().endsWith('?')) {
      prompt += '?'
    }
    
    // Add context about what we've already collected
    const collectedEntries = Object.entries(this.collectedData)
    if (collectedEntries.length > 0) {
      const contextItems = collectedEntries
        .slice(-2) // Last 2 items
        .map(([fieldName, value]) => {
          const shortValue = value.length > 30 ? `${value.substring(0, 30)}...` : value
          return `${fieldName}: ${shortValue}`
        })
      
      if (contextItems.length > 0) {
        prompt = `Based on what you've told me (${contextItems.join(', ')}), ${prompt.toLowerCase()}`
      }
    }
    
    // Add hint if available
    if (field.hint) {
      prompt += `\n\n💡 ${field.hint}`
    }
    
    return prompt
  }

  /**
   * Get a summary of the conversation so far
   */
  getConversationSummary(): string {
    if (Object.keys(this.collectedData).length === 0) {
      return "No data collected yet."
    }
    
    const summaryItems = Object.entries(this.collectedData).map(([fieldName, value]) => {
      const field = this.meta.getField(fieldName)
      const fieldDesc = field ? field.description : fieldName
      const shortValue = value.length > 50 ? `${value.substring(0, 50)}...` : value
      return `- ${fieldDesc}: ${shortValue}`
    })
    
    return `Collected so far:\n${summaryItems.join('\n')}`
  }

  /**
   * Get the conversation history
   */
  getHistory(): ConversationMessage[] {
    return [...this.conversationHistory]
  }

  /**
   * Get current collected data
   */
  getCurrentData(): CollectedData {
    return { ...this.collectedData }
  }

  /**
   * Reset the conversation
   */
  reset(): void {
    this.collectedData = {}
    this.conversationHistory = []
  }
}