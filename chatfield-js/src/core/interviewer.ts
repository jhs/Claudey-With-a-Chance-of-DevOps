/**
 * LangGraph-based Interviewer for Chatfield conversations
 * Manages conversation flow and state using LangGraph.js
 */

import { 
  StateGraph, 
  MemorySaver,
  START,
  END,
  Annotation,
  interrupt
} from '@langchain/langgraph'
import { 
  BaseMessage, 
  HumanMessage, 
  AIMessage, 
  SystemMessage,
  ToolMessage 
} from '@langchain/core/messages'
import { ChatOpenAI } from '@langchain/openai'
import { tool } from '@langchain/core/tools'
import { z } from 'zod'
import { v4 as uuidv4 } from 'uuid'

/**
 * Interview base class (simplified version for TypeScript)
 */
export interface Interview {
  _name(): string
  _fields(): string[]
  _alice_role_name(): string
  _bob_role_name(): string
  _alice_role(): { type?: string; traits: string[] }
  _bob_role(): { type?: string; traits: string[] }
  _done: boolean
  _chatfield: {
    type: string
    desc?: string
    roles: {
      alice: { type?: string; traits: string[] }
      bob: { type?: string; traits: string[] }
    }
    fields: Record<string, {
      desc?: string
      specs?: Record<string, string[]>
      casts?: Record<string, any>
      value?: any
    }>
  }
  _get_chat_field(name: string): any
  _copy_from(other: Interview): void
  _pretty(): string
}

/**
 * State type for LangGraph conversation
 */
const InterviewState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => [...x, ...y],
    default: () => []
  }),
  interview: Annotation<Interview>({
    reducer: (a, b) => mergeInterviews(a, b)
  })
})

type InterviewStateType = typeof InterviewState.State

/**
 * Merge two Interview instances
 */
function mergeInterviews(a: Interview, b: Interview): Interview {
  // For now, just return b (the newer state)
  // TODO: Implement proper merging logic
  if (a && b) {
    // Copy over any new field values from b to a
    for (const fieldName of Object.keys(b._chatfield.fields)) {
      const bValue = b._chatfield.fields[fieldName].value
      if (bValue !== undefined && bValue !== null) {
        a._chatfield.fields[fieldName].value = bValue
      }
    }
    return a
  }
  return b || a
}

/**
 * Interviewer class that orchestrates conversations using LangGraph
 */
export class Interviewer {
  private interview: Interview
  private graph: any
  private config: any
  private llm: ChatOpenAI
  private llmWithTools!: ChatOpenAI
  private checkpointer: MemorySaver
  private toolName: string

  constructor(interview: Interview, threadId?: string) {
    this.interview = interview
    this.checkpointer = new MemorySaver()
    this.config = {
      configurable: {
        thread_id: threadId || uuidv4()
      }
    }

    // Initialize LLM
    this.llm = new ChatOpenAI({
      modelName: 'gpt-4o',
      temperature: 0.0
    })

    // Setup tools and graph
    this.toolName = `update_${this.interview._name()}`
    this.setupGraph()
  }

  private setupGraph() {
    const theAlice = this.interview._alice_role_name()
    const theBob = this.interview._bob_role_name()

    // Create tool for updating interview fields
    const toolDescription = `Record valid information stated by the ${theBob} about the ${this.interview._name()}`
    
    // Build Zod schema for tool arguments dynamically
    const fieldSchemas: Record<string, any> = {}
    
    for (const fieldName of this.interview._fields()) {
      const field = this.interview._chatfield.fields[fieldName]
      
      // Create schema for this field
      const fieldSchema = z.object({
        value: z.string().describe('The most typical valid representation'),
        context: z.string().describe('Conversational context'),
        as_quote: z.string().describe(`Direct quote from ${theBob}`)
      }).optional()
      
      fieldSchemas[fieldName] = fieldSchema
    }

    const toolSchema = z.object(fieldSchemas)

    // Create the tool with simplified schema
    const updateTool = tool(
      async (args: any) => {
        console.log('Tool called with:', args)
        
        try {
          // Process the tool input
          for (const [fieldName, fieldValue] of Object.entries(args)) {
            if (fieldValue && typeof fieldValue === 'object') {
              console.log(`Setting field ${fieldName}:`, fieldValue)
              if (this.interview._chatfield.fields[fieldName]) {
                this.interview._chatfield.fields[fieldName].value = fieldValue
              }
            }
          }
          return 'Success'
        } catch (error: any) {
          return `Error: ${error.message}`
        }
      },
      {
        name: this.toolName,
        description: toolDescription,
        schema: z.record(z.any()) // Simplified schema to avoid deep instantiation
      }
    )

    // Bind tools to LLM
    this.llmWithTools = this.llm.bindTools([updateTool])

    // Build the state graph
    const builder = new StateGraph(InterviewState)
      .addNode('initialize', this.initialize.bind(this))
      .addNode('think', this.think.bind(this))
      .addNode('listen', this.listen.bind(this))
      .addNode('tools', this.toolsNode.bind(this))
      .addNode('teardown', this.teardown.bind(this))
      .addEdge(START, 'initialize')
      .addEdge('initialize', 'think')
      .addConditionalEdges('think', this.routeThink.bind(this))
      .addEdge('listen', 'think')
      .addEdge('tools', 'think')
      .addEdge('teardown', END)

    // Compile the graph
    this.graph = builder.compile({ checkpointer: this.checkpointer })
  }

  private async initialize(state: InterviewStateType) {
    console.log('Initialize:', this.interview._name())
    return {}
  }

  private async think(state: InterviewStateType) {
    console.log('Think:', this.interview._name())
    
    const newMessages: BaseMessage[] = []
    
    // Add system message if this is the start
    if (!state.messages || state.messages.length === 0) {
      console.log('Starting conversation in thread:', this.config.configurable.thread_id)
      const systemPrompt = this.makeSystemPrompt(state)
      newMessages.push(new SystemMessage(systemPrompt))
    }

    // Determine which LLM to use (with or without tools)
    let llm = this.llmWithTools
    const latestMessage = newMessages[newMessages.length - 1] || 
                         (state.messages && state.messages[state.messages.length - 1])
    
    if (latestMessage instanceof SystemMessage) {
      llm = this.llm // No tools after system message
    } else if (latestMessage instanceof ToolMessage && latestMessage.content === 'Success') {
      llm = this.llm // No tools after successful tool response
    }

    // Invoke LLM
    const allMessages = [...(state.messages || []), ...newMessages]
    const response = await llm.invoke(allMessages)
    newMessages.push(response)

    return { messages: newMessages }
  }

  private async listen(state: InterviewStateType) {
    console.log('Listen:', this.interview._name())
    
    // Copy state back to interview
    if (state.interview) {
      this.interview._copy_from(state.interview)
    }

    // Get the last AI message
    const lastMessage = state.messages[state.messages.length - 1]
    if (!(lastMessage instanceof AIMessage)) {
      throw new Error('Expected last message to be AIMessage')
    }

    // Interrupt to get user input
    const feedback = lastMessage.content as string
    const update = interrupt(feedback)
    
    console.log('Interrupt result:', update)
    const userInput = (update as any).user_input
    const userMsg = new HumanMessage(userInput)
    
    return { messages: [userMsg] }
  }

  private async toolsNode(state: InterviewStateType) {
    console.log('Tools node')
    
    // Get the last message (should have tool calls)
    const lastMessage = state.messages[state.messages.length - 1] as AIMessage
    
    if (lastMessage.tool_calls && lastMessage.tool_calls.length > 0) {
      const toolCall = lastMessage.tool_calls[0]
      
      // Process the tool call
      try {
        for (const [fieldName, fieldValue] of Object.entries(toolCall?.args || {})) {
          if (fieldValue && typeof fieldValue === 'object') {
            console.log(`Setting field ${fieldName}:`, fieldValue)
            if (this.interview._chatfield.fields[fieldName]) {
              this.interview._chatfield.fields[fieldName].value = fieldValue
            }
          }
        }
        
        const toolMessage = new ToolMessage({
          content: 'Success',
          tool_call_id: toolCall?.id || ''
        })
        
        return { 
          messages: [toolMessage],
          interview: this.interview
        }
      } catch (error: any) {
        const toolMessage = new ToolMessage({
          content: `Error: ${error.message}`,
          tool_call_id: toolCall?.id || ''
        })
        
        return { messages: [toolMessage] }
      }
    }
    
    return {}
  }

  private async teardown(state: InterviewStateType) {
    console.log('Teardown:', this.interview._name())
    
    // Copy final state back to interview
    if (state.interview) {
      this.interview._copy_from(state.interview)
    }
    
    return {}
  }

  private routeThink(state: InterviewStateType): string {
    console.log('Route think edge')
    
    // Check if last message has tool calls
    const lastMessage = state.messages[state.messages.length - 1]
    if (lastMessage instanceof AIMessage && lastMessage.tool_calls && lastMessage.tool_calls.length > 0) {
      return 'tools'
    }
    
    // Check if interview is done
    if (this.interview._done) {
      console.log('Route: to teardown')
      return 'teardown'
    }
    
    return 'listen'
  }

  private makeSystemPrompt(state: InterviewStateType): string {
    const interview = state.interview || this.interview
    const collectionName = interview._name()
    const theAlice = interview._alice_role_name()
    const theBob = interview._bob_role_name()
    
    // Build field descriptions
    const fields: string[] = []
    for (const fieldName of Object.keys(interview._chatfield.fields).reverse()) {
      const field = interview._chatfield.fields[fieldName]
      if (!field) continue
      let fieldLabel = fieldName
      if (field.desc) {
        fieldLabel += `: ${field.desc}`
      }
      
      // Add specs if any
      const specs: string[] = []
      if (field.specs) {
        for (const [specType, rules] of Object.entries(field.specs)) {
          for (const rule of rules) {
            specs.push(`    - ${specType}: ${rule}`)
          }
        }
      }
      
      const fieldPrompt = `- ${fieldLabel}`
      if (specs.length > 0) {
        fields.push(fieldPrompt + '\n' + specs.join('\n'))
      } else {
        fields.push(fieldPrompt)
      }
    }
    
    // Build traits
    let aliceTraits = ''
    let bobTraits = ''
    
    const aliceRole = interview._alice_role()
    if (aliceRole.traits && aliceRole.traits.length > 0) {
      aliceTraits = `# Traits and Characteristics about the ${theAlice}\n\n`
      aliceTraits += aliceRole.traits.map(t => `- ${t}`).reverse().join('\n')
    }
    
    const bobRole = interview._bob_role()
    if (bobRole.traits && bobRole.traits.length > 0) {
      bobTraits = `# Traits and Characteristics about the ${theBob}\n\n`
      bobTraits += bobRole.traits.map(t => `- ${t}`).reverse().join('\n')
    }
    
    let withTraits = ''
    let aliceAndBob = ''
    if (aliceTraits || bobTraits) {
      withTraits = ` Participants' characteristics and traits will be described below.`
      aliceAndBob = '\n\n'
      if (aliceTraits) aliceAndBob += aliceTraits
      if (aliceTraits && bobTraits) aliceAndBob += '\n\n'
      if (bobTraits) aliceAndBob += bobTraits
    }
    
    const useTools = ` Use tools to record information fields when you identify valid information to collect.`
    
    return `You are the conversational ${theAlice} focused on gathering key information in conversation with the ${theBob}, into a collection called ${collectionName}, detailed below.${withTraits}${useTools} Although the ${theBob} may take the conversation anywhere, your response must fit the conversation and your respective roles while refocusing the discussion so that you can gather clear key ${collectionName} information from the ${theBob}.${aliceAndBob}

----

# Collection: ${collectionName}

${fields.join('\n\n')}
`
  }

  /**
   * Process one conversation turn
   */
  async go(userInput?: string | null): Promise<string | null> {
    console.log('Go: User input:', userInput)
    
    const currentState = await this.graph.getState(this.config)
    
    let graphInput: any
    if (currentState.values && currentState.values.messages && currentState.values.messages.length > 0) {
      console.log('Continue conversation:', this.config.configurable.thread_id)
      graphInput = {
        __command__: {
          update: {},
          resume: { user_input: userInput }
        }
      }
    } else {
      console.log('New conversation:', this.config.configurable.thread_id)
      const messages = userInput ? [new HumanMessage(userInput)] : []
      graphInput = {
        messages,
        interview: this.interview
      }
    }
    
    const interrupts: string[] = []
    
    // Stream the graph execution
    const stream = await this.graph.stream(graphInput, this.config)
    
    for await (const event of stream) {
      console.log('Event:', Object.keys(event))
      
      // Check for interrupts
      for (const [nodeName, nodeOutput] of Object.entries(event)) {
        if (nodeOutput && typeof nodeOutput === 'object' && '__interrupt__' in nodeOutput) {
          const interruptValue = (nodeOutput as any).__interrupt__.value
          if (typeof interruptValue === 'string') {
            interrupts.push(interruptValue)
          }
        }
      }
    }
    
    if (interrupts.length === 0) {
      return null
    }
    
    if (interrupts.length > 1) {
      throw new Error(`Multiple interrupts received: ${interrupts}`)
    }
    
    return interrupts[0]
  }
}