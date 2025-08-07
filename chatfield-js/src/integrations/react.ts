/**
 * React hooks and utilities for Chatfield
 */

// React imports are optional - only used if React is available
let useState: any, useEffect: any, useCallback: any, useRef: any
try {
  const react = require('react')
  useState = react.useState
  useEffect = react.useEffect
  useCallback = react.useCallback
  useRef = react.useRef
} catch {
  // React not available - hooks will throw runtime errors
}
import { Gatherer, GathererInstance } from '../core/gatherer'
import { Conversation } from '../core/conversation'
import { ConversationMessage, CollectedData } from '../core/types'
import { FieldMeta } from '../core/metadata'

export interface UseConversationOptions {
  onComplete?: (instance: GathererInstance) => void
  onError?: (error: Error) => void
  onFieldChange?: (fieldName: string, value: string) => void
}

export interface ConversationState {
  // Conversation data
  messages: ConversationMessage[]
  collectedData: CollectedData
  currentField: FieldMeta | null
  isComplete: boolean
  
  // UI state
  isLoading: boolean
  isWaitingForUser: boolean
  validationError: string | null
  
  // Progress tracking
  totalFields: number
  completedFields: number
  progress: number // 0-100
}

export interface ConversationActions {
  sendMessage: (message: string) => Promise<void>
  retry: () => Promise<void>
  reset: () => void
  skipField: () => void
}

/**
 * Hook for managing conversation state and interactions
 */
export function useConversation(
  gatherer: Gatherer,
  options: UseConversationOptions = {}
): [ConversationState, ConversationActions] {
  
  const conversationRef = useRef<Conversation>()
  const [state, setState] = useState<ConversationState>(() => {
    const meta = gatherer.getMeta()
    const totalFields = meta.getFields().length
    
    return {
      messages: [],
      collectedData: {},
      currentField: null,
      isComplete: false,
      isLoading: false,
      isWaitingForUser: false,
      validationError: null,
      totalFields,
      completedFields: 0,
      progress: 0
    }
  })

  // Initialize conversation
  useEffect(() => {
    const conversation = new Conversation(gatherer.getMeta())
    conversationRef.current = conversation

    // Set up event handlers
    conversation.setEventHandlers({
      onMessage: (message) => {
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, message],
          isWaitingForUser: message.role === 'assistant',
          isLoading: false
        }))
      },
      
      onFieldStart: (field) => {
        setState(prev => ({
          ...prev,
          currentField: field,
          validationError: null,
          isWaitingForUser: true
        }))
      },
      
      onFieldComplete: (field, value) => {
        setState(prev => {
          const newCollectedData = { ...prev.collectedData, [field.name]: value }
          const completedCount = Object.keys(newCollectedData).length
          const progress = (completedCount / prev.totalFields) * 100
          
          return {
            ...prev,
            collectedData: newCollectedData,
            completedFields: completedCount,
            progress,
            validationError: null,
            isWaitingForUser: false
          }
        })
        
        options.onFieldChange?.(field.name, value)
      },
      
      onValidationError: (field, error) => {
        setState(prev => ({
          ...prev,
          validationError: error,
          isWaitingForUser: true,
          isLoading: false
        }))
      }
    })

    // Start the conversation
    const startConversation = async () => {
      setState(prev => ({ ...prev, isLoading: true }))
      
      try {
        // Get the first field to start
        const nextField = conversation.getNextField()
        if (nextField) {
          setState(prev => ({ ...prev, currentField: nextField }))
          
          // Build opening message
          const openingMessage: ConversationMessage = {
            role: 'assistant',
            content: conversation['getOpeningMessage']() || 'Let\'s get started!',
            timestamp: new Date()
          }
          
          setState(prev => ({
            ...prev,
            messages: [openingMessage],
            isWaitingForUser: true,
            isLoading: false
          }))
        } else {
          setState(prev => ({ ...prev, isComplete: true, isLoading: false }))
        }
      } catch (error) {
        options.onError?.(error as Error)
        setState(prev => ({ ...prev, isLoading: false }))
      }
    }

    startConversation()
  }, [gatherer])

  const sendMessage = useCallback(async (message: string) => {
    if (!conversationRef.current || state.isLoading) return

    setState(prev => ({ ...prev, isLoading: true, validationError: null }))

    try {
      // Add user message immediately
      const userMessage: ConversationMessage = {
        role: 'user',
        content: message,
        timestamp: new Date()
      }
      
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isWaitingForUser: false
      }))

      // Process the response
      const result = await conversationRef.current.processUserResponse(message)
      
      if (result.success) {
        // Check if conversation is complete
        const nextField = conversationRef.current.getNextField()
        if (!nextField) {
          const finalData = conversationRef.current.getCurrentData()
          const instance = new GathererInstance(gatherer.getMeta(), finalData)
          
          setState(prev => ({
            ...prev,
            isComplete: true,
            isLoading: false
          }))
          
          options.onComplete?.(instance)
        } else {
          setState(prev => ({
            ...prev,
            currentField: nextField,
            isWaitingForUser: true,
            isLoading: false
          }))
        }
      } else if (result.needsRetry) {
        setState(prev => ({
          ...prev,
          validationError: result.feedback || 'Please try again',
          isWaitingForUser: true,
          isLoading: false
        }))
      }
      
    } catch (error) {
      options.onError?.(error as Error)
      setState(prev => ({ 
        ...prev, 
        isLoading: false,
        validationError: 'An error occurred. Please try again.'
      }))
    }
  }, [state.isLoading, gatherer, options])

  const retry = useCallback(async () => {
    setState(prev => ({ ...prev, validationError: null }))
  }, [])

  const reset = useCallback(() => {
    conversationRef.current?.reset()
    
    const meta = gatherer.getMeta()
    const totalFields = meta.getFields().length
    
    setState({
      messages: [],
      collectedData: {},
      currentField: null,
      isComplete: false,
      isLoading: false,
      isWaitingForUser: false,
      validationError: null,
      totalFields,
      completedFields: 0,
      progress: 0
    })
    
    // Restart conversation
    const startConversation = async () => {
      setState(prev => ({ ...prev, isLoading: true }))
      
      const nextField = conversationRef.current?.getNextField()
      if (nextField) {
        setState(prev => ({
          ...prev,
          currentField: nextField,
          isWaitingForUser: true,
          isLoading: false
        }))
      }
    }

    startConversation()
  }, [gatherer])

  const skipField = useCallback(() => {
    if (!conversationRef.current || !state.currentField) return

    // Move to next field
    const nextField = conversationRef.current.getNextField()
    
    if (nextField) {
      setState(prev => ({
        ...prev,
        currentField: nextField,
        validationError: null
      }))
    } else {
      setState(prev => ({ ...prev, isComplete: true }))
    }
  }, [state.currentField])

  return [
    state,
    { sendMessage, retry, reset, skipField }
  ]
}

/**
 * Simple hook for basic gatherer usage
 */
export function useGatherer(gatherer: Gatherer) {
  const [state, actions] = useConversation(gatherer)
  
  return {
    ...state,
    ...actions,
    // Convenience getters
    canSend: !state.isLoading && state.isWaitingForUser,
    hasError: !!state.validationError,
    summary: conversationRef.current?.getConversationSummary() || ''
  }
}

/**
 * Hook for managing multiple gatherers or steps
 */
export function useMultiStepGatherer(gatherers: Gatherer[]) {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<GathererInstance[]>([])
  const [isComplete, setIsComplete] = useState(false)

  const currentGatherer = gatherers[currentStep]
  const [state, actions] = useConversation(currentGatherer, {
    onComplete: (instance) => {
      const newCompleted = [...completedSteps, instance]
      setCompletedSteps(newCompleted)
      
      if (currentStep + 1 < gatherers.length) {
        setCurrentStep(currentStep + 1)
      } else {
        setIsComplete(true)
      }
    }
  })

  const goToStep = useCallback((step: number) => {
    if (step >= 0 && step < gatherers.length) {
      setCurrentStep(step)
    }
  }, [gatherers.length])

  const reset = useCallback(() => {
    setCurrentStep(0)
    setCompletedSteps([])
    setIsComplete(false)
    actions.reset()
  }, [actions])

  return {
    // Current step state
    ...state,
    ...actions,
    
    // Multi-step specific
    currentStep,
    totalSteps: gatherers.length,
    completedSteps,
    isComplete: isComplete,
    canGoNext: state.isComplete && currentStep + 1 < gatherers.length,
    canGoPrevious: currentStep > 0,
    
    // Actions
    goToStep,
    reset: reset,
    nextStep: () => goToStep(currentStep + 1),
    previousStep: () => goToStep(currentStep - 1),
    
    // Data access
    getAllData: () => completedSteps.reduce((acc, step) => ({ ...acc, ...step.getData() }), {}),
    getStepData: (step: number) => completedSteps[step]?.getData() || {}
  }
}

/**
 * Hook for form-like usage where you want to control the conversation flow
 */
export function useControlledGatherer(gatherer: Gatherer) {
  const [collectedData, setCollectedData] = useState<CollectedData>({})
  const [currentFieldIndex, setCurrentFieldIndex] = useState(0)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  
  const meta = gatherer.getMeta()
  const fields = meta.getFields()
  const currentField = fields[currentFieldIndex]
  const isComplete = currentFieldIndex >= fields.length

  const setValue = useCallback((fieldName: string, value: string) => {
    setCollectedData(prev => ({ ...prev, [fieldName]: value }))
    setValidationErrors(prev => ({ ...prev, [fieldName]: '' }))
  }, [])

  const validateField = useCallback(async (fieldName: string, value: string) => {
    const field = meta.getField(fieldName)
    if (!field) return true

    const conversation = new Conversation(meta)
    const result = await conversation.validateResponse(field, value)
    
    if (!result.isValid) {
      setValidationErrors(prev => ({ ...prev, [fieldName]: result.feedback }))
      return false
    }
    
    return true
  }, [meta])

  const nextField = useCallback(async () => {
    if (!currentField) return
    
    const value = collectedData[currentField.name] || ''
    const isValid = await validateField(currentField.name, value)
    
    if (isValid) {
      setCurrentFieldIndex(prev => prev + 1)
    }
  }, [currentField, collectedData, validateField])

  const previousField = useCallback(() => {
    setCurrentFieldIndex(prev => Math.max(0, prev - 1))
  }, [])

  const reset = useCallback(() => {
    setCollectedData({})
    setCurrentFieldIndex(0)
    setValidationErrors({})
  }, [])

  const complete = useCallback(() => {
    if (isComplete) {
      return new GathererInstance(meta, collectedData)
    }
    return null
  }, [isComplete, meta, collectedData])

  return {
    // Current state
    currentField,
    currentFieldIndex,
    isComplete,
    collectedData,
    validationErrors,
    
    // Field info
    totalFields: fields.length,
    progress: (currentFieldIndex / fields.length) * 100,
    
    // Actions
    setValue,
    validateField,
    nextField,
    previousField,
    reset,
    complete,
    
    // Helpers
    canGoNext: !!currentField && !!collectedData[currentField.name],
    canGoPrevious: currentFieldIndex > 0,
    getFieldError: (fieldName: string) => validationErrors[fieldName] || '',
    hasError: (fieldName: string) => !!validationErrors[fieldName]
  }
}