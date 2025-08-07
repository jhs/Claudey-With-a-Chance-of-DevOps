/**
 * Core gatherer classes for Chatfield
 */

import { GathererMeta } from './metadata'
import { Conversation } from './conversation'
import { CollectedData, GathererOptions } from './types'

/**
 * Instance created after completing a conversation
 */
export class GathererInstance {
  private _meta: GathererMeta
  private _data: CollectedData

  constructor(meta: GathererMeta, collectedData: CollectedData) {
    this._meta = meta
    this._data = { ...collectedData }
  }

  /**
   * Get field value with optional default
   */
  get(fieldName: string, defaultValue?: string): string | undefined {
    return this._data[fieldName] ?? defaultValue
  }

  /**
   * Get all collected data as a dictionary
   */
  getData(): CollectedData {
    return { ...this._data }
  }

  /**
   * Check if a field was collected
   */
  has(fieldName: string): boolean {
    return fieldName in this._data
  }

  /**
   * Get field names that were collected
   */
  getCollectedFields(): string[] {
    return Object.keys(this._data)
  }

  /**
   * Get metadata for reference
   */
  getMeta(): GathererMeta {
    return this._meta
  }

  /**
   * String representation of collected data
   */
  toString(): string {
    const fields = Object.entries(this._data)
      .map(([k, v]) => {
        const displayValue = v.length > 50 ? `${v.substring(0, 50)}...` : v
        return `${k}='${displayValue}'`
      })
      .join(', ')
    
    return `GathererInstance(${fields})`
  }

  /**
   * Convert to JSON
   */
  toJSON(): { meta: any, data: CollectedData } {
    return {
      meta: {
        userContext: this._meta.userContext,
        agentContext: this._meta.agentContext,
        docstring: this._meta.docstring,
        fields: Array.from(this._meta.fields.entries()).map(([name, field]) => ({
          name,
          description: field.description,
          mustRules: field.mustRules,
          rejectRules: field.rejectRules,
          hint: field.hint
        }))
      },
      data: this._data
    }
  }
}

/**
 * Main gatherer class that conducts conversations
 */
export class Gatherer {
  private meta: GathererMeta
  private options: GathererOptions

  constructor(meta: GathererMeta, options: GathererOptions = {}) {
    this.meta = meta
    this.options = {
      maxRetryAttempts: 3,
      ...options
    }
  }

  /**
   * Conduct a conversation to gather data
   */
  async gather(): Promise<GathererInstance> {
    const conversation = new Conversation(this.meta, {
      maxRetryAttempts: this.options.maxRetryAttempts,
      llmBackend: this.options.llmBackend
    })

    const collectedData = await conversation.conductConversation()
    return new GathererInstance(this.meta, collectedData)
  }

  /**
   * Get the metadata for this gatherer
   */
  getMeta(): GathererMeta {
    return this.meta
  }

  /**
   * Create a copy of this gatherer with modified options
   */
  withOptions(newOptions: Partial<GathererOptions>): Gatherer {
    return new Gatherer(this.meta, { ...this.options, ...newOptions })
  }

  /**
   * Get a preview of what fields will be collected
   */
  getFieldPreview(): Array<{
    name: string
    description: string
    hasValidation: boolean
    hint?: string
  }> {
    return this.meta.getFields().map(field => ({
      name: field.name,
      description: field.description,
      hasValidation: field.hasValidationRules(),
      hint: field.hint
    }))
  }
}