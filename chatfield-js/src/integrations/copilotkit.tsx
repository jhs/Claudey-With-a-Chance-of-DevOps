/**
 * CopilotKit integration for Chatfield
 * Allows using Chatfield gatherers within CopilotKit conversations
 */

import React, { useState, useCallback, useEffect } from 'react'
import { useCopilotChat, useCopilotAction } from '@copilotkit/react-core'
import { Gatherer, GathererInstance } from '../core/gatherer'
import { createGatherer, schemaPresets } from '../builders/schema-builder'
import { useConversation } from './react'
import { ConversationInterface, FieldPreview } from './react-components'

export interface ChatfieldCopilotProps {
  gatherers?: Record<string, Gatherer>
  onDataCollected?: (gathererName: string, data: any) => void
  className?: string
}

/**
 * CopilotKit component that integrates Chatfield gatherers
 */
export function ChatfieldCopilot({ 
  gatherers = {}, 
  onDataCollected, 
  className = '' 
}: ChatfieldCopilotProps) {
  const [activeGatherer, setActiveGatherer] = useState<string | null>(null)
  const [collectedData, setCollectedData] = useState<Record<string, any>>({})

  // Register actions with CopilotKit for each gatherer
  Object.entries(gatherers).forEach(([name, gatherer]) => {
    useCopilotAction({
      name: `start_${name}_gathering`,
      description: `Start collecting ${name} information through a conversation`,
      handler: async () => {
        setActiveGatherer(name)
        return `Starting ${name} information gathering...`
      }
    })
  })

  // Register preset actions
  useCopilotAction({
    name: "start_business_plan",
    description: "Start collecting business plan information",
    handler: async () => {
      setActiveGatherer('business_plan')
      return "Starting business plan gathering..."
    }
  })

  useCopilotAction({
    name: "start_bug_report",
    description: "Start collecting bug report information",
    handler: async () => {
      setActiveGatherer('bug_report')
      return "Starting bug report gathering..."
    }
  })

  useCopilotAction({
    name: "start_user_feedback",
    description: "Start collecting user feedback",
    handler: async () => {
      setActiveGatherer('user_feedback')
      return "Starting user feedback collection..."
    }
  })

  useCopilotAction({
    name: "show_collected_data",
    description: "Show all collected data from previous conversations",
    handler: async () => {
      if (Object.keys(collectedData).length === 0) {
        return "No data has been collected yet."
      }
      
      let summary = "Here's what we've collected:\n\n"
      Object.entries(collectedData).forEach(([gathererName, data]) => {
        summary += `**${gathererName}:**\n`
        Object.entries(data).forEach(([field, value]) => {
          summary += `- ${field}: ${value}\n`
        })
        summary += "\n"
      })
      
      return summary
    }
  })

  const handleDataCollected = useCallback((gathererName: string, data: any) => {
    setCollectedData(prev => ({
      ...prev,
      [gathererName]: data
    }))
    setActiveGatherer(null)
    onDataCollected?.(gathererName, data)
  }, [onDataCollected])

  // Get the current gatherer
  const getCurrentGatherer = (): Gatherer | null => {
    if (!activeGatherer) return null
    
    if (gatherers[activeGatherer]) {
      return gatherers[activeGatherer]
    }
    
    // Use presets
    switch (activeGatherer) {
      case 'business_plan':
        return createGatherer(schemaPresets.businessPlan())
      case 'bug_report':
        return createGatherer(schemaPresets.bugReport())
      case 'user_feedback':
        return createGatherer(schemaPresets.userFeedback())
      default:
        return null
    }
  }

  const currentGatherer = getCurrentGatherer()

  if (activeGatherer && currentGatherer) {
    return (
      <div className={`chatfield-copilot ${className}`}>
        <div className="mb-4">
          <h3 className="text-lg font-semibold mb-2">
            {activeGatherer.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Collection
          </h3>
          <button
            onClick={() => setActiveGatherer(null)}
            className="text-sm text-gray-600 hover:text-gray-800 underline"
          >
            ← Back to chat
          </button>
        </div>
        
        <ConversationInterface
          gatherer={currentGatherer}
          onComplete={(data) => handleDataCollected(activeGatherer, data)}
          onError={(error) => console.error('Gatherer error:', error)}
          className="h-96"
        />
      </div>
    )
  }

  return (
    <div className={`chatfield-copilot ${className}`}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Data Collection Tools</h3>
        <p className="text-sm text-gray-600 mb-4">
          Available gathering tools you can activate through conversation:
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {/* Built-in presets */}
        <GathererCard
          name="Business Plan"
          description="Collect comprehensive business plan information"
          onClick={() => setActiveGatherer('business_plan')}
          gatherer={createGatherer(schemaPresets.businessPlan())}
        />
        
        <GathererCard
          name="Bug Report"
          description="Gather detailed bug report information"
          onClick={() => setActiveGatherer('bug_report')}
          gatherer={createGatherer(schemaPresets.bugReport())}
        />
        
        <GathererCard
          name="User Feedback"
          description="Collect user feedback and suggestions"
          onClick={() => setActiveGatherer('user_feedback')}
          gatherer={createGatherer(schemaPresets.userFeedback())}
        />
        
        {/* Custom gatherers */}
        {Object.entries(gatherers).map(([name, gatherer]) => (
          <GathererCard
            key={name}
            name={name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            description={`Custom ${name} data collection`}
            onClick={() => setActiveGatherer(name)}
            gatherer={gatherer}
          />
        ))}
      </div>

      {Object.keys(collectedData).length > 0 && (
        <div className="border-t pt-4">
          <h4 className="font-semibold mb-2">Previously Collected Data:</h4>
          <div className="space-y-2">
            {Object.entries(collectedData).map(([name, data]) => (
              <div key={name} className="bg-gray-50 p-3 rounded">
                <div className="font-medium text-sm text-gray-700">{name}</div>
                <div className="text-xs text-gray-500">
                  {Object.keys(data).length} fields collected
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface GathererCardProps {
  name: string
  description: string
  onClick: () => void
  gatherer: Gatherer
}

function GathererCard({ name, description, onClick, gatherer }: GathererCardProps) {
  const [showPreview, setShowPreview] = useState(false)
  const fieldCount = gatherer.getFieldPreview().length

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-medium text-gray-900">{name}</h4>
        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
          {fieldCount} fields
        </span>
      </div>
      
      <p className="text-sm text-gray-600 mb-3">{description}</p>
      
      <div className="flex space-x-2">
        <button
          onClick={onClick}
          className="flex-1 px-3 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
        >
          Start
        </button>
        
        <button
          onClick={() => setShowPreview(!showPreview)}
          className="px-3 py-2 text-gray-600 text-sm border border-gray-300 rounded hover:bg-gray-50"
        >
          {showPreview ? 'Hide' : 'Preview'}
        </button>
      </div>
      
      {showPreview && (
        <div className="mt-3 pt-3 border-t">
          <FieldPreview gatherer={gatherer} className="border-0 p-0" />
        </div>
      )}
    </div>
  )
}

/**
 * Hook for using Chatfield within CopilotKit conversations
 */
export function useChatfieldCopilot() {
  const [activeGatherers, setActiveGatherers] = useState<Record<string, Gatherer>>({})
  const [gathererInstances, setGathererInstances] = useState<Record<string, GathererInstance>>({})

  const startGathering = useCallback((name: string, gatherer: Gatherer) => {
    setActiveGatherers(prev => ({ ...prev, [name]: gatherer }))
  }, [])

  const completeGathering = useCallback((name: string, instance: GathererInstance) => {
    setGathererInstances(prev => ({ ...prev, [name]: instance }))
    setActiveGatherers(prev => {
      const { [name]: _, ...rest } = prev
      return rest
    })
  }, [])

  const getAllData = useCallback(() => {
    return Object.fromEntries(
      Object.entries(gathererInstances).map(([name, instance]) => [
        name,
        instance.getData()
      ])
    )
  }, [gathererInstances])

  return {
    activeGatherers,
    gathererInstances,
    startGathering,
    completeGathering,
    getAllData,
    hasActiveGatherers: Object.keys(activeGatherers).length > 0,
    hasCompletedData: Object.keys(gathererInstances).length > 0
  }
}

/**
 * CopilotKit action registrar for dynamic gatherer setup
 */
export function registerChatfieldActions(
  gatherers: Record<string, Gatherer>,
  options: {
    onGathererStart?: (name: string) => void
    onGathererComplete?: (name: string, data: any) => void
  } = {}
) {
  return Object.entries(gatherers).map(([name, gatherer]) => {
    return {
      name: `collect_${name}`,
      description: `Start collecting ${name} information through an interactive conversation`,
      handler: async () => {
        options.onGathererStart?.(name)
        return `Starting ${name} information collection. This will guide you through a conversational form to gather all necessary details.`
      }
    }
  })
}

/**
 * Chatfield-powered CopilotKit sidebar component
 */
export function ChatfieldSidebar({ 
  gatherers = {},
  className = '' 
}: {
  gatherers?: Record<string, Gatherer>
  className?: string
}) {
  const {
    activeGatherers,
    gathererInstances,
    startGathering,
    completeGathering,
    getAllData
  } = useChatfieldCopilot()

  // Register actions for all gatherers
  Object.entries(gatherers).forEach(([name, gatherer]) => {
    useCopilotAction({
      name: `collect_${name}`,
      description: `Collect ${name} information through conversation`,
      handler: async () => {
        startGathering(name, gatherer)
        return `Starting ${name} collection...`
      }
    })
  })

  // Register data export action
  useCopilotAction({
    name: "export_collected_data",
    description: "Export all collected data as JSON",
    handler: async () => {
      const data = getAllData()
      return JSON.stringify(data, null, 2)
    }
  })

  const activeGathererEntries = Object.entries(activeGatherers)

  return (
    <div className={`chatfield-sidebar ${className}`}>
      {activeGathererEntries.length > 0 ? (
        <div className="space-y-4">
          {activeGathererEntries.map(([name, gatherer]) => (
            <div key={name} className="border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold mb-2">
                Collecting: {name.replace('_', ' ')}
              </h3>
              
              <ConversationInterface
                gatherer={gatherer}
                onComplete={(data) => {
                  const instance = new GathererInstance(gatherer.getMeta(), data)
                  completeGathering(name, instance)
                }}
                className="h-80"
              />
            </div>
          ))}
        </div>
      ) : (
        <ChatfieldCopilot 
          gatherers={gatherers}
          onDataCollected={(name, data) => console.log(`Collected ${name}:`, data)}
          className={className}
        />
      )}
    </div>
  )
}