/**
 * React integration tests for Chatfield
 * Tests React hooks, components, and CopilotKit integration
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { renderHook, act } from '@testing-library/react-hooks'
import { chatfield } from '../../src/builders/gatherer-builder'
import { useGatherer, GathererProvider } from '../../src/integrations/react'
import { ChatfieldSidebar } from '../../src/integrations/copilotkit'
import { MockLLMBackend } from '../../src/backends/llm-backend'

describe('React Integration Tests', () => {
  let mockLLM: MockLLMBackend

  beforeEach(() => {
    mockLLM = new MockLLMBackend()
    mockLLM.addValidationResponse('VALID')
  })

  describe('useGatherer Hook', () => {
    test('should initialize with empty data', () => {
      const gatherer = chatfield()
        .field('name', 'Your name')
        .field('email', 'Your email')
        .build({ llmBackend: mockLLM })

      const { result } = renderHook(() => useGatherer(gatherer))

      expect(result.current.isComplete).toBe(false)
      expect(result.current.data).toEqual({})
      expect(result.current.currentField).toBe('name')
    })

    test('should track field completion', async () => {
      const gatherer = chatfield()
        .field('name', 'Your name')
        .build({ llmBackend: mockLLM })

      const { result } = renderHook(() => useGatherer(gatherer))

      await act(async () => {
        await result.current.submitResponse('John Doe')
      })

      expect(result.current.data.name).toBe('John Doe')
      expect(result.current.isComplete).toBe(true)
    })

    test('should handle validation errors', async () => {
      mockLLM.reset()
      mockLLM.addValidationResponse('Invalid email format')
      
      const gatherer = chatfield()
        .field('email', 'Your email')
        .must('valid email format')
        .build({ llmBackend: mockLLM })

      const { result } = renderHook(() => useGatherer(gatherer))

      await act(async () => {
        await result.current.submitResponse('notanemail')
      })

      expect(result.current.error).toContain('Invalid')
      expect(result.current.data.email).toBeUndefined()
    })

    test('should handle conditional fields', async () => {
      const gatherer = chatfield()
        .field('hasJob', 'Are you employed?')
        .field('jobTitle', 'Your job title')
        .when(data => data.hasJob === 'yes')
        .build({ llmBackend: mockLLM })

      const { result } = renderHook(() => useGatherer(gatherer))

      // Initially should ask about employment
      expect(result.current.currentField).toBe('hasJob')

      // Answer no - should complete without asking job title
      await act(async () => {
        await result.current.submitResponse('no')
      })

      expect(result.current.isComplete).toBe(true)
      expect(result.current.data.jobTitle).toBeUndefined()
    })
  })

  describe('GathererProvider Component', () => {
    test('should provide gatherer context to children', () => {
      const gatherer = chatfield()
        .field('name', 'Your name')
        .build({ llmBackend: mockLLM })

      const TestComponent = () => {
        const { currentField } = useGatherer(gatherer)
        return <div>Current field: {currentField}</div>
      }

      render(
        <GathererProvider gatherer={gatherer}>
          <TestComponent />
        </GathererProvider>
      )

      expect(screen.getByText('Current field: name')).toBeInTheDocument()
    })

    test('should handle nested providers', () => {
      const gatherer1 = chatfield()
        .field('field1', 'Field 1')
        .build({ llmBackend: mockLLM })

      const gatherer2 = chatfield()
        .field('field2', 'Field 2')
        .build({ llmBackend: mockLLM })

      const TestComponent1 = () => {
        const { currentField } = useGatherer(gatherer1)
        return <div>Gatherer 1: {currentField}</div>
      }

      const TestComponent2 = () => {
        const { currentField } = useGatherer(gatherer2)
        return <div>Gatherer 2: {currentField}</div>
      }

      render(
        <GathererProvider gatherer={gatherer1}>
          <TestComponent1 />
          <GathererProvider gatherer={gatherer2}>
            <TestComponent2 />
          </GathererProvider>
        </GathererProvider>
      )

      expect(screen.getByText('Gatherer 1: field1')).toBeInTheDocument()
      expect(screen.getByText('Gatherer 2: field2')).toBeInTheDocument()
    })
  })

  describe('CopilotKit Integration', () => {
    test('should render ChatfieldSidebar component', () => {
      const gatherer = chatfield()
        .field('name', 'Your name')
        .build({ llmBackend: mockLLM })

      const onComplete = jest.fn()

      render(
        <ChatfieldSidebar 
          gatherer={gatherer}
          onComplete={onComplete}
        />
      )

      // Should render the sidebar
      expect(screen.getByRole('complementary')).toBeInTheDocument()
    })

    test('should call onComplete when all fields collected', async () => {
      const gatherer = chatfield()
        .field('name', 'Your name')
        .build({ llmBackend: mockLLM })

      const onComplete = jest.fn()

      const { container } = render(
        <ChatfieldSidebar 
          gatherer={gatherer}
          onComplete={onComplete}
        />
      )

      // Simulate user completing the field
      const input = container.querySelector('input')
      if (input) {
        fireEvent.change(input, { target: { value: 'John Doe' } })
        fireEvent.submit(input.closest('form')!)
      }

      await waitFor(() => {
        expect(onComplete).toHaveBeenCalledWith({
          name: 'John Doe'
        })
      })
    })

    test('should display conversation history', async () => {
      const gatherer = chatfield()
        .field('name', 'Your name')
        .field('email', 'Your email')
        .build({ llmBackend: mockLLM })

      render(
        <ChatfieldSidebar 
          gatherer={gatherer}
          onComplete={() => {}}
        />
      )

      // Should show the first field question
      await waitFor(() => {
        expect(screen.getByText(/Your name/)).toBeInTheDocument()
      })
    })

    test('should handle multi-step conversations', async () => {
      const gatherer = chatfield()
        .field('name', 'Your name')
        .field('email', 'Your email')
        .field('message', 'Your message')
        .build({ llmBackend: mockLLM })

      const onComplete = jest.fn()

      const { container } = render(
        <ChatfieldSidebar 
          gatherer={gatherer}
          onComplete={onComplete}
        />
      )

      // Complete first field
      let input = container.querySelector('input')
      if (input) {
        fireEvent.change(input, { target: { value: 'John Doe' } })
        fireEvent.submit(input.closest('form')!)
      }

      // Should move to second field
      await waitFor(() => {
        expect(screen.getByText(/Your email/)).toBeInTheDocument()
      })

      // Complete second field
      input = container.querySelector('input')
      if (input) {
        fireEvent.change(input, { target: { value: 'john@example.com' } })
        fireEvent.submit(input.closest('form')!)
      }

      // Should move to third field
      await waitFor(() => {
        expect(screen.getByText(/Your message/)).toBeInTheDocument()
      })

      // Complete third field
      input = container.querySelector('input')
      if (input) {
        fireEvent.change(input, { target: { value: 'Hello world' } })
        fireEvent.submit(input.closest('form')!)
      }

      // Should call onComplete with all data
      await waitFor(() => {
        expect(onComplete).toHaveBeenCalledWith({
          name: 'John Doe',
          email: 'john@example.com',
          message: 'Hello world'
        })
      })
    })
  })

  describe('React Component Rendering', () => {
    test('should render conversation UI with current question', () => {
      const gatherer = chatfield()
        .field('name', 'What is your full name?')
        .field('email', 'What is your email address?')
        .build({ llmBackend: mockLLM })

      const ConversationUI = ({ gatherer }: { gatherer: any }) => {
        const { currentField, getCurrentQuestion } = useGatherer(gatherer)
        
        return (
          <div>
            <h2>Current Field: {currentField}</h2>
            <p>{getCurrentQuestion()}</p>
          </div>
        )
      }

      render(
        <GathererProvider gatherer={gatherer}>
          <ConversationUI gatherer={gatherer} />
        </GathererProvider>
      )

      expect(screen.getByText('Current Field: name')).toBeInTheDocument()
      expect(screen.getByText('What is your full name?')).toBeInTheDocument()
    })

    test('should show completion state', async () => {
      const gatherer = chatfield()
        .field('name', 'Your name')
        .build({ llmBackend: mockLLM })

      const CompletionUI = ({ gatherer }: { gatherer: any }) => {
        const { isComplete, data } = useGatherer(gatherer)
        
        if (isComplete) {
          return <div>Thank you, {data.name}!</div>
        }
        
        return <div>Please complete the form</div>
      }

      const { rerender } = render(
        <GathererProvider gatherer={gatherer}>
          <CompletionUI gatherer={gatherer} />
        </GathererProvider>
      )

      expect(screen.getByText('Please complete the form')).toBeInTheDocument()

      // Simulate completion
      gatherer._chatfield.fields.name.value = {
        value: 'John',
        context: 'User provided name',
        as_quote: 'John'
      }

      rerender(
        <GathererProvider gatherer={gatherer}>
          <CompletionUI gatherer={gatherer} />
        </GathererProvider>
      )

      await waitFor(() => {
        expect(screen.getByText('Thank you, John!')).toBeInTheDocument()
      })
    })

    test('should handle streaming responses', async () => {
      const gatherer = chatfield()
        .field('story', 'Tell me a story')
        .build({ llmBackend: mockLLM })

      const StreamingUI = ({ gatherer }: { gatherer: any }) => {
        const { streamingResponse, isStreaming } = useGatherer(gatherer)
        
        return (
          <div>
            {isStreaming && <span>Loading...</span>}
            <p>{streamingResponse}</p>
          </div>
        )
      }

      render(
        <GathererProvider gatherer={gatherer}>
          <StreamingUI gatherer={gatherer} />
        </GathererProvider>
      )

      // Initially not streaming
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()

      // Simulate streaming response
      // This would be handled by the actual LLM backend in production
    })
  })
})