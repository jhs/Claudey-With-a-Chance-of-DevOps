/**
 * Fluent builder API for creating gatherers
 */

import { GathererMeta, FieldMeta } from '../core/metadata'
import { Gatherer } from '../core/gatherer'
import { GathererOptions } from '../core/types'

/**
 * Field builder for configuring individual fields
 */
export class FieldBuilder {
  private fieldMeta: FieldMeta
  private parentBuilder: GathererBuilder

  constructor(fieldMeta: FieldMeta, parentBuilder: GathererBuilder) {
    this.fieldMeta = fieldMeta
    this.parentBuilder = parentBuilder
  }

  /**
   * Add a validation requirement
   */
  must(rule: string): FieldBuilder {
    this.fieldMeta.addMustRule(rule)
    return this
  }

  /**
   * Add a validation rejection rule
   */
  reject(rule: string): FieldBuilder {
    this.fieldMeta.addRejectRule(rule)
    return this
  }

  /**
   * Add helpful context for users
   */
  hint(tooltip: string): FieldBuilder {
    this.fieldMeta.setHint(tooltip)
    return this
  }

  /**
   * Set conditional visibility logic
   */
  when(condition: (data: Record<string, string>) => boolean): FieldBuilder {
    this.fieldMeta.setWhenCondition(condition)
    return this
  }

  /**
   * Add another field
   */
  field(name: string, description: string): FieldBuilder {
    return this.parentBuilder.field(name, description)
  }

  /**
   * Add user context
   */
  user(context: string): GathererBuilder {
    return this.parentBuilder.user(context)
  }

  /**
   * Add agent behavior context
   */
  agent(behavior: string): GathererBuilder {
    return this.parentBuilder.agent(behavior)
  }

  /**
   * Set docstring
   */
  docstring(doc: string): GathererBuilder {
    return this.parentBuilder.docstring(doc)
  }

  /**
   * Build the final gatherer
   */
  build(options?: GathererOptions): Gatherer {
    return this.parentBuilder.build(options)
  }
}

/**
 * Main builder for creating gatherers with fluent API
 */
export class GathererBuilder {
  private meta: GathererMeta

  constructor() {
    this.meta = new GathererMeta()
  }

  /**
   * Add a field
   */
  field(name: string, description: string): FieldBuilder {
    const fieldMeta = this.meta.addField(name, description)
    return new FieldBuilder(fieldMeta, this)
  }

  /**
   * Add user context information
   */
  user(context: string): GathererBuilder {
    this.meta.addUserContext(context)
    return this
  }

  /**
   * Add agent behavior context
   */
  agent(behavior: string): GathererBuilder {
    this.meta.addAgentContext(behavior)
    return this
  }

  /**
   * Set the main description/docstring
   */
  docstring(doc: string): GathererBuilder {
    this.meta.setDocstring(doc)
    return this
  }

  /**
   * Build the final gatherer
   */
  build(options?: GathererOptions): Gatherer {
    return new Gatherer(this.meta.clone(), options)
  }

  /**
   * Get the metadata (for inspection/debugging)
   */
  getMeta(): GathererMeta {
    return this.meta.clone()
  }
}

/**
 * Create a new gatherer builder
 */
export function chatfield(): GathererBuilder {
  return new GathererBuilder()
}

/**
 * Convenience function to create a simple gatherer with multiple fields
 */
export function simpleGatherer(fields: Record<string, string>, options?: {
  userContext?: string[]
  agentContext?: string[]
  docstring?: string
}): Gatherer {
  const builder = chatfield()

  // Add docstring
  if (options?.docstring) {
    builder.docstring(options.docstring)
  }

  // Add user context
  if (options?.userContext) {
    options.userContext.forEach(context => builder.user(context))
  }

  // Add agent context
  if (options?.agentContext) {
    options.agentContext.forEach(behavior => builder.agent(behavior))
  }

  // Add fields
  let currentBuilder: FieldBuilder | GathererBuilder = builder
  const fieldEntries = Object.entries(fields)
  
  for (let i = 0; i < fieldEntries.length; i++) {
    const [name, description] = fieldEntries[i]
    currentBuilder = currentBuilder.field(name, description)
  }

  return currentBuilder.build()
}

/**
 * Quick preset for patient data gathering
 */
export function patientGatherer(): GathererBuilder {
  return chatfield()
    .agent('Be patient and thorough')
    .agent('Ask follow-up questions when answers seem incomplete')
    .agent('Provide helpful examples when users seem confused')
}

/**
 * Quick preset for rapid data gathering
 */
export function quickGatherer(): GathererBuilder {
  return chatfield()
    .agent('Be concise and efficient')
    .agent('Accept brief answers when they meet requirements')
    .agent('Move quickly through fields')
}

/**
 * Quick preset for expert consultation
 */
export function expertGatherer(): GathererBuilder {
  return chatfield()
    .agent('Assume the user has domain expertise')
    .agent('Ask detailed technical questions')
    .agent('Expect comprehensive, specific answers')
}