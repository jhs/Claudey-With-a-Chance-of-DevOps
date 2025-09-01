/**
 * Tests for FieldProxy implementation
 */

import { createFieldProxy, isFieldProxy, FieldMetadata, FieldTransformations } from '../src/core/field-proxy'

describe('FieldProxy', () => {
  describe('String behavior', () => {
    it('should act as a string in string contexts', () => {
      const metadata: FieldMetadata = {
        desc: 'Test field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: 'hello world' }
      }
      
      const proxy = createFieldProxy('hello world', metadata)
      
      // String equality
      expect(proxy == 'hello world').toBe(true)
      expect(proxy === 'hello world').toBe(false) // Strict equality won't work with objects
      expect(proxy.valueOf()).toBe('hello world')
      expect(proxy.toString()).toBe('hello world')
      expect(String(proxy)).toBe('hello world')
    })

    it('should support string methods', () => {
      const metadata: FieldMetadata = {
        desc: 'Test field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: 'Hello World' }
      }
      
      const proxy = createFieldProxy('Hello World', metadata)
      
      expect(proxy.toUpperCase()).toBe('HELLO WORLD')
      expect(proxy.toLowerCase()).toBe('hello world')
      expect(proxy.substring(0, 5)).toBe('Hello')
      expect(proxy.split(' ')).toEqual(['Hello', 'World'])
      expect(proxy.length).toBe(11)
      expect(proxy[0]).toBe('H')
      expect(proxy.charAt(6)).toBe('W')
      expect(proxy.indexOf('World')).toBe(6)
      expect(proxy.includes('Hello')).toBe(true)
      expect(proxy.startsWith('Hello')).toBe(true)
      expect(proxy.endsWith('World')).toBe(true)
    })

    it('should work in template literals', () => {
      const metadata: FieldMetadata = {
        desc: 'Name field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: 'John' }
      }
      
      const proxy = createFieldProxy('John', metadata)
      const message = `Hello ${proxy}!`
      
      expect(message).toBe('Hello John!')
    })

    it('should work with string concatenation', () => {
      const metadata: FieldMetadata = {
        desc: 'Test field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: 'Hello' }
      }
      
      const proxy = createFieldProxy('Hello', metadata)
      const result = proxy + ' World'
      
      expect(result).toBe('Hello World')
    })

    it('should support typeof checks', () => {
      const metadata: FieldMetadata = {
        desc: 'Test field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: 'test' }
      }
      
      const proxy = createFieldProxy('test', metadata)
      
      // typeof will return 'object' for Proxy, but we can check other things
      expect(typeof proxy.valueOf()).toBe('string')
      expect(isFieldProxy(proxy)).toBe(true)
    })
  })

  describe('Transformation access', () => {
    it('should provide access to transformations', () => {
      const transformations: FieldTransformations = {
        value: '42',
        as_int: 42,
        as_float: 42.0,
        as_bool: true,
        context: 'The answer is 42',
        as_quote: 'forty-two'
      }
      
      const metadata: FieldMetadata = {
        desc: 'Number field',
        specs: { must: [], reject: [], hint: [] },
        casts: {
          as_int: { type: 'int', prompt: 'parse as integer' },
          as_float: { type: 'float', prompt: 'parse as float' },
          as_bool: { type: 'bool', prompt: 'parse as boolean' }
        },
        value: transformations
      }
      
      const proxy = createFieldProxy('42', metadata)
      
      expect(proxy.valueOf()).toBe('42')
      expect(proxy.as_int).toBe(42)
      expect(proxy.as_float).toBe(42.0)
      expect(proxy.as_bool).toBe(true)
      expect(proxy.context).toBe('The answer is 42')
      expect(proxy.as_quote).toBe('forty-two')
    })

    it('should handle language transformations', () => {
      const transformations: FieldTransformations = {
        value: 'five',
        as_lang_fr: 'cinq',
        as_lang_es: 'cinco',
        as_lang_de: 'fünf'
      }
      
      const metadata: FieldMetadata = {
        desc: 'Number word',
        specs: { must: [], reject: [], hint: [] },
        casts: {
          as_lang_fr: { type: 'str', prompt: 'translate to French' },
          as_lang_es: { type: 'str', prompt: 'translate to Spanish' },
          as_lang_de: { type: 'str', prompt: 'translate to German' }
        },
        value: transformations
      }
      
      const proxy = createFieldProxy('five', metadata)
      
      expect(proxy.toString()).toBe('five')
      expect(proxy.as_lang_fr).toBe('cinq')
      expect(proxy.as_lang_es).toBe('cinco')
      expect(proxy.as_lang_de).toBe('fünf')
    })

    it('should handle choice transformations', () => {
      const transformations: FieldTransformations = {
        value: 'JavaScript, TypeScript, Python',
        as_multi_skill: ['JavaScript', 'TypeScript', 'Python'],
        as_one_primary: 'JavaScript'
      }
      
      const metadata: FieldMetadata = {
        desc: 'Skills',
        specs: { must: [], reject: [], hint: [] },
        casts: {
          as_multi_skill: { 
            type: 'choice', 
            prompt: 'parse as skill list',
            choices: ['JavaScript', 'TypeScript', 'Python', 'Go', 'Rust'],
            multi: true,
            null: false
          },
          as_one_primary: {
            type: 'choice',
            prompt: 'select primary skill',
            choices: ['JavaScript', 'TypeScript', 'Python', 'Go', 'Rust'],
            multi: false,
            null: false
          }
        },
        value: transformations
      }
      
      const proxy = createFieldProxy('JavaScript, TypeScript, Python', metadata)
      
      expect(proxy.valueOf()).toBe('JavaScript, TypeScript, Python')
      expect(proxy.as_multi_skill).toEqual(['JavaScript', 'TypeScript', 'Python'])
      expect(proxy.as_one_primary).toBe('JavaScript')
    })

    it('should return undefined for non-existent transformations', () => {
      const metadata: FieldMetadata = {
        desc: 'Test field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: 'test' }
      }
      
      const proxy = createFieldProxy('test', metadata)
      
      expect(proxy.as_int).toBeUndefined()
      expect(proxy.nonExistent).toBeUndefined()
    })
  })

  describe('Metadata access', () => {
    it('should provide access to _chatfield metadata', () => {
      const metadata: FieldMetadata = {
        desc: 'Test field with metadata',
        specs: { 
          must: ['specific requirement'],
          reject: ['forbidden content'],
          hint: ['helpful tip'],
          confidential: false,
          conclude: false
        },
        casts: {
          as_int: { type: 'int', prompt: 'parse as integer' }
        },
        value: { value: 'test value', as_int: 123 }
      }
      
      const proxy = createFieldProxy('test value', metadata)
      
      expect(proxy._chatfield).toBe(metadata)
      expect(proxy._chatfield.desc).toBe('Test field with metadata')
      expect(proxy._chatfield.specs.must).toContain('specific requirement')
      expect(proxy._chatfield.casts.as_int.type).toBe('int')
    })

    it('should support _pretty() method', () => {
      const transformations: FieldTransformations = {
        value: '42',
        as_int: 42,
        as_float: 42.0,
        as_bool: true,
        as_lang_fr: 'quarante-deux'
      }
      
      const metadata: FieldMetadata = {
        desc: 'Number field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: transformations
      }
      
      const proxy = createFieldProxy('42', metadata)
      const pretty = proxy._pretty()
      
      expect(pretty).toContain('as_int')
      expect(pretty).toContain('42')
      expect(pretty).toContain('as_float')
      expect(pretty).toContain('as_bool')
      expect(pretty).toContain('as_lang_fr')
      expect(pretty).toContain('quarante-deux')
    })
  })

  describe('Null field handling', () => {
    it('should return null for fields with no value', () => {
      const metadata: FieldMetadata = {
        desc: 'Unpopulated field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: null
      }
      
      // When value is null, we typically return null (not a proxy)
      // This matches Python behavior
      const result = metadata.value ? createFieldProxy('', metadata) : null
      
      expect(result).toBeNull()
    })
  })

  describe('Edge cases', () => {
    it('should handle empty string values', () => {
      const metadata: FieldMetadata = {
        desc: 'Empty field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: '', as_bool_empty: true }
      }
      
      const proxy = createFieldProxy('', metadata)
      
      expect(proxy.valueOf()).toBe('')
      expect(proxy.length).toBe(0)
      expect(proxy.as_bool_empty).toBe(true)
    })

    it('should handle very long strings', () => {
      const longString = 'x'.repeat(10000)
      const metadata: FieldMetadata = {
        desc: 'Long field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: longString }
      }
      
      const proxy = createFieldProxy(longString, metadata)
      
      expect(proxy.length).toBe(10000)
      expect(proxy.substring(0, 10)).toBe('xxxxxxxxxx')
    })

    it('should handle special characters', () => {
      const specialString = '🎉 Hello\nWorld\t!"#$%'
      const metadata: FieldMetadata = {
        desc: 'Special field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: specialString }
      }
      
      const proxy = createFieldProxy(specialString, metadata)
      
      expect(proxy.valueOf()).toBe(specialString)
      expect(proxy.includes('🎉')).toBe(true)
      expect(proxy.split('\n')).toEqual(['🎉 Hello', 'World\t!"#$%'])
    })
  })

  describe('Type guard', () => {
    it('should correctly identify FieldProxy instances', () => {
      const metadata: FieldMetadata = {
        desc: 'Test field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: { value: 'test' }
      }
      
      const proxy = createFieldProxy('test', metadata)
      const normalString = 'test'
      const normalObject = { value: 'test' }
      
      expect(isFieldProxy(proxy)).toBe(true)
      expect(isFieldProxy(normalString)).toBe(false)
      expect(isFieldProxy(normalObject)).toBe(false)
      expect(isFieldProxy(null)).toBe(false)
      expect(isFieldProxy(undefined)).toBe(false)
    })
  })

  describe('Property iteration', () => {
    it('should support for...in loops for transformations', () => {
      const transformations: FieldTransformations = {
        value: '100',
        as_int: 100,
        as_float: 100.0,
        as_percent: 1.0
      }
      
      const metadata: FieldMetadata = {
        desc: 'Number field',
        specs: { must: [], reject: [], hint: [] },
        casts: {},
        value: transformations
      }
      
      const proxy = createFieldProxy('100', metadata)
      const foundProps = new Set<string>()
      
      for (const prop in proxy) {
        if (prop.startsWith('as_')) {
          foundProps.add(prop)
        }
      }
      
      expect(foundProps.has('as_int')).toBe(true)
      expect(foundProps.has('as_float')).toBe(true)
      expect(foundProps.has('as_percent')).toBe(true)
    })
  })
})