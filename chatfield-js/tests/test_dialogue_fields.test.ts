/**
 * Test field behaviors and decorators in Interview classes.
 * Mirrors Python's test_dialogue_fields.py
 */

import { chatfield } from '../src/builders/gatherer-builder'

describe('TestInterviewFields', () => {
  test('test_field_with_type_transformations', () => {
    const instance = chatfield()
      .type('TypedInterview')
      .desc('Interview with typed fields')
      .field('age')
        .desc('Your age')
        .as_int()
      .field('salary')
        .desc('Expected salary')
        .as_float()
      .field('available')
        .desc('Are you available immediately?')
        .as_bool()
      .build()
    const meta = instance._chatfield

    // Check fields exist
    expect('age' in meta.fields).toBe(true)
    expect('salary' in meta.fields).toBe(true)
    expect('available' in meta.fields).toBe(true)

    // Check transformations are registered
    expect('as_int' in meta.fields.age.casts).toBe(true)
    expect('as_float' in meta.fields.salary.casts).toBe(true)
    expect('as_bool' in meta.fields.available.casts).toBe(true)
  })

  test('test_field_with_language_transformations', () => {
    const instance = chatfield()
      .type('MultilingualInterview')
      .desc('Interview with language transformations')
      .field('greeting')
        .desc('Say hello')
        .as_lang.fr()
        .as_lang.es()
      .build()
    const meta = instance._chatfield

    // Check field exists
    expect('greeting' in meta.fields).toBe(true)

    // Check language transformations
    const fieldCasts = meta.fields.greeting.casts
    expect('as_lang_fr' in fieldCasts).toBe(true)
    expect('as_lang_es' in fieldCasts).toBe(true)
  })

  test('test_field_with_mixed_decorators', () => {
    const instance = chatfield()
      .type('MixedInterview')
      .desc('Interview with mixed decorators')
      .field('years_experience')
        .desc('Years of experience')
        .must('be positive')
        .hint('Think of your best qualities')
        .as_int()
      .build()
    const meta = instance._chatfield

    const field = meta.fields.years_experience

    // Check validation rules
    expect(field.specs.must).toContain('be positive')
    expect(field.specs.hint).toContain('Think of your best qualities')

    // Check transformation
    expect('as_int' in field.casts).toBe(true)
  })

  test('test_multiple_fields_with_decorators', () => {
    const instance = chatfield()
      .type('CompleteInterview')
      .desc('Complete interview process')
      .field('name')
        .desc('Your full name')
        .must('be honest')
      .field('email')
        .desc('Your email address')
        .must('valid email')
        .hint("We'll send confirmation here")
      .field('experience')
        .desc('Years of experience')
        .must('be realistic')
        .as_int()
      .field('remote')
        .desc('Open to remote work?')
        .as_bool()
      .build()
    const meta = instance._chatfield

    // Verify all fields exist
    expect(Object.keys(meta.fields).length).toBe(4)
    expect(['name', 'email', 'experience', 'remote'].every(field => field in meta.fields)).toBe(true)

    // Check specific field configurations
    expect(meta.fields.name.specs.must).toContain('be honest')
    expect(meta.fields.email.specs.must).toContain('valid email')
    expect(meta.fields.email.specs.hint).toContain("We'll send confirmation here")
    expect('as_int' in meta.fields.experience.casts).toBe(true)
    expect('as_bool' in meta.fields.remote.casts).toBe(true)
  })

  test('test_field_description_extraction', () => {
    const instance = chatfield()
      .type('DescriptiveInterview')
      .desc('Interview with detailed descriptions')
      .field('short').desc('Name')
      .field('medium').desc('Please provide your full legal name')
      .field('long').desc('This is a very long description that explains in great detail what we need from you and why it\'s important for the process')
      .build()
    const meta = instance._chatfield

    expect(meta.fields.short.desc).toBe('Name')
    expect(meta.fields.medium.desc).toBe('Please provide your full legal name')
    expect(meta.fields.long.desc).toBe('This is a very long description that explains in great detail what we need from you and why it\'s important for the process')
  })

  test('test_field_order_preservation', () => {
    const instance = chatfield()
      .type('OrderedInterview')
      .desc('Interview with specific field order')
      .field('first').desc('First question')
      .field('second').desc('Second question')
      .field('third').desc('Third question')
      .field('fourth').desc('Fourth question')
      .build()
    const meta = instance._chatfield

    // JavaScript/TypeScript guarantees object key order
    const fieldNames = Object.keys(meta.fields)
    expect(fieldNames).toEqual(['first', 'second', 'third', 'fourth'])
  })

  test('test_empty_specs_and_casts', () => {
    const instance = chatfield()
      .type('PlainInterview')
      .desc('Plain interview without decorators')
      .field('undecorated').desc('Simple field')
      .build()
    const meta = instance._chatfield

    const field = meta.fields.undecorated

    // Should have empty specs and casts
    expect(field.specs.must).toEqual([])
    expect(field.specs.reject).toEqual([])
    expect(field.specs.hint).toEqual([])
    expect(field.casts).toEqual({})
    expect(field.value).toBeNull() // Not collected yet
  })
})