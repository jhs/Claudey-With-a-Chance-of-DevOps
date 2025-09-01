/**
 * Tests for the Interviewer class equivalent functionality.
 * Mirrors Python's test_interviewer.py
 */

import { chatfield } from '../src/builders/gatherer-builder'
import { Interviewer } from '../src/core/interviewer'
import { MockLLMBackend } from '../src/backends/llm-backend'

describe('TestInterviewerBasics', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
  })

  test('test_interviewer_initialization', () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .field('email').desc('Your email')
      .build()
    const interviewer = new Interviewer(interview)

    expect(interviewer.interview).toBe(interview)
    expect(interviewer.config.configurable.thread_id).toBeDefined()
    expect(interviewer.checkpointer).toBeDefined()
    expect(interviewer.graph).toBeDefined()
  })

  test('test_interviewer_with_custom_thread_id', () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()
    const interviewer = new Interviewer(interview, { threadId: 'custom-123' })

    expect(interviewer.config.configurable.thread_id).toBe('custom-123')
  })

  test('test_llm_initialization', () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    expect(interviewer.llm).toBe(mockLLM)
  })
})

describe('TestSystemPromptGeneration', () => {
  test('test_basic_system_prompt', () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .desc('Customer feedback form')
      .field('rating').desc('Overall satisfaction rating')
      .field('comments').desc('Additional comments')
      .build()
    const interviewer = new Interviewer(interview)

    const prompt = interviewer.mk_system_prompt({ interview })

    expect(prompt).toContain('Customer feedback form')
    expect(prompt).toContain('rating: Overall satisfaction rating')
    expect(prompt).toContain('comments: Additional comments')
    expect(prompt).toContain('Agent') // Default role
    expect(prompt).toContain('User') // Default role
  })

  test('test_system_prompt_with_roles', () => {
    const interview = chatfield()
      .type('SupportInterview')
      .desc('Support ticket')
      .alice()
        .type('Customer Support Agent')
        .trait('Friendly and helpful')
      .bob()
        .type('Frustrated Customer')
        .trait('Had a bad experience')
      .field('issue').desc('What went wrong')
      .build()
    const interviewer = new Interviewer(interview)

    const prompt = interviewer.mk_system_prompt({ interview })

    expect(prompt).toContain('Customer Support Agent')
    expect(prompt).toContain('Frustrated Customer')
    expect(prompt).toContain('Friendly and helpful')
    expect(prompt).toContain('Had a bad experience')
  })

  test('test_system_prompt_with_validation', () => {
    const interview = chatfield()
      .type('ValidatedInterview')
      .field('feedback')
        .desc('Your feedback')
        .must('specific details')
        .reject('profanity')
        .hint('Be constructive')
      .build()
    const interviewer = new Interviewer(interview)

    const prompt = interviewer.mk_system_prompt({ interview })

    expect(prompt).toContain('Must: specific details')
    expect(prompt).toContain('Reject: profanity')
    // Note: Hints may or may not appear in system prompt
  })
})

describe('TestToolGeneration', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
  })

  test('test_tool_creation', () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .field('field1').desc('Field 1')
      .field('field2').desc('Field 2')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    // Tool should be bound to LLM
    expect(interviewer.llm_with_both).toBeDefined()
    expect(typeof interviewer.llm_with_both.bind_tools).toBe('function')
  })

  test('test_tool_with_transformations', () => {
    const interview = chatfield()
      .type('TypedInterview')
      .field('number')
        .desc('A number')
        .as_int()
        .as_bool()
        .as_lang.fr()
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    // Tool args should include transformations
    expect(interviewer.llm_with_both).toBeDefined()
  })
})

describe('TestConversationFlow', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    mockLLM.addValidationResponse('VALID')
  })

  test('test_go_method_basic', async () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()
    const interviewer = new Interviewer(interview, { llmBackend: mockLLM })

    // Start conversation
    const aiMessage = await interviewer.go(null)

    expect(aiMessage).toBeDefined()
    expect(typeof aiMessage).toBe('string')
    expect(aiMessage.length).toBeGreaterThan(0)
  })

  test('test_interview_state_updates', () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()
    const interviewer = new Interviewer(interview)

    // Manually update field as if tool was called
    interviewer.process_tool_input(interview, {
      name: {
        value: 'Test User',
        context: 'User provided their name',
        as_quote: 'My name is Test User'
      }
    })

    // Check interview was updated
    expect(interview._chatfield.fields.name.value).toBeDefined()
    expect(interview._chatfield.fields.name.value.value).toBe('Test User')
  })

  test('test_done_detection', () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .field('field1').desc('Field 1')
      .field('field2').desc('Field 2')
      .build()
    const interviewer = new Interviewer(interview)

    // Initially not done
    expect(interview._done).toBe(false)

    // Set both fields
    interviewer.process_tool_input(interview, {
      field1: { value: 'value1', context: 'N/A', as_quote: 'value1' }
    })
    interviewer.process_tool_input(interview, {
      field2: { value: 'value2', context: 'N/A', as_quote: 'value2' }
    })

    // Should be done
    expect(interview._done).toBe(true)
  })
})

describe('TestInterviewerWithFeatures', () => {
  test('test_interviewer_with_all_features', () => {
    const interview = chatfield()
      .type('ComplexInterview')
      .desc('Complex interview')
      .alice()
        .type('Interviewer')
        .trait('Professional')
      .bob()
        .type('Candidate')
      .field('years')
        .desc('Years of experience')
        .must('specific answer')
        .reject('vague response')
        .hint('Think carefully')
        .as_int()
        .as_bool.positive('True if positive')
      .build()
    const interviewer = new Interviewer(interview)

    // System prompt should include all features
    const prompt = interviewer.mk_system_prompt({ interview })

    expect(prompt).toContain('Interviewer')
    expect(prompt).toContain('Candidate')
    expect(prompt).toContain('Professional')
    expect(prompt).toContain('Years of experience')
  })

  test('test_process_tool_input_with_transformations', () => {
    const interview = chatfield()
      .type('TypedInterview')
      .field('number')
        .desc('A number')
        .as_int()
        .as_lang.fr()
      .build()
    const interviewer = new Interviewer(interview)

    // Process tool input with transformations
    interviewer.process_tool_input(interview, {
      number: {
        value: 'five',
        context: 'User said five',
        as_quote: 'The answer is five',
        choose_exactly_one_as_int: 5, // Note: Tool prefixes with choose_
        choose_exactly_one_as_lang_fr: 'cinq'
      }
    })

    // Check the field was updated with renamed keys
    const fieldValue = interview._chatfield.fields.number.value
    expect(fieldValue.value).toBe('five')
    expect(fieldValue.as_one_as_int).toBe(5) // Renamed from choose_exactly_one_
    expect(fieldValue.as_one_as_lang_fr).toBe('cinq')
  })
})

describe('TestInterviewerEdgeCases', () => {
  test('test_empty_interview', () => {
    const interview = chatfield()
      .type('EmptyInterview')
      .desc('Empty interview')
      .build()
    const interviewer = new Interviewer(interview)

    // Should handle empty interview gracefully
    expect(interview._done).toBe(true)
  })

  test('test_interview_copy_from', () => {
    const interview1 = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()
    const interview2 = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()

    // Set field in interview2
    interview2._chatfield.fields.name.value = {
      value: 'Test',
      context: 'N/A',
      as_quote: 'Test'
    }

    // Copy from interview2 to interview1
    interview1._copy_from(interview2)

    // Check the copy worked
    expect(interview1._chatfield.fields.name.value).toBeDefined()
    expect(interview1._chatfield.fields.name.value.value).toBe('Test')

    // Ensure it's a deep copy
    interview2._chatfield.fields.name.value.value = 'Changed'
    expect(interview1._chatfield.fields.name.value.value).toBe('Test')
  })

  test('test_thread_isolation', () => {
    const interview1 = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()
    const interview2 = chatfield()
      .type('SimpleInterview')
      .field('name').desc('Your name')
      .build()

    const interviewer1 = new Interviewer(interview1, { threadId: 'thread-1' })
    const interviewer2 = new Interviewer(interview2, { threadId: 'thread-2' })

    expect(interviewer1.config.configurable.thread_id).toBe('thread-1')
    expect(interviewer2.config.configurable.thread_id).toBe('thread-2')
    expect(interviewer1.config).not.toBe(interviewer2.config)
  })
})