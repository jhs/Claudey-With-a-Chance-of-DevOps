/**
 * React UI components for Chatfield conversations
 */

import React, { useState, useRef, useEffect } from 'react'
import { Gatherer } from '../core/gatherer'
import { useConversation, useControlledGatherer, ConversationState } from './react'
import { ConversationMessage } from '../core/types'

export interface ChatMessageProps {
  message: ConversationMessage
  isLatest?: boolean
}

export function ChatMessage({ message, isLatest }: ChatMessageProps) {
  const isAssistant = message.role === 'assistant'
  
  return (
    <div className={`flex ${isAssistant ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
        isAssistant 
          ? 'bg-gray-100 text-gray-800' 
          : 'bg-blue-500 text-white'
      }`}>
        <div className="whitespace-pre-wrap">{message.content}</div>
        {message.timestamp && (
          <div className={`text-xs mt-1 ${
            isAssistant ? 'text-gray-500' : 'text-blue-100'
          }`}>
            {message.timestamp.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  )
}

export interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
  hint?: string
}

export function ChatInput({ onSend, disabled, placeholder, hint }: ChatInputProps) {
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput('')
    }
  }

  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus()
    }
  }, [disabled])

  return (
    <div className="border-t bg-gray-50 p-4">
      {hint && (
        <div className="mb-2 text-sm text-gray-600 bg-blue-50 border-l-4 border-blue-200 p-2 rounded">
          💡 {hint}
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex space-x-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder || "Type your response..."}
          disabled={disabled}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  )
}

export interface ProgressBarProps {
  progress: number
  completedFields: number
  totalFields: number
}

export function ProgressBar({ progress, completedFields, totalFields }: ProgressBarProps) {
  return (
    <div className="bg-white border-b p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">
          Progress: {completedFields} of {totalFields} fields completed
        </span>
        <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}

export interface ValidationErrorProps {
  error: string
  onRetry?: () => void
}

export function ValidationError({ error, onRetry }: ValidationErrorProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <span className="text-red-400">⚠️</span>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm text-red-800">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export interface ConversationInterfaceProps {
  gatherer: Gatherer
  onComplete?: (data: any) => void
  onError?: (error: Error) => void
  className?: string
  showProgress?: boolean
}

export function ConversationInterface({ 
  gatherer, 
  onComplete, 
  onError,
  className = '',
  showProgress = true 
}: ConversationInterfaceProps) {
  const [state, actions] = useConversation(gatherer, {
    onComplete: (instance) => onComplete?.(instance.getData()),
    onError
  })

  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.messages.length])

  if (state.isComplete) {
    return (
      <div className={`flex flex-col items-center justify-center p-8 bg-green-50 border border-green-200 rounded-lg ${className}`}>
        <div className="text-green-600 text-4xl mb-4">✅</div>
        <h3 className="text-lg font-semibold text-green-800 mb-2">All Done!</h3>
        <p className="text-green-600 text-center mb-4">
          I've collected all the information needed. Thank you for your responses!
        </p>
        <button
          onClick={actions.reset}
          className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
        >
          Start Over
        </button>
      </div>
    )
  }

  return (
    <div className={`flex flex-col h-full bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {showProgress && (
        <ProgressBar 
          progress={state.progress}
          completedFields={state.completedFields}
          totalFields={state.totalFields}
        />
      )}
      
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {state.messages.map((message, index) => (
          <ChatMessage 
            key={index}
            message={message}
            isLatest={index === state.messages.length - 1}
          />
        ))}
        
        {state.isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        
        {state.validationError && (
          <ValidationError 
            error={state.validationError}
            onRetry={actions.retry}
          />
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input area */}
      <ChatInput
        onSend={actions.sendMessage}
        disabled={state.isLoading || !state.isWaitingForUser}
        placeholder={
          state.currentField 
            ? `Answer: ${state.currentField.description}`
            : "Type your response..."
        }
        hint={state.currentField?.hint}
      />
    </div>
  )
}

export interface FormInterfaceProps {
  gatherer: Gatherer
  onComplete?: (data: any) => void
  className?: string
}

export function FormInterface({ gatherer, onComplete, className = '' }: FormInterfaceProps) {
  const {
    currentField,
    currentFieldIndex,
    isComplete,
    collectedData,
    validationErrors,
    totalFields,
    progress,
    setValue,
    nextField,
    previousField,
    reset,
    complete,
    canGoNext,
    canGoPrevious,
    getFieldError,
    hasError
  } = useControlledGatherer(gatherer)

  const handleFieldChange = (value: string) => {
    if (currentField) {
      setValue(currentField.name, value)
    }
  }

  const handleNext = async () => {
    await nextField()
    
    if (currentFieldIndex + 1 >= totalFields) {
      const instance = complete()
      if (instance) {
        onComplete?.(instance.getData())
      }
    }
  }

  if (isComplete) {
    const instance = complete()
    return (
      <div className={`p-6 bg-green-50 border border-green-200 rounded-lg ${className}`}>
        <h3 className="text-lg font-semibold text-green-800 mb-4">Form Complete!</h3>
        <div className="space-y-2 mb-4">
          {Object.entries(collectedData).map(([key, value]) => (
            <div key={key} className="flex justify-between">
              <span className="font-medium text-gray-700">{key}:</span>
              <span className="text-gray-600">{value}</span>
            </div>
          ))}
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => onComplete?.(instance?.getData())}
            className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
          >
            Submit
          </button>
          <button
            onClick={reset}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
          >
            Start Over
          </button>
        </div>
      </div>
    )
  }

  if (!currentField) {
    return <div>Loading...</div>
  }

  return (
    <div className={`p-6 bg-white border border-gray-200 rounded-lg ${className}`}>
      {/* Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">
            Step {currentFieldIndex + 1} of {totalFields}
          </h2>
          <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Current field */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {currentField.description}
        </label>
        
        {currentField.hint && (
          <p className="text-sm text-gray-500 mb-3">
            💡 {currentField.hint}
          </p>
        )}
        
        <textarea
          value={collectedData[currentField.name] || ''}
          onChange={(e) => handleFieldChange(e.target.value)}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            hasError(currentField.name) ? 'border-red-300' : 'border-gray-300'
          }`}
          rows={3}
          placeholder="Enter your response here..."
        />
        
        {hasError(currentField.name) && (
          <p className="mt-1 text-sm text-red-600">
            {getFieldError(currentField.name)}
          </p>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={previousField}
          disabled={!canGoPrevious}
          className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        
        <div className="flex space-x-2">
          <button
            onClick={reset}
            className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
          >
            Reset
          </button>
          
          <button
            onClick={handleNext}
            disabled={!canGoNext}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-blue-300 disabled:cursor-not-allowed"
          >
            {currentFieldIndex + 1 >= totalFields ? 'Complete' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  )
}

export interface FieldPreviewProps {
  gatherer: Gatherer
  className?: string
}

export function FieldPreview({ gatherer, className = '' }: FieldPreviewProps) {
  const preview = gatherer.getFieldPreview()
  
  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <h3 className="text-lg font-semibold mb-4">What we'll collect:</h3>
      <div className="space-y-3">
        {preview.map((field, index) => (
          <div key={field.name} className="flex items-start space-x-3">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">
              {index + 1}
            </span>
            <div className="flex-1">
              <h4 className="font-medium text-gray-900">{field.description}</h4>
              {field.hint && (
                <p className="text-sm text-gray-500 mt-1">💡 {field.hint}</p>
              )}
              {field.hasValidation && (
                <p className="text-xs text-blue-600 mt-1">✓ Has validation requirements</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}