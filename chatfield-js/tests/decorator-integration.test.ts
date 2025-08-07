/**
 * Integration tests for decorator-based gatherers
 */

import { gather, field, must, reject, hint, user, agent } from '../src/decorators'
import { MockLLMBackend } from '../src/backends/llm-backend'
import { Conversation } from '../src/core/conversation'

describe('Decorator Integration Tests', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    // Set up default valid responses
    mockLLM.addValidationResponse('VALID')
    mockLLM.addValidationResponse('VALID')
    mockLLM.addValidationResponse('VALID')
  })

  test('should complete full conversation with decorated gatherer', async () => {
    @gather
    @user("test user")
    @agent("be helpful")
    class TestForm {
      @field("Your name")
      @must("include full name")
      @hint("First and last name")
      name!: string

      @field("Your email")
      @must("valid email format")
      email!: string

      @field("Your message")
      message!: string
    }

    const meta = TestForm._chatfield_meta
    const conversation = new Conversation(meta, { llmBackend: mockLLM })

    // Track events
    const events: any[] = []
    conversation.setEventHandlers({
      onFieldStart: (field) => events.push({ type: 'start', field: field.name }),
      onFieldComplete: (field, value) => events.push({ type: 'complete', field: field.name, value }),
      onMessage: (message) => events.push({ type: 'message', role: message.role })
    })

    // Simulate responses
    await conversation.processUserResponse('John Smith')
    await conversation.processUserResponse('john@example.com')
    await conversation.processUserResponse('Hello, I need help')

    const data = conversation.getCurrentData()
    expect(data.name).toBe('John Smith')
    expect(data.email).toBe('john@example.com')
    expect(data.message).toBe('Hello, I need help')

    // Check that all fields were processed
    const completedFields = events.filter(e => e.type === 'complete')
    expect(completedFields).toHaveLength(3)
  })

  test('should handle validation failures', async () => {
    @gather
    class ValidatedForm {
      @field("Your email")
      @must("valid email format")
      @reject("temporary email providers")
      email!: string
    }

    // Set up validation responses: first fails, second succeeds
    mockLLM.reset()
    mockLLM.addValidationResponse('Please provide a valid email format')
    mockLLM.addValidationResponse('VALID')

    const meta = ValidatedForm._chatfield_meta
    const conversation = new Conversation(meta, { llmBackend: mockLLM })

    const validationErrors: string[] = []
    conversation.setEventHandlers({
      onValidationError: (field, error) => validationErrors.push(error)
    })

    // First attempt should fail
    const result1 = await conversation.processUserResponse('notanemail')
    expect(result1.success).toBe(false)
    expect(result1.needsRetry).toBe(true)
    expect(validationErrors).toHaveLength(1)

    // Second attempt should succeed
    const result2 = await conversation.processUserResponse('user@example.com')
    expect(result2.success).toBe(true)

    expect(conversation.getCurrentData().email).toBe('user@example.com')
  })

  test('should work with complex business form', async () => {
    @gather
    @user("entrepreneur")
    @agent("thorough and encouraging")
    class BusinessPlan {
      @field("Your business idea")
      @must("include target market")
      @must("describe the product")
      @hint("What problem are you solving and for whom?")
      idea!: string

      @field("Your target customers")
      @must("specific demographic")
      @reject("everyone")
      customers!: string

      @field("Your revenue model")
      @must("how you'll make money")
      revenue!: string
    }

    const meta = BusinessPlan._chatfield_meta
    
    // Verify metadata structure
    expect(meta.userContext).toEqual(['entrepreneur'])
    expect(meta.agentContext).toEqual(['thorough and encouraging'])
    expect(meta.getFieldNames()).toEqual(['idea', 'customers', 'revenue'])

    const conversation = new Conversation(meta, { llmBackend: mockLLM })

    // Simulate full conversation
    await conversation.processUserResponse('A SaaS platform for small businesses to manage inventory, targeting retail stores with 10-50 employees')
    await conversation.processUserResponse('Small retail business owners aged 30-55 who are tech-comfortable but not tech-savvy')
    await conversation.processUserResponse('Monthly subscription model with tiered pricing based on inventory size')

    const data = conversation.getCurrentData()
    expect(Object.keys(data)).toHaveLength(3)
    expect(data.idea).toContain('SaaS platform')
    expect(data.customers).toContain('retail business owners')
    expect(data.revenue).toContain('subscription model')
  })

  test('should provide field preview correctly', () => {
    @gather
    class PreviewTest {
      @field("Simple field")
      simple!: string

      @field("Validated field")
      @must("has validation")
      @hint("This has a hint")
      validated!: string

      @field("Complex field") 
      @must("rule 1")
      @must("rule 2")
      @reject("bad stuff")
      @hint("Complex hint")
      complex!: string
    }

    const preview = PreviewTest.getFieldPreview()
    expect(preview).toHaveLength(3)

    expect(preview[0]).toEqual({
      name: 'simple',
      description: 'Simple field', 
      hasValidation: false,
      hint: undefined
    })

    expect(preview[1]).toEqual({
      name: 'validated',
      description: 'Validated field',
      hasValidation: true,
      hint: 'This has a hint'
    })

    expect(preview[2]).toEqual({
      name: 'complex',
      description: 'Complex field',
      hasValidation: true,
      hint: 'Complex hint'
    })
  })

  test('should handle field order preservation', () => {
    @gather
    class OrderTest {
      @field("Third field")
      third!: string

      @field("First field") 
      first!: string

      @field("Second field")
      second!: string
    }

    const meta = OrderTest._chatfield_meta
    const fieldNames = meta.getFieldNames()
    
    // Should preserve definition order (based on decorator processing order)
    expect(fieldNames).toEqual(['third', 'first', 'second'])
  })

  test('should work without validation', async () => {
    @gather
    class SimpleForm {
      @field("Your name")
      name!: string

      @field("Your comment")
      comment!: string
    }

    const meta = SimpleForm._chatfield_meta
    const conversation = new Conversation(meta, { llmBackend: mockLLM })

    // Should accept any responses since no validation rules
    await conversation.processUserResponse('John')
    await conversation.processUserResponse('This is my comment')

    const data = conversation.getCurrentData()
    expect(data.name).toBe('John')
    expect(data.comment).toBe('This is my comment')
  })

  test('should handle empty responses appropriately', async () => {
    @gather
    class TestForm {
      @field("Required field")
      @must("not be empty")
      required!: string
    }

    const meta = TestForm._chatfield_meta
    const conversation = new Conversation(meta, { llmBackend: mockLLM })

    // Empty response should be rejected before validation
    const result = await conversation.processUserResponse('')
    expect(result.success).toBe(false)
    expect(result.needsRetry).toBe(true)
    expect(result.feedback).toContain('provide an answer')
  })

  test('should work with inline field options', async () => {
    @gather
    class InlineOptionsForm {
      @field("Your project description", {
        must: ["include timeline", "mention budget"],
        reject: ["vague statements"],
        hint: "Be specific about scope and resources"
      })
      project!: string
    }

    const meta = InlineOptionsForm._chatfield_meta
    const projectField = meta.getField('project')!

    expect(projectField.description).toBe('Your project description')
    expect(projectField.mustRules).toEqual(['include timeline', 'mention budget'])
    expect(projectField.rejectRules).toEqual(['vague statements'])
    expect(projectField.hint).toBe('Be specific about scope and resources')

    // Test actual conversation
    const conversation = new Conversation(meta, { llmBackend: mockLLM })
    await conversation.processUserResponse('A web application to manage tasks, launching in 3 months with a $50k budget')

    const data = conversation.getCurrentData()
    expect(data.project).toContain('web application')
  })

  test('should maintain class inheritance structure', () => {
    class BaseClass {
      baseMethod() {
        return 'base'
      }
    }

    @gather
    class ExtendedGatherer extends BaseClass {
      @field("Test field")
      test!: string
    }

    const instance = new ExtendedGatherer()
    expect(instance.baseMethod()).toBe('base')
    expect(typeof ExtendedGatherer.gather).toBe('function')
  })

  test('should work with React-style property initialization', () => {
    @gather
    class ReactStyleGatherer {
      @field("User input")
      @must("be descriptive")
      input: string = '' // React-style initialization

      @field("Optional field")
      optional?: string // Optional field
    }

    const meta = ReactStyleGatherer._chatfield_meta
    expect(meta.getFieldNames()).toEqual(['input', 'optional'])
    
    const inputField = meta.getField('input')!
    expect(inputField.mustRules).toEqual(['be descriptive'])
  })
})