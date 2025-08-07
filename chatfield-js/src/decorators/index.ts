/**
 * TypeScript decorators for Chatfield - mirroring Python implementation
 */

import 'reflect-metadata'
import { GathererMeta, FieldMeta } from '../core/metadata'
import { Gatherer, GathererInstance } from '../core/gatherer'
import { Conversation } from '../core/conversation'

// Metadata keys for storing decorator information
const CHATFIELD_FIELDS = Symbol('chatfield:fields')
const CHATFIELD_USER_CONTEXT = Symbol('chatfield:user_context')
const CHATFIELD_AGENT_CONTEXT = Symbol('chatfield:agent_context')

// Field metadata storage
interface FieldDescriptor {
  name: string
  description: string
  mustRules: string[]
  rejectRules: string[]
  hint?: string
}

/**
 * Define a field with description and optional validation
 */
export function field(description: string, options?: {
  must?: string | string[]
  reject?: string | string[]
  hint?: string
}) {
  return function (target: any, propertyKey: string) {
    if (!target[CHATFIELD_FIELDS]) {
      target[CHATFIELD_FIELDS] = new Map<string, FieldDescriptor>()
    }
    
    const mustRules = options?.must 
      ? Array.isArray(options.must) ? options.must : [options.must]
      : []
    
    const rejectRules = options?.reject
      ? Array.isArray(options.reject) ? options.reject : [options.reject] 
      : []
    
    target[CHATFIELD_FIELDS].set(propertyKey, {
      name: propertyKey,
      description,
      mustRules,
      rejectRules,
      hint: options?.hint
    })
  }
}

/**
 * Add a must rule to a field (can stack multiple)
 */
export function must(rule: string) {
  return function (target: any, propertyKey: string) {
    if (!target[CHATFIELD_FIELDS]) {
      target[CHATFIELD_FIELDS] = new Map<string, FieldDescriptor>()
    }
    
    const existing = target[CHATFIELD_FIELDS].get(propertyKey) || {
      name: propertyKey,
      description: propertyKey, // fallback
      mustRules: [],
      rejectRules: []
    }
    
    existing.mustRules.push(rule)
    target[CHATFIELD_FIELDS].set(propertyKey, existing)
  }
}

/**
 * Add a reject rule to a field (can stack multiple)
 */
export function reject(rule: string) {
  return function (target: any, propertyKey: string) {
    if (!target[CHATFIELD_FIELDS]) {
      target[CHATFIELD_FIELDS] = new Map<string, FieldDescriptor>()
    }
    
    const existing = target[CHATFIELD_FIELDS].get(propertyKey) || {
      name: propertyKey,
      description: propertyKey, // fallback
      mustRules: [],
      rejectRules: []
    }
    
    existing.rejectRules.push(rule)
    target[CHATFIELD_FIELDS].set(propertyKey, existing)
  }
}

/**
 * Add a hint to a field
 */
export function hint(tooltip: string) {
  return function (target: any, propertyKey: string) {
    if (!target[CHATFIELD_FIELDS]) {
      target[CHATFIELD_FIELDS] = new Map<string, FieldDescriptor>()
    }
    
    const existing = target[CHATFIELD_FIELDS].get(propertyKey) || {
      name: propertyKey,
      description: propertyKey, // fallback
      mustRules: [],
      rejectRules: []
    }
    
    existing.hint = tooltip
    target[CHATFIELD_FIELDS].set(propertyKey, existing)
  }
}

/**
 * Add information about the user
 */
export function user(context: string) {
  return function <T extends { new(...args: any[]): {} }>(constructor: T): T {
    if (!constructor.prototype[CHATFIELD_USER_CONTEXT]) {
      constructor.prototype[CHATFIELD_USER_CONTEXT] = []
    }
    constructor.prototype[CHATFIELD_USER_CONTEXT].push(context)
    return constructor
  }
}

/**
 * Define how the agent should behave
 */
export function agent(behavior: string) {
  return function <T extends { new(...args: any[]): {} }>(constructor: T): T {
    if (!constructor.prototype[CHATFIELD_AGENT_CONTEXT]) {
      constructor.prototype[CHATFIELD_AGENT_CONTEXT] = []
    }
    constructor.prototype[CHATFIELD_AGENT_CONTEXT].push(behavior)
    return constructor
  }
}

/**
 * Transform a class into a conversational gatherer
 */
export function gather<T extends { new(...args: any[]): {} }>(constructor: T): T & GathererClass {
  // Process the class to extract metadata
  const meta = processGathererClass(constructor)
  
  // Create new class that extends the original
  class GatheredClass extends constructor {
    static async gather(): Promise<GathererInstance> {
      const conversation = new Conversation(meta)
      const collectedData = await conversation.conductConversation()
      return new GathererInstance(meta, collectedData)
    }
    
    static _chatfield_meta = meta
    
    static getFieldPreview() {
      return meta.getFields().map(field => ({
        name: field.name,
        description: field.description,
        hasValidation: field.hasValidationRules(),
        hint: field.hint
      }))
    }
  }
  
  // Preserve the original class name
  Object.defineProperty(GatheredClass, 'name', { value: constructor.name })
  
  return GatheredClass as any
}

/**
 * Extract all metadata from a decorated class (mirrors Python implementation)
 */
function processGathererClass(cls: any): GathererMeta {
  const meta = new GathererMeta()
  
  // Get docstring from class name
  if (cls.name) {
    meta.setDocstring(`${cls.name} data gathering session`)
  }
  
  // Get user/agent context from class decorators
  const userContext = cls.prototype[CHATFIELD_USER_CONTEXT] || []
  const agentContext = cls.prototype[CHATFIELD_AGENT_CONTEXT] || []
  
  userContext.forEach((context: string) => meta.addUserContext(context))
  agentContext.forEach((behavior: string) => meta.addAgentContext(behavior))
  
  // Get field metadata from decorators
  const fields = cls.prototype[CHATFIELD_FIELDS] || new Map<string, FieldDescriptor>()
  
  // Process each field descriptor
  for (const [propertyKey, fieldDesc] of fields) {
    const fieldMeta = meta.addField(fieldDesc.name, fieldDesc.description)
    
    // Add validation rules
    fieldDesc.mustRules.forEach(rule => fieldMeta.addMustRule(rule))
    fieldDesc.rejectRules.forEach(rule => fieldMeta.addRejectRule(rule))
    
    if (fieldDesc.hint) {
      fieldMeta.setHint(fieldDesc.hint)
    }
  }
  
  return meta
}

/**
 * Helper type for gatherer classes
 */
export interface GathererClass {
  gather(): Promise<GathererInstance>
  getFieldPreview(): Array<{
    name: string
    description: string
    hasValidation: boolean
    hint?: string
  }>
  _chatfield_meta: GathererMeta
}