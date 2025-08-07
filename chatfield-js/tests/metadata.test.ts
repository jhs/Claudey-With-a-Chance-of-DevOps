/**
 * Tests for metadata classes
 */

import { FieldMeta, GathererMeta } from '../src/core/metadata'

describe('FieldMeta', () => {
  let fieldMeta: FieldMeta

  beforeEach(() => {
    fieldMeta = new FieldMeta('testField', 'Test field description')
  })

  test('should initialize with name and description', () => {
    expect(fieldMeta.name).toBe('testField')
    expect(fieldMeta.description).toBe('Test field description')
    expect(fieldMeta.mustRules).toEqual([])
    expect(fieldMeta.rejectRules).toEqual([])
    expect(fieldMeta.hint).toBeUndefined()
  })

  test('should add must rules', () => {
    fieldMeta.addMustRule('include specific details')
    fieldMeta.addMustRule('mention timeline')
    
    expect(fieldMeta.mustRules).toEqual(['include specific details', 'mention timeline'])
  })

  test('should add reject rules', () => {
    fieldMeta.addRejectRule('no vague statements')
    fieldMeta.addRejectRule('avoid generic answers')
    
    expect(fieldMeta.rejectRules).toEqual(['no vague statements', 'avoid generic answers'])
  })

  test('should set hint', () => {
    fieldMeta.setHint('This is a helpful hint')
    expect(fieldMeta.hint).toBe('This is a helpful hint')
  })

  test('should detect validation rules', () => {
    expect(fieldMeta.hasValidationRules()).toBe(false)
    
    fieldMeta.addMustRule('test rule')
    expect(fieldMeta.hasValidationRules()).toBe(true)
    
    const fieldWithReject = new FieldMeta('test', 'desc')
    fieldWithReject.addRejectRule('reject rule')
    expect(fieldWithReject.hasValidationRules()).toBe(true)
  })

  test('should handle conditional visibility', () => {
    const condition = (data: Record<string, string>) => data.hasPrereq === 'yes'
    fieldMeta.setWhenCondition(condition)
    
    expect(fieldMeta.shouldShow({})).toBe(false)
    expect(fieldMeta.shouldShow({ hasPrereq: 'no' })).toBe(false)
    expect(fieldMeta.shouldShow({ hasPrereq: 'yes' })).toBe(true)
  })

  test('should clone correctly', () => {
    fieldMeta.addMustRule('must rule')
    fieldMeta.addRejectRule('reject rule')
    fieldMeta.setHint('hint text')
    fieldMeta.setWhenCondition(() => true)
    
    const clone = fieldMeta.clone()
    
    expect(clone.name).toBe(fieldMeta.name)
    expect(clone.description).toBe(fieldMeta.description)
    expect(clone.mustRules).toEqual(fieldMeta.mustRules)
    expect(clone.rejectRules).toEqual(fieldMeta.rejectRules)
    expect(clone.hint).toBe(fieldMeta.hint)
    expect(clone.whenCondition).toBeDefined()
    
    // Ensure it's a deep clone
    clone.mustRules.push('new rule')
    expect(fieldMeta.mustRules).not.toContain('new rule')
  })
})

describe('GathererMeta', () => {
  let gathererMeta: GathererMeta

  beforeEach(() => {
    gathererMeta = new GathererMeta()
  })

  test('should initialize empty', () => {
    expect(gathererMeta.userContext).toEqual([])
    expect(gathererMeta.agentContext).toEqual([])
    expect(gathererMeta.docstring).toBe('')
    expect(gathererMeta.fields.size).toBe(0)
    expect(gathererMeta.getFieldNames()).toEqual([])
  })

  test('should add user context', () => {
    gathererMeta.addUserContext('startup founder')
    gathererMeta.addUserContext('technical background')
    
    expect(gathererMeta.userContext).toEqual(['startup founder', 'technical background'])
  })

  test('should add agent context', () => {
    gathererMeta.addAgentContext('be patient')
    gathererMeta.addAgentContext('ask follow-up questions')
    
    expect(gathererMeta.agentContext).toEqual(['be patient', 'ask follow-up questions'])
  })

  test('should set docstring', () => {
    gathererMeta.setDocstring('  This is a docstring with whitespace  ')
    expect(gathererMeta.docstring).toBe('This is a docstring with whitespace')
  })

  test('should add and retrieve fields', () => {
    const field1 = gathererMeta.addField('name', 'Your name')
    const field2 = gathererMeta.addField('email', 'Your email')
    
    expect(gathererMeta.getFieldNames()).toEqual(['name', 'email'])
    expect(gathererMeta.getField('name')).toBe(field1)
    expect(gathererMeta.getField('email')).toBe(field2)
    expect(gathererMeta.getField('nonexistent')).toBeUndefined()
    
    const fields = gathererMeta.getFields()
    expect(fields).toHaveLength(2)
    expect(fields[0]).toBe(field1)
    expect(fields[1]).toBe(field2)
  })

  test('should detect context', () => {
    expect(gathererMeta.hasContext()).toBe(false)
    
    gathererMeta.addUserContext('user info')
    expect(gathererMeta.hasContext()).toBe(true)
    
    const gatherer2 = new GathererMeta()
    gatherer2.addAgentContext('agent behavior')
    expect(gatherer2.hasContext()).toBe(true)
    
    const gatherer3 = new GathererMeta()
    gatherer3.setDocstring('description')
    expect(gatherer3.hasContext()).toBe(true)
  })

  test('should filter visible fields', () => {
    const field1 = gathererMeta.addField('always', 'Always visible')
    const field2 = gathererMeta.addField('conditional', 'Conditionally visible')
    
    field2.setWhenCondition((data) => data.showConditional === 'yes')
    
    let visibleFields = gathererMeta.getVisibleFields({})
    expect(visibleFields).toHaveLength(1)
    expect(visibleFields[0]).toBe(field1)
    
    visibleFields = gathererMeta.getVisibleFields({ showConditional: 'yes' })
    expect(visibleFields).toHaveLength(2)
    expect(visibleFields).toContain(field1)
    expect(visibleFields).toContain(field2)
  })

  test('should clone correctly', () => {
    gathererMeta.addUserContext('user context')
    gathererMeta.addAgentContext('agent context')
    gathererMeta.setDocstring('docstring')
    const field = gathererMeta.addField('field', 'description')
    field.addMustRule('must rule')
    
    const clone = gathererMeta.clone()
    
    expect(clone.userContext).toEqual(gathererMeta.userContext)
    expect(clone.agentContext).toEqual(gathererMeta.agentContext)
    expect(clone.docstring).toBe(gathererMeta.docstring)
    expect(clone.getFieldNames()).toEqual(gathererMeta.getFieldNames())
    
    const clonedField = clone.getField('field')!
    expect(clonedField.mustRules).toEqual(field.mustRules)
    
    // Ensure it's a deep clone
    clone.userContext.push('new context')
    expect(gathererMeta.userContext).not.toContain('new context')
    
    clonedField.addMustRule('new rule')
    expect(field.mustRules).not.toContain('new rule')
  })
})