/**
 * Integration tests for complete Chatfield workflows
 */

import { chatfield, simpleGatherer } from '../src/builders/gatherer-builder'
import { createGatherer, schemaPresets } from '../src/builders/schema-builder'
import { MockLLMBackend } from '../src/backends/llm-backend'
import { Conversation } from '../src/core/conversation'

describe('Chatfield Integration Tests', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    mockLLM.addValidationResponse('VALID')
    mockLLM.addValidationResponse('VALID')
    mockLLM.addValidationResponse('VALID')
  })

  test('should complete full business plan gathering workflow', async () => {
    const gatherer = chatfield()
      .docstring('Business plan gathering session')
      .user('startup founder')
      .agent('patient and thorough')
      .field('concept', 'Your business concept')
      .must('include target market')
      .hint('Describe what you\'re building and who it\'s for')
      .field('problem', 'What problem does it solve?')
      .must('specific problem statement')
      .field('revenue', 'How will you make money?')
      .when(data => data.concept && data.problem)
      .build({ llmBackend: mockLLM })

    // Simulate the conversation manually since we don't have UI integration yet
    const conversation = new Conversation(gatherer.getMeta(), { llmBackend: mockLLM })
    
    const events: any[] = []
    conversation.setEventHandlers({
      onMessage: (msg) => events.push({ type: 'message', data: msg }),
      onFieldStart: (field) => events.push({ type: 'fieldStart', data: field }),
      onFieldComplete: (field, value) => events.push({ type: 'fieldComplete', data: { field, value } })
    })

    // Process first field
    let result = await conversation.processUserResponse('A SaaS platform for small business inventory management targeting retail stores with 10-100 employees')
    expect(result.success).toBe(true)
    
    // Process second field  
    result = await conversation.processUserResponse('Small businesses struggle with accurate inventory tracking leading to stockouts and overstock situations')
    expect(result.success).toBe(true)
    
    // Process conditional third field (should be visible now)
    const nextField = conversation.getNextField()
    expect(nextField?.name).toBe('revenue')
    
    result = await conversation.processUserResponse('Monthly subscription model with tiered pricing')
    expect(result.success).toBe(true)

    const finalData = conversation.getCurrentData()
    expect(finalData.concept).toContain('SaaS platform')
    expect(finalData.problem).toContain('inventory tracking')
    expect(finalData.revenue).toContain('subscription model')
    
    expect(events.filter(e => e.type === 'fieldComplete')).toHaveLength(3)
  })

  test('should handle validation failures and retries', async () => {
    const gatherer = chatfield()
      .field('email', 'Your email address')
      .must('valid email format')
      .reject('temporary email providers')
      .build({ llmBackend: mockLLM })

    const conversation = new Conversation(gatherer.getMeta(), { llmBackend: mockLLM })
    
    // Set up validation responses: fail first, succeed second
    mockLLM.reset()
    mockLLM.addValidationResponse('Please provide a valid email format.')
    mockLLM.addValidationResponse('VALID')
    
    const validationErrors: string[] = []
    conversation.setEventHandlers({
      onValidationError: (field, error) => validationErrors.push(error)
    })

    // First attempt should fail
    let result = await conversation.processUserResponse('notanemail')
    expect(result.success).toBe(false)
    expect(result.needsRetry).toBe(true)
    expect(validationErrors).toHaveLength(1)
    
    // Second attempt should succeed
    result = await conversation.processUserResponse('user@example.com')
    expect(result.success).toBe(true)
    
    expect(conversation.getCurrentData().email).toBe('user@example.com')
  })

  test('should work with schema-based gatherers', async () => {
    const schema = schemaPresets.bugReport()
    const gatherer = createGatherer(schema, { llmBackend: mockLLM })
    
    expect(gatherer.getFieldPreview()).toEqual([
      { name: 'summary', description: 'What\'s a brief summary of the issue?', hasValidation: true, hint: 'One sentence describing what went wrong' },
      { name: 'steps', description: 'What steps can we follow to reproduce this bug?', hasValidation: true, hint: 'List the exact actions that lead to the problem' },
      { name: 'expected', description: 'What did you expect to happen?', hasValidation: true, hint: 'Describe the correct behavior you were expecting' },
      { name: 'actual', description: 'What actually happened instead?', hasValidation: true, hint: 'Describe what went wrong or what you saw instead' },
      { name: 'environment', description: 'What system are you using?', hasValidation: true, hint: 'OS, browser, app version, etc.' }
    ])

    const conversation = new Conversation(gatherer.getMeta(), { llmBackend: mockLLM })
    
    // Simulate collecting bug report data
    await conversation.processUserResponse('Button click doesn\'t work')
    await conversation.processUserResponse('1. Navigate to dashboard 2. Click submit button 3. Observe error')
    await conversation.processUserResponse('Form should submit successfully')
    await conversation.processUserResponse('Error message appears and form doesn\'t submit')
    await conversation.processUserResponse('Chrome 120 on macOS Ventura')
    
    const data = conversation.getCurrentData()
    expect(data.summary).toBe('Button click doesn\'t work')
    expect(data.steps).toContain('Navigate to dashboard')
    expect(data.expected).toContain('submit successfully')
    expect(data.actual).toContain('Error message')
    expect(data.environment).toContain('Chrome')
  })

  test('should handle simple gatherer helper', () => {
    const gatherer = simpleGatherer({
      firstName: 'Your first name',
      lastName: 'Your last name', 
      phone: 'Your phone number'
    }, {
      docstring: 'Contact information',
      userContext: ['new customer'],
      agentContext: ['be friendly']
    })

    const meta = gatherer.getMeta()
    expect(meta.docstring).toBe('Contact information')
    expect(meta.userContext).toEqual(['new customer'])
    expect(meta.agentContext).toEqual(['be friendly'])
    expect(meta.getFieldNames()).toEqual(['firstName', 'lastName', 'phone'])
  })

  test('should create gatherer instance with collected data', async () => {
    const gatherer = chatfield()
      .field('name', 'Your name')
      .field('age', 'Your age')
      .build({ llmBackend: mockLLM })

    const conversation = new Conversation(gatherer.getMeta(), { llmBackend: mockLLM })
    
    await conversation.processUserResponse('John Doe')
    await conversation.processUserResponse('30')
    
    const collectedData = conversation.getCurrentData()
    const instance = new (require('../src/core/gatherer').GathererInstance)(gatherer.getMeta(), collectedData)
    
    expect(instance.get('name')).toBe('John Doe')
    expect(instance.get('age')).toBe('30')
    expect(instance.get('nonexistent', 'default')).toBe('default')
    expect(instance.has('name')).toBe(true)
    expect(instance.has('nonexistent')).toBe(false)
    expect(instance.getCollectedFields()).toEqual(['name', 'age'])
    
    const data = instance.getData()
    expect(data).toEqual({ name: 'John Doe', age: '30' })
    
    expect(instance.toString()).toContain('name=\'John Doe\'')
    expect(instance.toString()).toContain('age=\'30\'')
  })

  test('should handle complex conditional logic', async () => {
    const gatherer = chatfield()
      .field('hasJob', 'Are you currently employed?')
      .field('jobTitle', 'What is your job title?')
      .when(data => data.hasJob === 'yes')
      .field('employer', 'Who do you work for?')
      .when(data => data.hasJob === 'yes')
      .field('lookingFor', 'What type of work are you looking for?')
      .when(data => data.hasJob === 'no')
      .build({ llmBackend: mockLLM })

    const conversation = new Conversation(gatherer.getMeta(), { llmBackend: mockLLM })
    
    // Start with employment status
    await conversation.processUserResponse('yes')
    
    // Should now ask about job-related fields
    let nextField = conversation.getNextField()
    expect(nextField?.name).toBe('jobTitle')
    
    await conversation.processUserResponse('Software Engineer')
    
    nextField = conversation.getNextField()
    expect(nextField?.name).toBe('employer')
    
    await conversation.processUserResponse('Tech Corp')
    
    // Should be done now (lookingFor field shouldn't be visible)
    nextField = conversation.getNextField()
    expect(nextField).toBeNull()
    
    const data = conversation.getCurrentData()
    expect(data.hasJob).toBe('yes')
    expect(data.jobTitle).toBe('Software Engineer')
    expect(data.employer).toBe('Tech Corp')
    expect(data.lookingFor).toBeUndefined()
  })

  test('should generate comprehensive conversation summary', () => {
    const gatherer = chatfield()
      .field('project', 'Your project name')
      .field('description', 'A very long project description that should be truncated in the summary')
      .build()

    const conversation = new Conversation(gatherer.getMeta())
    const data = conversation.getCurrentData()
    
    data.project = 'My Awesome Project'
    data.description = 'This is a very long description that goes on and on and should definitely be truncated when displayed in the summary because it exceeds the character limit'
    
    const summary = conversation.getConversationSummary()
    
    expect(summary).toContain('Collected so far:')
    expect(summary).toContain('Your project name: My Awesome Project')
    expect(summary).toContain('A very long project description')
    expect(summary).toContain('...') // Should be truncated
    expect(summary.length).toBeLessThan(500) // Should be reasonable length
  })
})