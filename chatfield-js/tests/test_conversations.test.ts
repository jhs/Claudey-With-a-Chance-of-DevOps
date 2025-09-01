/**
 * Test conversation flow and state management.
 * Mirrors Python's test_conversations.py
 */

import { chatfield } from '../src/builders/gatherer-builder'
import { Interviewer } from '../src/core/interviewer'
import { MockLLMBackend } from '../src/backends/llm-backend'

describe('TestConversationBasics', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    mockLLM.addValidationResponse('VALID')
  })

  test('test_conversation_initialization', async () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    // Start conversation
    const message = await interviewer.go(null)
    
    expect(message).toBeDefined()
    expect(typeof message).toBe('string')
    expect(message.length).toBeGreaterThan(0)
  })

  test('test_conversation_with_user_input', async () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    // Start conversation
    await interviewer.go(null)

    // Provide user input
    const response = await interviewer.go('John Doe')
    
    expect(response).toBeDefined()
    expect(interview.name).toBeDefined()
  })

  test('test_multi_field_conversation', async () => {
    const interview = chatfield()
      .type('MultiFieldInterview')
      .field('name').desc('Your name')
      .field('email').desc('Your email')
      .field('phone').desc('Your phone')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    // Start conversation
    await interviewer.go(null)

    // Provide responses for each field
    await interviewer.go('John Doe')
    await interviewer.go('john@example.com')
    await interviewer.go('555-1234')

    // Check all fields were collected
    expect(interview._done).toBe(true)
  })
})

describe('TestConversationValidation', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
  })

  test('test_validation_failure_and_retry', async () => {
    const interview = chatfield()
      .type('ValidatedInterview')
      .field('email')
        .desc('Your email')
        .must('valid email format')
        .reject('temporary emails')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    // First validation fails
    mockLLM.addValidationResponse('Invalid email format')
    
    await interviewer.go(null)
    const failResponse = await interviewer.go('notanemail')
    expect(failResponse).toContain('Invalid')

    // Second validation succeeds
    mockLLM.addValidationResponse('VALID')
    const successResponse = await interviewer.go('john@example.com')
    
    expect(interview.email).toBe('john@example.com')
  })

  test('test_multiple_validation_rules', async () => {
    const interview = chatfield()
      .type('StrictInterview')
      .field('password')
        .desc('Create a password')
        .must('at least 8 characters')
        .must('include numbers')
        .must('include special characters')
        .reject('common passwords')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    mockLLM.addValidationResponse('VALID')
    
    await interviewer.go(null)
    await interviewer.go('SecureP@ss123')
    
    expect(interview.password).toBe('SecureP@ss123')
  })
})

describe('TestConversationWithRoles', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    mockLLM.addValidationResponse('VALID')
  })

  test('test_conversation_with_alice_bob_roles', async () => {
    const interview = chatfield()
      .type('RoleBasedInterview')
      .alice()
        .type('Technical Interviewer')
        .trait('asks detailed questions')
      .bob()
        .type('Senior Developer')
        .trait('experienced in Python')
      .field('experience').desc('Your experience with Python')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    const systemPrompt = interviewer.mk_system_prompt({ interview })
    
    expect(systemPrompt).toContain('Technical Interviewer')
    expect(systemPrompt).toContain('Senior Developer')
    expect(systemPrompt).toContain('asks detailed questions')
    expect(systemPrompt).toContain('experienced in Python')
  })
})

describe('TestConversationWithTransformations', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    mockLLM.addValidationResponse('VALID')
  })

  test('test_conversation_with_type_transformations', async () => {
    const interview = chatfield()
      .type('TypedInterview')
      .field('age')
        .desc('Your age')
        .as_int()
      .field('salary')
        .desc('Expected salary')
        .as_float()
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    // Simulate tool responses with transformations
    interviewer.process_tool_input(interview, {
      age: {
        value: 'thirty',
        context: 'User said thirty',
        as_quote: 'I am thirty years old',
        as_int: 30
      }
    })

    interviewer.process_tool_input(interview, {
      salary: {
        value: 'seventy-five thousand',
        context: 'User mentioned salary',
        as_quote: 'Looking for 75k',
        as_float: 75000.0
      }
    })

    expect(interview.age).toBe('thirty')
    expect(interview.age.as_int).toBe(30)
    expect(interview.salary).toBe('seventy-five thousand')
    expect(interview.salary.as_float).toBe(75000.0)
  })

  test('test_conversation_with_language_transformations', async () => {
    const interview = chatfield()
      .type('MultilingualInterview')
      .field('greeting')
        .desc('Say hello')
        .as_lang.fr()
        .as_lang.es()
        .as_lang.de()
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    interviewer.process_tool_input(interview, {
      greeting: {
        value: 'hello',
        context: 'User greeting',
        as_quote: 'Hello there',
        as_lang_fr: 'bonjour',
        as_lang_es: 'hola',
        as_lang_de: 'hallo'
      }
    })

    expect(interview.greeting).toBe('hello')
    expect(interview.greeting.as_lang_fr).toBe('bonjour')
    expect(interview.greeting.as_lang_es).toBe('hola')
    expect(interview.greeting.as_lang_de).toBe('hallo')
  })
})

describe('TestConversationWithChoices', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    mockLLM.addValidationResponse('VALID')
  })

  test('test_conversation_with_single_choice', async () => {
    const interview = chatfield()
      .type('ChoiceInterview')
      .field('color')
        .desc('Favorite color')
        .as_one.color('red', 'green', 'blue')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    interviewer.process_tool_input(interview, {
      color: {
        value: 'blue',
        context: 'User selected blue',
        as_quote: 'I like blue',
        as_one_color: 'blue'
      }
    })

    expect(interview.color).toBe('blue')
    expect(interview.color.as_one_color).toBe('blue')
  })

  test('test_conversation_with_multiple_choices', async () => {
    const interview = chatfield()
      .type('MultiChoiceInterview')
      .field('languages')
        .desc('Programming languages you know')
        .as_multi.languages('python', 'javascript', 'rust', 'go')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    interviewer.process_tool_input(interview, {
      languages: {
        value: 'python and javascript',
        context: 'User knows multiple languages',
        as_quote: 'I work with Python and JavaScript',
        as_multi_languages: ['python', 'javascript']
      }
    })

    expect(interview.languages).toBe('python and javascript')
    expect(interview.languages.as_multi_languages).toEqual(['python', 'javascript'])
  })
})

describe('TestConversationState', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    mockLLM.addValidationResponse('VALID')
  })

  test('test_conversation_state_progression', async () => {
    const interview = chatfield()
      .type('ProgressiveInterview')
      .field('field1').desc('First field')
      .field('field2').desc('Second field')
      .field('field3').desc('Third field')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    // Initially not done
    expect(interview._done).toBe(false)

    // Collect field1
    interviewer.process_tool_input(interview, {
      field1: { value: 'value1', context: 'N/A', as_quote: 'value1' }
    })
    expect(interview._done).toBe(false)

    // Collect field2
    interviewer.process_tool_input(interview, {
      field2: { value: 'value2', context: 'N/A', as_quote: 'value2' }
    })
    expect(interview._done).toBe(false)

    // Collect field3
    interviewer.process_tool_input(interview, {
      field3: { value: 'value3', context: 'N/A', as_quote: 'value3' }
    })
    expect(interview._done).toBe(true)
  })

  test('test_conversation_checkpointing', async () => {
    const interview1 = chatfield()
      .type('CheckpointInterview')
      .field('name').desc('Your name')
      .build()
    
    const interview2 = chatfield()
      .type('CheckpointInterview')
      .field('name').desc('Your name')
      .build()

    const interviewer1 = new Interviewer(interview1, { 
      threadId: 'thread-1',
      llmBackend: mockLLM 
    })
    
    const interviewer2 = new Interviewer(interview2, { 
      threadId: 'thread-2',
      llmBackend: mockLLM 
    })

    // Each should have independent state
    expect(interviewer1.config.configurable.thread_id).toBe('thread-1')
    expect(interviewer2.config.configurable.thread_id).toBe('thread-2')
    
    // Update one shouldn't affect the other
    interviewer1.process_tool_input(interview1, {
      name: { value: 'Alice', context: 'N/A', as_quote: 'Alice' }
    })
    
    expect(interview1.name).toBe('Alice')
    expect(interview2.name).toBeNull()
  })
})