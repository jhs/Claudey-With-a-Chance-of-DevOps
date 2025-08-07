/**
 * Tests for builder APIs
 */

import { chatfield, simpleGatherer, patientGatherer } from '../src/builders/gatherer-builder'
import { createGatherer, validateSchema, mergeSchemas, schemaPresets } from '../src/builders/schema-builder'
import { GathererSchema } from '../src/core/types'

describe('Fluent Builder API', () => {
  test('should create simple gatherer', () => {
    const gatherer = chatfield()
      .field('name', 'Your name')
      .field('email', 'Your email')
      .build()

    const meta = gatherer.getMeta()
    expect(meta.getFieldNames()).toEqual(['name', 'email'])
    
    const nameField = meta.getField('name')!
    expect(nameField.description).toBe('Your name')
    expect(nameField.mustRules).toEqual([])
  })

  test('should handle field validation rules', () => {
    const gatherer = chatfield()
      .field('concept', 'Your business concept')
      .must('include timeline')
      .must('be specific')
      .reject('vague statements')
      .hint('Think about your target market')
      .build()

    const meta = gatherer.getMeta()
    const field = meta.getField('concept')!
    
    expect(field.mustRules).toEqual(['include timeline', 'be specific'])
    expect(field.rejectRules).toEqual(['vague statements'])
    expect(field.hint).toBe('Think about your target market')
  })

  test('should handle conditional fields', () => {
    const gatherer = chatfield()
      .field('hasExperience', 'Do you have prior experience?')
      .field('experienceDetails', 'Please describe your experience')
      .when(data => data.hasExperience === 'yes')
      .build()

    const meta = gatherer.getMeta()
    const conditionalField = meta.getField('experienceDetails')!
    
    expect(conditionalField.shouldShow({})).toBe(false)
    expect(conditionalField.shouldShow({ hasExperience: 'no' })).toBe(false)
    expect(conditionalField.shouldShow({ hasExperience: 'yes' })).toBe(true)
  })

  test('should chain field definitions', () => {
    const gatherer = chatfield()
      .field('first', 'First field')
      .must('first rule')
      .field('second', 'Second field')
      .reject('second rule')
      .field('third', 'Third field')
      .hint('third hint')
      .build()

    const meta = gatherer.getMeta()
    expect(meta.getFieldNames()).toEqual(['first', 'second', 'third'])
    
    expect(meta.getField('first')!.mustRules).toEqual(['first rule'])
    expect(meta.getField('second')!.rejectRules).toEqual(['second rule'])
    expect(meta.getField('third')!.hint).toBe('third hint')
  })

  test('should handle context and docstring', () => {
    const gatherer = chatfield()
      .docstring('This is a test gatherer')
      .user('startup founder')
      .user('technical background')
      .agent('be patient')
      .agent('ask follow-ups')
      .field('test', 'Test field')
      .build()

    const meta = gatherer.getMeta()
    expect(meta.docstring).toBe('This is a test gatherer')
    expect(meta.userContext).toEqual(['startup founder', 'technical background'])
    expect(meta.agentContext).toEqual(['be patient', 'ask follow-ups'])
  })

  test('should create simple gatherer helper', () => {
    const gatherer = simpleGatherer({
      name: 'Your name',
      email: 'Your email',
      phone: 'Your phone number'
    }, {
      docstring: 'Contact information gathering',
      userContext: ['new customer'],
      agentContext: ['be friendly']
    })

    const meta = gatherer.getMeta()
    expect(meta.getFieldNames()).toEqual(['name', 'email', 'phone'])
    expect(meta.docstring).toBe('Contact information gathering')
    expect(meta.userContext).toEqual(['new customer'])
    expect(meta.agentContext).toEqual(['be friendly'])
  })

  test('should create preset gatherers', () => {
    const patient = patientGatherer().field('test', 'Test').build()
    const meta = patient.getMeta()
    
    expect(meta.agentContext).toContain('Be patient and thorough')
    expect(meta.agentContext).toContain('Ask follow-up questions when answers seem incomplete')
  })
})

describe('Schema Builder API', () => {
  const testSchema: GathererSchema = {
    docstring: 'Test schema',
    userContext: ['test user'],
    agentContext: ['test agent'],
    fields: {
      name: {
        description: 'Your name',
        must: ['be specific'],
        hint: 'First and last name'
      },
      email: {
        description: 'Your email',
        reject: ['no temporary emails']
      }
    }
  }

  test('should create gatherer from schema', () => {
    const gatherer = createGatherer(testSchema)
    const meta = gatherer.getMeta()

    expect(meta.docstring).toBe('Test schema')
    expect(meta.userContext).toEqual(['test user'])
    expect(meta.agentContext).toEqual(['test agent'])
    expect(meta.getFieldNames()).toEqual(['name', 'email'])
    
    const nameField = meta.getField('name')!
    expect(nameField.description).toBe('Your name')
    expect(nameField.mustRules).toEqual(['be specific'])
    expect(nameField.hint).toBe('First and last name')
    
    const emailField = meta.getField('email')!
    expect(emailField.rejectRules).toEqual(['no temporary emails'])
  })

  test('should validate schema', () => {
    // Valid schema
    let result = validateSchema(testSchema)
    expect(result.isValid).toBe(true)
    expect(result.errors).toEqual([])

    // Invalid schema - no fields
    result = validateSchema({ fields: {} })
    expect(result.isValid).toBe(false)
    expect(result.errors).toContain('Schema must have at least one field')

    // Invalid schema - missing description
    result = validateSchema({
      fields: {
        bad: {} as any
      }
    })
    expect(result.isValid).toBe(false)
    expect(result.errors.some(e => e.includes('must have a description'))).toBe(true)
  })

  test('should merge schemas', () => {
    const schema1: GathererSchema = {
      fields: { field1: { description: 'Field 1' } },
      userContext: ['user1'],
      docstring: 'First schema'
    }

    const schema2: GathererSchema = {
      fields: { field2: { description: 'Field 2' } },
      userContext: ['user2'],
      agentContext: ['agent1'],
      docstring: 'Second schema'
    }

    const merged = mergeSchemas(schema1, schema2)
    
    expect(Object.keys(merged.fields)).toEqual(['field1', 'field2'])
    expect(merged.userContext).toEqual(['user1', 'user2'])
    expect(merged.agentContext).toEqual(['agent1'])
    expect(merged.docstring).toBe('Second schema') // Last non-empty wins
  })

  test('should use schema presets', () => {
    const businessPlan = schemaPresets.businessPlan()
    
    expect(businessPlan.docstring).toContain('business plan')
    expect(businessPlan.userContext).toContain('entrepreneur')
    expect(Object.keys(businessPlan.fields)).toContain('concept')
    expect(Object.keys(businessPlan.fields)).toContain('market')
    
    // Test creating gatherer from preset
    const gatherer = createGatherer(businessPlan)
    const meta = gatherer.getMeta()
    expect(meta.getFieldNames().length).toBeGreaterThan(0)
  })

  test('should handle conditional fields in schema', () => {
    const schemaWithConditions: GathererSchema = {
      fields: {
        hasAccount: { description: 'Do you have an account?' },
        loginInfo: { 
          description: 'Login details',
          when: (data) => data.hasAccount === 'yes'
        }
      }
    }

    const gatherer = createGatherer(schemaWithConditions)
    const meta = gatherer.getMeta()
    const conditionalField = meta.getField('loginInfo')!
    
    expect(conditionalField.shouldShow({})).toBe(false)
    expect(conditionalField.shouldShow({ hasAccount: 'yes' })).toBe(true)
  })
})