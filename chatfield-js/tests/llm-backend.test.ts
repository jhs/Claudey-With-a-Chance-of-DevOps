/**
 * Tests for LLM backends
 */

import { MockLLMBackend, ConsoleLLMBackend } from '../src/backends/llm-backend'
import { GathererMeta, FieldMeta } from '../src/core/metadata'
import { ConversationMessage } from '../src/core/types'

describe('MockLLMBackend', () => {
  let mockLLM: MockLLMBackend
  let meta: GathererMeta
  let field: FieldMeta
  let history: ConversationMessage[]

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    
    meta = new GathererMeta()
    meta.setDocstring('Test context')
    meta.addUserContext('test user')
    meta.addAgentContext('be helpful')
    
    field = new FieldMeta('name', 'Your name')
    field.addMustRule('be specific')
    field.setHint('First and last name')
    
    history = [
      { role: 'assistant', content: 'Hello', timestamp: new Date() },
      { role: 'user', content: 'Hi there', timestamp: new Date() }
    ]
  })

  test('should initialize correctly', () => {
    expect(mockLLM).toBeDefined()
  })

  test('should create conversation prompt', () => {
    const prompt = mockLLM.createConversationPrompt(meta, field, history)
    
    expect(prompt).toContain('Context: Test context')
    expect(prompt).toContain('Field: Your name')
    expect(prompt).toContain('Hint: First and last name')
  })

  test('should handle mock responses', async () => {
    mockLLM.addResponse('First response')
    mockLLM.addResponse('Second response')
    
    expect(await mockLLM.getResponse('test prompt')).toBe('First response')
    expect(await mockLLM.getResponse('test prompt')).toBe('Second response')
    expect(await mockLLM.getResponse('test prompt')).toBe('Mock response')
  })

  test('should handle mock validation responses', async () => {
    mockLLM.addValidationResponse('VALID')
    mockLLM.addValidationResponse('Please be more specific')
    
    expect(await mockLLM.validateResponse('test')).toBe('VALID')
    expect(await mockLLM.validateResponse('test')).toBe('Please be more specific')
    expect(await mockLLM.validateResponse('test')).toBe('VALID') // default
  })

  test('should reset state', () => {
    mockLLM.addResponse('test')
    mockLLM.addValidationResponse('test validation')
    
    // Use up the responses
    mockLLM.getResponse('prompt')
    mockLLM.validateResponse('validation')
    
    mockLLM.reset()
    
    // Should return defaults now
    expect(mockLLM.getResponse('prompt')).resolves.toBe('Mock response')
    expect(mockLLM.validateResponse('validation')).resolves.toBe('VALID')
  })
})

describe('ConsoleLLMBackend', () => {
  let consoleLLM: ConsoleLLMBackend
  let consoleSpy: jest.SpyInstance

  beforeEach(() => {
    consoleLLM = new ConsoleLLMBackend()
    consoleSpy = jest.spyOn(console, 'log').mockImplementation()
  })

  afterEach(() => {
    consoleSpy.mockRestore()
  })

  test('should create simple conversation prompt', () => {
    const meta = new GathererMeta()
    const field = new FieldMeta('test', 'Test field')
    field.setHint('Test hint')
    
    const prompt = consoleLLM.createConversationPrompt(meta, field, [])
    
    expect(prompt).toBe('Field: Test field\nHint: Test hint')
  })

  test('should log prompts to console', async () => {
    const response = await consoleLLM.getResponse('test prompt')
    
    expect(consoleSpy).toHaveBeenCalledWith('\n--- LLM Prompt ---')
    expect(consoleSpy).toHaveBeenCalledWith('test prompt')
    expect(consoleSpy).toHaveBeenCalledWith('--- End Prompt ---\n')
    expect(response).toContain('Console backend response')
  })

  test('should log validation prompts', async () => {
    const response = await consoleLLM.validateResponse('validation prompt')
    
    expect(consoleSpy).toHaveBeenCalledWith('\n--- Validation Prompt ---')
    expect(consoleSpy).toHaveBeenCalledWith('validation prompt')
    expect(consoleSpy).toHaveBeenCalledWith('--- End Validation ---\n')
    expect(response).toBe('VALID')
  })
})

// Note: OpenAIBackend tests would require either:
// 1. Integration tests with real API (expensive, slow)
// 2. Mocking the OpenAI client (complex, brittle)
// 3. Contract tests (recommended for production)

describe('OpenAIBackend', () => {
  // Skip actual OpenAI tests in unit test suite
  test.skip('should require API key', () => {
    // This would test OpenAI client initialization
    // Skipped to avoid requiring actual API keys in tests
  })

  test('should build comprehensive conversation prompts', () => {
    // Test the prompt building logic without actually calling OpenAI
    const meta = new GathererMeta()
    meta.setDocstring('Business planning session')
    meta.addUserContext('startup founder')
    meta.addUserContext('technical background')
    meta.addAgentContext('be patient')
    meta.addAgentContext('ask detailed questions')
    
    const field = new FieldMeta('concept', 'Business concept')
    field.addMustRule('include target market')
    field.addRejectRule('avoid vague descriptions')
    field.setHint('Think about your unique value proposition')
    
    const history: ConversationMessage[] = [
      { role: 'assistant', content: 'Welcome! I\'ll help you develop your business plan.', timestamp: new Date() },
      { role: 'user', content: 'I want to build a SaaS platform for small businesses', timestamp: new Date() }
    ]
    
    // We can test the prompt building logic by extracting it to a separate function
    // or by testing it through the mock backend that uses the same logic
    const mockLLM = new MockLLMBackend()
    const prompt = mockLLM.createConversationPrompt(meta, field, history)
    
    expect(prompt).toContain('Context: Business planning session')
    expect(prompt).toContain('Field: Business concept')
    expect(prompt).toContain('Hint: Think about your unique value proposition')
  })
})