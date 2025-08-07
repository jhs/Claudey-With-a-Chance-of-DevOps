/**
 * React integration examples using decorator-based gatherers
 */

import React, { useState } from 'react'
import { gather, field, must, reject, hint, user, agent } from '../src'
import { ConversationInterface, FormInterface } from '../src'
import { useConversation } from '../src'

// Define gatherers with decorators
@gather
@user("startup founder")
@agent("be patient and encouraging")
class StartupPitch {
  @field("What's your startup idea?")
  @must("include target problem")
  @hint("Describe the problem you're solving and for whom")
  idea!: string

  @field("Who is your target customer?")
  @must("specific demographic or market")
  @hint("Be as specific as possible about your ideal customer")
  customer!: string

  @field("How big is the market opportunity?")
  @must("market size estimate")
  @hint("Research TAM, SAM, or SOM if possible")
  market_size!: string

  @field("What makes you uniquely qualified to solve this?")
  @must("personal experience or expertise")
  @hint("What's your unfair advantage or unique insight?")
  expertise!: string
}

@gather
@user("team member")
@agent("supportive and constructive")
class TeamFeedback {
  @field("How would you rate this week's sprint?")
  @must("rating from 1-10")
  @hint("Consider velocity, quality, and team collaboration")
  sprint_rating!: string

  @field("What went well this week?")
  @hint("Highlights, achievements, good processes")
  went_well!: string

  @field("What could be improved?")
  @hint("Bottlenecks, process issues, or blockers")
  improvements!: string

  @field("Do you have any blockers for next week?")
  @hint("Dependencies, resource needs, or technical challenges")
  blockers!: string
}

@gather
@user("customer")
@agent("empathetic and solution-focused")
class SupportTicket {
  @field("What issue are you experiencing?")
  @must("clear description of the problem")
  @hint("Describe what's not working as expected")
  issue!: string

  @field("When did this issue start?")
  @must("timeframe")
  @hint("Today, this week, after a recent change, etc.")
  started!: string

  @field("How is this impacting your work?")
  @must("impact description")
  @hint("Critical blocker, minor inconvenience, etc.")
  impact!: string

  @field("What have you tried so far?")
  @hint("Any troubleshooting steps or workarounds attempted")
  attempted!: string
}

// React component using conversational interface
export function StartupPitchChat() {
  const [pitchData, setPitchData] = useState<any>(null)
  
  if (pitchData) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <h2 className="text-2xl font-bold mb-4">Your Startup Pitch</h2>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
          <div><strong>Idea:</strong> {pitchData.idea}</div>
          <div><strong>Target Customer:</strong> {pitchData.customer}</div>
          <div><strong>Market Size:</strong> {pitchData.market_size}</div>
          <div><strong>Your Expertise:</strong> {pitchData.expertise}</div>
        </div>
        <button 
          onClick={() => setPitchData(null)}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Start Over
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Tell Us About Your Startup</h2>
      <ConversationInterface
        gatherer={StartupPitch as any}
        onComplete={(data) => setPitchData(data)}
        className="h-96"
      />
    </div>
  )
}

// React component using form interface
export function TeamFeedbackForm() {
  const [feedbackData, setFeedbackData] = useState<any>(null)
  
  if (feedbackData) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <h2 className="text-2xl font-bold mb-4">Sprint Feedback Submitted</h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
          <div><strong>Sprint Rating:</strong> {feedbackData.sprint_rating}/10</div>
          <div><strong>What Went Well:</strong> {feedbackData.went_well}</div>
          <div><strong>Improvements:</strong> {feedbackData.improvements}</div>
          <div><strong>Blockers:</strong> {feedbackData.blockers}</div>
        </div>
        <button 
          onClick={() => setFeedbackData(null)}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Submit Another
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Sprint Feedback</h2>
      <FormInterface
        gatherer={TeamFeedback as any}
        onComplete={(data) => setFeedbackData(data)}
      />
    </div>
  )
}

// Hook-based usage example
export function SupportTicketHook() {
  const [state, actions] = useConversation(SupportTicket as any, {
    onComplete: (instance) => {
      console.log('Support ticket created:', instance.getData())
      // Send to support system
    },
    onError: (error) => {
      console.error('Error creating ticket:', error)
    }
  })

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Create Support Ticket</h2>
      
      {/* Progress indicator */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span>{Math.round(state.progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${state.progress}%` }}
          />
        </div>
      </div>

      {/* Messages */}
      <div className="border rounded-lg mb-4 h-64 overflow-y-auto p-4 space-y-3">
        {state.messages.map((message, index) => (
          <div key={index} className={`flex ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}>
            <div className={`max-w-xs px-3 py-2 rounded-lg ${
              message.role === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {message.content}
            </div>
          </div>
        ))}
        
        {state.isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-3 py-2">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Validation error */}
      {state.validationError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
          <div className="text-red-800 text-sm">{state.validationError}</div>
        </div>
      )}

      {/* Input */}
      <div className="flex space-x-2">
        <input
          type="text"
          placeholder={state.currentField ? `Answer: ${state.currentField.description}` : "Type your response..."}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={!state.isWaitingForUser || state.isLoading}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && e.currentTarget.value.trim()) {
              actions.sendMessage(e.currentTarget.value.trim())
              e.currentTarget.value = ''
            }
          }}
        />
        <button
          onClick={() => {
            const input = document.querySelector('input') as HTMLInputElement
            if (input && input.value.trim()) {
              actions.sendMessage(input.value.trim())
              input.value = ''
            }
          }}
          disabled={!state.isWaitingForUser || state.isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400"
        >
          Send
        </button>
      </div>

      {state.currentField?.hint && (
        <div className="mt-2 text-sm text-gray-600 bg-blue-50 p-2 rounded">
          💡 {state.currentField.hint}
        </div>
      )}

      {/* Completion state */}
      {state.isComplete && (
        <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-800 mb-2">Support Ticket Created!</h3>
          <p className="text-green-600">Your ticket has been submitted and you'll hear back from our team soon.</p>
          <button
            onClick={actions.reset}
            className="mt-3 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Create Another Ticket
          </button>
        </div>
      )}
    </div>
  )
}

// Multi-step example
export function MultiStepOnboarding() {
  const gatherers = [
    StartupPitch as any,
    TeamFeedback as any,
    SupportTicket as any
  ]
  
  // This would use useMultiStepGatherer hook
  // Implementation depends on specific requirements
  
  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">Multi-Step Onboarding</h2>
      <p className="text-gray-600">
        This would step through multiple gatherers in sequence.
        See the useMultiStepGatherer hook for implementation details.
      </p>
    </div>
  )
}

// App component showing all examples
export function DecoratorExamplesApp() {
  const [currentExample, setCurrentExample] = useState<string>('pitch')
  
  const examples = [
    { key: 'pitch', label: 'Startup Pitch Chat', component: StartupPitchChat },
    { key: 'feedback', label: 'Team Feedback Form', component: TeamFeedbackForm },
    { key: 'support', label: 'Support Ticket Hook', component: SupportTicketHook },
    { key: 'multi', label: 'Multi-Step Onboarding', component: MultiStepOnboarding }
  ]
  
  const CurrentComponent = examples.find(ex => ex.key === currentExample)?.component || StartupPitchChat
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <h1 className="text-xl font-bold mb-3">Chatfield Decorator Examples</h1>
          <div className="flex space-x-4">
            {examples.map(example => (
              <button
                key={example.key}
                onClick={() => setCurrentExample(example.key)}
                className={`px-3 py-1 rounded text-sm ${
                  currentExample === example.key
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                {example.label}
              </button>
            ))}
          </div>
        </div>
      </nav>
      
      {/* Content */}
      <main className="py-8">
        <CurrentComponent />
      </main>
    </div>
  )
}

export default DecoratorExamplesApp