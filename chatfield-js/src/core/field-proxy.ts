/**
 * FieldProxy - A string-like object with transformation properties
 * 
 * This provides similar ergonomics to Python's FieldProxy by using JavaScript's
 * Proxy to wrap a String object, allowing natural string operations while also
 * providing transformation access via properties.
 */

export interface FieldTransformations {
  [key: string]: any
  value: string
  context?: string
  as_quote?: string
  as_int?: number
  as_float?: number
  as_bool?: boolean
  as_percent?: number
  // Dynamic language transformations: as_lang_fr, as_lang_es, etc.
  // Dynamic choice transformations: as_one_priority, as_multi_skills, etc.
}

export interface FieldMetadata {
  desc: string
  specs: {
    must?: string[]
    reject?: string[]
    hint?: string[]
    confidential?: boolean
    conclude?: boolean
  }
  casts: {
    [key: string]: {
      type: string
      prompt: string
      choices?: string[]
      null?: boolean
      multi?: boolean
    }
  }
  value: FieldTransformations | null
}

/**
 * Create a FieldProxy that acts like a string but has transformation properties
 */
export function createFieldProxy(value: string, metadata: FieldMetadata): any {
  // Create a String object (not primitive) to use as base
  const stringObj = new String(value)
  
  // Store metadata on the String object
  ;(stringObj as any)._chatfield = metadata
  
  // Create and return the Proxy
  return new Proxy(stringObj, {
    get(target: any, prop: string | symbol, receiver: any) {
      // Handle symbol properties (needed for string coercion)
      if (typeof prop === 'symbol') {
        if (prop === Symbol.toPrimitive) {
          return (hint: string) => {
            if (hint === 'string' || hint === 'default') {
              return value
            }
            if (hint === 'number') {
              return Number(value)
            }
            return value
          }
        }
        if (prop === Symbol.toStringTag) {
          return 'FieldProxy'
        }
        return Reflect.get(target, prop, receiver)
      }
      
      // Handle valueOf and toString explicitly
      if (prop === 'valueOf' || prop === 'toString') {
        return () => value
      }
      
      // Handle length property
      if (prop === 'length') {
        return value.length
      }
      
      // Handle numeric indices for character access
      if (!isNaN(Number(prop))) {
        return value[Number(prop)]
      }
      
      // Check for transformation properties from metadata
      const transformations = metadata.value
      if (transformations && prop in transformations && prop !== 'value') {
        return transformations[prop]
      }
      
      // Handle _chatfield metadata access
      if (prop === '_chatfield') {
        return metadata
      }
      
      // Handle _pretty method like Python
      if (prop === '_pretty') {
        return () => {
          const lines: string[] = []
          if (transformations) {
            for (const [key, val] of Object.entries(transformations)) {
              if (key !== 'value') {
                lines.push(`    ${key.padEnd(25)}: ${JSON.stringify(val)}`)
              }
            }
          }
          return lines.join('\n')
        }
      }
      
      // Check if it's a String prototype method
      if (prop in String.prototype) {
        const method = (String.prototype as any)[prop]
        if (typeof method === 'function') {
          return function(...args: any[]) {
            // Call the method on the primitive string value
            const result = method.apply(value, args)
            // If the result is a string, wrap it in a new FieldProxy
            if (typeof result === 'string' && result !== value) {
              // For methods that return a new string, return plain string
              // (not a FieldProxy, as transformations wouldn't apply)
              return result
            }
            return result
          }
        }
      }
      
      // Default: try to get from the String object
      const val = Reflect.get(target, prop, receiver)
      if (val !== undefined) {
        return val
      }
      
      // Property doesn't exist
      return undefined
    },
    
    // Handle setting properties (shouldn't normally happen)
    set(target: any, prop: string | symbol, value: any, receiver: any) {
      if (prop === '_chatfield') {
        target._chatfield = value
        return true
      }
      return Reflect.set(target, prop, value, receiver)
    },
    
    // Make typeof return 'string'
    has(target: any, prop: string | symbol) {
      if (typeof prop === 'string') {
        // Check transformations first
        const transformations = metadata.value
        if (transformations && prop in transformations) {
          return true
        }
        // Then check String prototype
        if (prop in String.prototype) {
          return true
        }
      }
      return Reflect.has(target, prop)
    },
    
    // Support for...in loops
    ownKeys(target: any) {
      const keys = new Set<string | symbol>()
      
      // Add string indices
      for (let i = 0; i < value.length; i++) {
        keys.add(String(i))
      }
      
      // Add transformation keys
      const transformations = metadata.value
      if (transformations) {
        for (const key of Object.keys(transformations)) {
          if (key !== 'value') {
            keys.add(key)
          }
        }
      }
      
      // Add String methods
      for (const key of Object.getOwnPropertyNames(String.prototype)) {
        keys.add(key)
      }
      
      return Array.from(keys)
    },
    
    // Support property descriptor queries
    getOwnPropertyDescriptor(target: any, prop: string | symbol) {
      if (typeof prop === 'string') {
        // Check numeric indices
        if (!isNaN(Number(prop))) {
          const index = Number(prop)
          if (index >= 0 && index < value.length) {
            return {
              value: value[index],
              writable: false,
              enumerable: true,
              configurable: true
            }
          }
        }
        
        // Check transformations
        const transformations = metadata.value
        if (transformations && prop in transformations && prop !== 'value') {
          return {
            value: transformations[prop],
            writable: false,
            enumerable: true,
            configurable: true
          }
        }
      }
      
      return Reflect.getOwnPropertyDescriptor(target, prop)
    }
  })
}

/**
 * Type definition for FieldProxy to provide TypeScript IntelliSense
 */
export interface FieldProxy extends String {
  // Metadata access
  readonly _chatfield: FieldMetadata
  _pretty(): string
  
  // Common transformations (may or may not exist)
  readonly as_int?: number
  readonly as_float?: number
  readonly as_bool?: boolean
  readonly as_percent?: number
  
  // Dynamic transformations
  [key: string]: any
}

/**
 * Type guard to check if a value is a FieldProxy
 */
export function isFieldProxy(value: any): value is FieldProxy {
  return value && 
         typeof value === 'object' && 
         '_chatfield' in value &&
         typeof value.valueOf === 'function' &&
         typeof value.valueOf() === 'string'
}

/**
 * Helper to create an empty/null FieldProxy
 */
export function createNullFieldProxy(metadata: FieldMetadata): null {
  // When field has no value yet, return null (like Python version)
  return null
}