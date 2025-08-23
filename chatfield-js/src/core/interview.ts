/**
 * Interview base class for TypeScript implementation
 * Mirrors the Python Interview class functionality
 */

import 'reflect-metadata'

export interface FieldChatfield {
  desc?: string
  specs?: {
    must?: string[]
    reject?: string[]
    hint?: string[]
  }
  casts?: Record<string, {
    type: string
    prompt: string
    choices?: string[]
    null?: boolean
    multi?: boolean
  }>
  value?: any
}

export interface RoleInfo {
  type?: string
  traits: string[]
}

/**
 * FieldProxy - String subclass that provides transformation access
 */
export class FieldProxy extends String {
  private _chatfield: FieldChatfield

  constructor(value: string, chatfield: FieldChatfield) {
    super(value)
    this._chatfield = chatfield
  }

  // Allow access to transformations like field.as_int, field.as_lang_fr, etc.
  [key: string]: any

  // Override property access to return transformation values
  get as_int(): number | undefined {
    return this._chatfield.value?.as_int
  }

  get as_float(): number | undefined {
    return this._chatfield.value?.as_float
  }

  get as_bool(): boolean | undefined {
    return this._chatfield.value?.as_bool
  }

  get as_list(): any[] | undefined {
    return this._chatfield.value?.as_list
  }

  get as_set(): Set<any> | undefined {
    const list = this._chatfield.value?.as_set
    return list ? new Set(list) : undefined
  }

  get as_dict(): Record<string, any> | undefined {
    return this._chatfield.value?.as_dict
  }

  get as_percent(): number | undefined {
    return this._chatfield.value?.as_percent
  }

  // Dynamic property getter for language and other transformations
  getTransformation(key: string): any {
    return this._chatfield.value?.[key]
  }
}

/**
 * Base Interview class
 */
export class Interview {
  _chatfield: {
    type: string
    desc?: string
    roles: {
      alice: RoleInfo
      bob: RoleInfo
    }
    fields: Record<string, FieldChatfield>
  }

  constructor() {
    const className = this.constructor.name
    const classDesc = (this.constructor as any).description || className
    const ctor = this.constructor as any

    this._chatfield = {
      type: className,
      desc: classDesc,
      roles: {
        alice: { 
          type: ctor._alice_role || undefined, 
          traits: ctor._alice_traits || [] 
        },
        bob: { 
          type: ctor._bob_role || undefined, 
          traits: ctor._bob_traits || [] 
        }
      },
      fields: {}
    }

    // Discover fields from class methods
    this._discoverFields()
  }

  private _discoverFields() {
    const proto = Object.getPrototypeOf(this)
    const propertyNames = Object.getOwnPropertyNames(proto)

    for (const name of propertyNames) {
      if (name.startsWith('_') || name === 'constructor') continue

      const descriptor = Object.getOwnPropertyDescriptor(proto, name)
      if (descriptor && typeof descriptor.value === 'function') {
        // Get metadata attached by decorators
        const metadata = Reflect.getMetadata('chatfield', proto, name) || {}
        
        this._chatfield.fields[name] = {
          desc: metadata.desc || descriptor.value.name,
          specs: metadata.specs || {},
          casts: metadata.casts || {},
          value: null
        }
      }
    }
  }

  _name(): string {
    return this._chatfield.type
  }

  _fields(): string[] {
    return Object.keys(this._chatfield.fields)
  }

  _alice_role_name(): string {
    return this._chatfield.roles.alice.type || 'Alice'
  }

  _bob_role_name(): string {
    return this._chatfield.roles.bob.type || 'Bob'
  }

  _alice_role(): RoleInfo {
    return this._chatfield.roles.alice
  }

  _bob_role(): RoleInfo {
    return this._chatfield.roles.bob
  }

  get _done(): boolean {
    // Check if all required fields have values
    for (const field of Object.values(this._chatfield.fields)) {
      if (!field.value) {
        return false
      }
    }
    return true
  }

  _get_chat_field(name: string): FieldChatfield {
    return this._chatfield.fields[name] || { value: null }
  }

  _copy_from(other: Interview): void {
    // Deep copy chatfield data from another interview
    this._chatfield = JSON.parse(JSON.stringify(other._chatfield))
  }

  _pretty(): string {
    const lines: string[] = []
    lines.push(`${this._name()}:`)
    
    for (const [name, field] of Object.entries(this._chatfield.fields)) {
      const value = field.value?.value || 'None'
      lines.push(`  ${name}: ${value}`)
      
      // Show transformations if present
      if (field.value) {
        for (const [key, val] of Object.entries(field.value)) {
          if (key !== 'value' && key !== 'context' && key !== 'as_quote') {
            lines.push(`    ${key}: ${val}`)
          }
        }
      }
    }
    
    return lines.join('\n')
  }

  model_dump(): any {
    return JSON.parse(JSON.stringify(this._chatfield))
  }

  // Dynamic property access for fields
  [key: string]: any
}

// Decorator functions

/**
 * Alice decorator - sets the interviewer role
 */
export function alice(role: string) {
  return function<T extends Interview>(target: new() => T): new() => T {
    const original = target

    const newConstructor: any = function(this: any, ...args: any[]) {
      const instance = new original(...args)
      instance._chatfield.roles.alice.type = role
      return instance
    }

    newConstructor.prototype = original.prototype
    
    // Add trait method
    newConstructor.trait = function(trait: string) {
      return function<T extends Interview>(target: new() => T): new() => T {
        const instance = new target()
        instance._chatfield.roles.alice.traits.push(trait)
        return target
      }
    }

    return newConstructor
  }
}

// Make alice.trait available
(alice as any).trait = function(trait: string) {
  return function<T extends Interview>(target: new() => T): new() => T {
    const original = target

    const newConstructor: any = function(this: any, ...args: any[]) {
      const instance = new original(...args)
      instance._chatfield.roles.alice.traits.push(trait)
      return instance
    }

    newConstructor.prototype = original.prototype
    return newConstructor
  }
}

/**
 * Bob decorator - sets the interviewee role
 */
export function bob(role: string) {
  return function<T extends Interview>(target: new() => T): new() => T {
    const original = target

    const newConstructor: any = function(this: any, ...args: any[]) {
      const instance = new original(...args)
      instance._chatfield.roles.bob.type = role
      return instance
    }

    newConstructor.prototype = original.prototype
    
    // Add trait method
    newConstructor.trait = function(trait: string) {
      return function<T extends Interview>(target: new() => T): new() => T {
        const instance = new target()
        instance._chatfield.roles.bob.traits.push(trait)
        return target
      }
    }

    return newConstructor
  }
}

// Make bob.trait available
(bob as any).trait = function(trait: string) {
  return function<T extends Interview>(target: new() => T): new() => T {
    const original = target

    const newConstructor: any = function(this: any, ...args: any[]) {
      const instance = new original(...args)
      instance._chatfield.roles.bob.traits.push(trait)
      return instance
    }

    newConstructor.prototype = original.prototype
    return newConstructor
  }
}

/**
 * Field specification decorators
 */
export function must(rule: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { specs: {} }
    if (!existing.specs.must) existing.specs.must = []
    existing.specs.must.push(rule)
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export function reject(rule: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { specs: {} }
    if (!existing.specs.reject) existing.specs.reject = []
    existing.specs.reject.push(rule)
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export function hint(hint: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { specs: {} }
    if (!existing.specs.hint) existing.specs.hint = []
    existing.specs.hint.push(hint)
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

/**
 * Type transformation decorators
 */
export function as_int(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_int = {
      type: 'int',
      prompt: prompt || 'Parse as integer'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export function as_float(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_float = {
      type: 'float',
      prompt: prompt || 'Parse as floating point number'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export function as_bool(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_bool = {
      type: 'bool',
      prompt: prompt || 'Parse as boolean (true/false)'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export function as_str(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_str = {
      type: 'str',
      prompt: prompt || 'Format as string'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export function as_percent(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_percent = {
      type: 'float',
      prompt: prompt || 'Parse as percentage (0.0 to 1.0)'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export function as_list(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_list = {
      type: 'list',
      prompt: prompt || 'Parse as list/array'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export function as_set(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_set = {
      type: 'set',
      prompt: prompt || 'Parse as unique set of values'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export function as_dict(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_dict = {
      type: 'dict',
      prompt: prompt || 'Parse as key-value dictionary/object'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

// Language decorator with sub-attributes
export const as_lang = {
  fr: function(prompt?: string) {
    return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
      const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
      if (!existing.casts) existing.casts = {}
      existing.casts.as_lang_fr = {
        type: 'str',
        prompt: prompt || 'Translate to French'
      }
      Reflect.defineMetadata('chatfield', existing, target, propertyKey)
    }
  },
  de: function(prompt?: string) {
    return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
      const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
      if (!existing.casts) existing.casts = {}
      existing.casts.as_lang_de = {
        type: 'str',
        prompt: prompt || 'Translate to German'
      }
      Reflect.defineMetadata('chatfield', existing, target, propertyKey)
    }
  },
  th: function(prompt?: string) {
    return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
      const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
      if (!existing.casts) existing.casts = {}
      existing.casts.as_lang_th = {
        type: 'str',
        prompt: prompt || 'Translate to Thai'
      }
      Reflect.defineMetadata('chatfield', existing, target, propertyKey)
    }
  },
  esperanto: function(prompt?: string) {
    return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
      const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
      if (!existing.casts) existing.casts = {}
      existing.casts.as_lang_esperanto = {
        type: 'str',
        prompt: prompt || 'Translate to Esperanto'
      }
      Reflect.defineMetadata('chatfield', existing, target, propertyKey)
    }
  },
  traditionalChinese: function(prompt?: string) {
    return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
      const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
      if (!existing.casts) existing.casts = {}
      existing.casts.as_lang_traditionalChinese = {
        type: 'str',
        prompt: prompt || 'Translate to Traditional Chinese'
      }
      Reflect.defineMetadata('chatfield', existing, target, propertyKey)
    }
  }
}

// Boolean sub-attributes
;(as_bool as any).even = function(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_bool_even = {
      type: 'bool',
      prompt: prompt || 'True if even, False if odd'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

;(as_bool as any).odd = function(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_bool_odd = {
      type: 'bool',
      prompt: prompt || 'True if odd, False if even'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

;(as_bool as any).power_of_two = function(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_bool_power_of_two = {
      type: 'bool',
      prompt: prompt || 'True if power of two, False otherwise'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

// Set sub-attributes
;(as_set as any).factors = function(prompt?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_set_factors = {
      type: 'set',
      prompt: prompt || 'Set of all factors excluding 1 and the number itself'
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

// Choice cardinality decorators
export const as_one = function(...choices: string[]) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    
    // Create sub-decorator functions for named choices
    const decorator: any = function(...choices: string[]) {
      return as_one(...choices)
    }
    
    decorator.parity = function(...choices: string[]) {
      existing.casts.as_one_parity = {
        type: 'choice',
        prompt: 'Choose exactly one: {name}',
        choices: choices,
        null: false,
        multi: false
      }
      Reflect.defineMetadata('chatfield', existing, target, propertyKey)
    }
    
    return decorator
  }
}

// Add parity as a property
;(as_one as any).parity = function(...choices: string[]) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
    if (!existing.casts) existing.casts = {}
    existing.casts.as_one_parity = {
      type: 'choice',
      prompt: 'Choose exactly one: {name}',
      choices: choices,
      null: false,
      multi: false
    }
    Reflect.defineMetadata('chatfield', existing, target, propertyKey)
  }
}

export const as_maybe = {
  speaking: function(...choices: string[]) {
    return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
      const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
      if (!existing.casts) existing.casts = {}
      existing.casts.as_maybe_speaking = {
        type: 'choice',
        prompt: 'Choose zero or one: {name}',
        choices: choices,
        null: true,
        multi: false
      }
      Reflect.defineMetadata('chatfield', existing, target, propertyKey)
    }
  }
}

export const as_multi = {
  math_facts: function(...choices: string[]) {
    return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
      const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
      if (!existing.casts) existing.casts = {}
      existing.casts.as_multi_math_facts = {
        type: 'choice',
        prompt: 'Choose one or more: {name}',
        choices: choices,
        null: false,
        multi: true
      }
      Reflect.defineMetadata('chatfield', existing, target, propertyKey)
    }
  }
}

export const as_any = {
  other_facts: function(...choices: string[]) {
    return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
      const existing = Reflect.getMetadata('chatfield', target, propertyKey) || { casts: {} }
      if (!existing.casts) existing.casts = {}
      existing.casts.as_any_other_facts = {
        type: 'choice',
        prompt: 'Choose zero or more: {name}',
        choices: choices,
        null: true,
        multi: true
      }
      Reflect.defineMetadata('chatfield', existing, target, propertyKey)
    }
  }
}