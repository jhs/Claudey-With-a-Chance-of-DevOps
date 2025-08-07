/**
 * Tests for conversation management
 */

import { Conversation } from '../src/core/conversation'
import { GathererMeta, FieldMeta } from '../src/core/metadata'
import { MockLLMBackend } from '../src/backends/llm-backend'

describe('Conversation', () => {
  let meta: GathererMeta
  let conversation: Conversation
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    meta = new GathererMeta()
    meta.setDocstring('Test gathering session')
    meta.addUserContext('test user')
    meta.addAgentContext('be helpful')
    
    const field1 = meta.addField('name', 'Your name')
    field1.addMustRule('be specific')
    field1.setHint('First and last name')
    
    const field2 = meta.addField('email', 'Your email')
    field2.addRejectRule('no temporary emails')

    mockLLM = new MockLLMBackend()
    conversation = new Conversation(meta, {
      llmBackend: mockLLM,
      maxRetryAttempts: 2
    })
  })

  test('should initialize correctly', () => {
    expect(conversation.getUncollectedFields()).toEqual(['name', 'email'])
    expect(conversation.getCurrentData()).toEqual({})
    expect(conversation.getHistory()).toEqual([])
  })

  test('should determine next field', () => {
    let nextField = conversation.getNextField()
    expect(nextField?.name).toBe('name')
    
    // Simulate collecting the first field
    const collected = conversation.getCurrentData()
    collected.name = 'John Doe'
    
    nextField = conversation.getNextField()
    expect(nextField?.name).toBe('email')
  })

  test('should handle conditional fields', () => {
    const conditionalMeta = new GathererMeta()
    conditionalMeta.addField('hasExperience', 'Do you have experience?')
    const conditionalField = conditionalMeta.addField('details', 'Please describe')
    conditionalField.setWhenCondition(data => data.hasExperience === 'yes')

    const conditionalConversation = new Conversation(conditionalMeta)
    
    // Initially, only the first field should be visible
    expect(conditionalConversation.getVisibleUncollectedFields()).toHaveLength(1)
    expect(conditionalConversation.getVisibleUncollectedFields()[0].name).toBe('hasExperience')
    
    // After answering yes, both fields should be visible
    const data = conditionalConversation.getCurrentData()
    data.hasExperience = 'yes'
    expect(conditionalConversation.getVisibleUncollectedFields()).toHaveLength(1) // details is still uncollected
    
    // After collecting hasExperience, details should be next
    const nextField = conditionalConversation.getNextField()
    expect(nextField?.name).toBe('details')
  })

  test('should build field prompts correctly', () => {
    const field = meta.getField('name')!
    const prompt = (conversation as any).buildFieldPrompt(field)
    
    expect(prompt).toContain('Your name?')
    expect(prompt).toContain('💡 First and last name')
  })

  test('should build contextual prompts', () => {
    // Simulate having some collected data
    const data = conversation.getCurrentData()
    data.name = 'John Doe'
    
    const emailField = meta.getField('email')!
    const prompt = (conversation as any).buildFieldPrompt(emailField)
    
    expect(prompt).toContain('Based on what you\'ve told me')
    expect(prompt).toContain('name: John Doe')
    expect(prompt).toContain('your email?')
  })

  test('should validate responses with LLM', async () => {
    mockLLM.addValidationResponse('VALID')
    
    const field = meta.getField('name')!
    const result = await conversation.validateResponse(field, 'John Smith')
    
    expect(result.isValid).toBe(true)
    expect(result.feedback).toBe('')
  })

  test('should handle validation failures', async () => {
    mockLLM.addValidationResponse('The name is too generic. Please provide more specific information.')
    
    const field = meta.getField('name')!
    const result = await conversation.validateResponse(field, 'John')
    
    expect(result.isValid).toBe(false)
    expect(result.feedback).toContain('too generic')
  })

  test('should build validation prompts correctly', () => {
    const field = meta.getField('name')!
    const prompt = (conversation as any).buildValidationPrompt(field, 'John')
    
    expect(prompt).toContain('The user provided this answer: "John"')
    expect(prompt).toContain('MUST include: be specific')
    expect(prompt).toContain('Your name')
  })

  test('should process user responses', async () => {
    mockLLM.addValidationResponse('VALID')
    
    // Mock event handlers
    const events = {
      onMessage: jest.fn(),
      onFieldComplete: jest.fn()
    }
    conversation.setEventHandlers(events)
    
    const result = await conversation.processUserResponse('John Smith')
    
    expect(result.success).toBe(true)
    expect(events.onMessage).toHaveBeenCalled()
    expect(events.onFieldComplete).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'name' }),
      'John Smith'
    )
    
    expect(conversation.getCurrentData().name).toBe('John Smith')
  })

  test('should handle validation retry', async () => {
    mockLLM.addValidationResponse('Please be more specific.')
    
    const events = {
      onValidationError: jest.fn()
    }
    conversation.setEventHandlers(events)
    
    const result = await conversation.processUserResponse('John')
    
    expect(result.success).toBe(false)
    expect(result.needsRetry).toBe(true)
    expect(result.feedback).toContain('more specific')
    expect(events.onValidationError).toHaveBeenCalled()
  })

  test('should reject empty responses', async () => {
    const result = await conversation.processUserResponse('  ')
    
    expect(result.success).toBe(false)
    expect(result.needsRetry).toBe(true)
    expect(result.feedback).toContain('Please provide an answer')
  })

  test('should generate conversation summary', () => {
    const data = conversation.getCurrentData()
    data.name = 'John Smith'
    data.email = 'john@example.com'
    
    const summary = conversation.getConversationSummary()
    
    expect(summary).toContain('Collected so far:')
    expect(summary).toContain('Your name: John Smith')
    expect(summary).toContain('Your email: john@example.com')
  })

  test('should handle empty summary', () => {
    const summary = conversation.getConversationSummary()
    expect(summary).toBe('No data collected yet.')
  })

  test('should reset conversation', () => {
    // Add some data and history
    const data = conversation.getCurrentData()
    data.name = 'John'
    conversation.getHistory().push({
      role: 'user',
      content: 'John',
      timestamp: new Date()
    })
    
    conversation.reset()
    
    expect(conversation.getCurrentData()).toEqual({})
    expect(conversation.getHistory()).toEqual([])
  })

  test('should handle fields without validation', async () => {
    const simpleField = new FieldMeta('simple', 'Simple field')
    const result = await conversation.validateResponse(simpleField, 'any answer')
    
    expect(result.isValid).toBe(true)
    expect(result.feedback).toBe('')
  })

  test('should be permissive when LLM fails', async () => {
    // No LLM backend provided
    const noLLMConversation = new Conversation(meta)
    const field = meta.getField('name')!
    
    const result = await noLLMConversation.validateResponse(field, 'John')
    expect(result.isValid).toBe(true) // Should be permissive
  })
})