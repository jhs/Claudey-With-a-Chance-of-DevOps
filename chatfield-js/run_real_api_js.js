#!/usr/bin/env node
/**
 * JavaScript version of run_real_api that bypasses TypeScript compilation issues
 * This is a direct port of the Python run_real_api.py using LangGraph.js
 */

const path = require('path');
require('dotenv').config({ 
  path: path.resolve(__dirname, '../.env'),
  override: true 
});

const { StateGraph, MemorySaver, START, END, Annotation, interrupt } = require('@langchain/langgraph');
const { BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage } = require('@langchain/core/messages');
const { ChatOpenAI } = require('@langchain/openai');
const { tool } = require('@langchain/core/tools');
const { z } = require('zod');
const { v4: uuidv4 } = require('uuid');
const readline = require('readline');

/**
 * NotableNumbers Interview class
 */
class NotableNumbers {
  constructor() {
    this._chatfield = {
      type: 'NotableNumbers',
      desc: 'Numbers important to you',
      roles: {
        alice: { 
          type: 'Alice', 
          traits: ['talks in Cockney rhyming slang'] 
        },
        bob: { 
          type: 'Albert Einstein', 
          traits: [] 
        }
      },
      fields: {
        favorite: {
          desc: 'what is your favorite number?',
          specs: {
            must: ['a number between 1 and 100']
          },
          casts: {
            as_int: { type: 'int', prompt: 'Parse as integer' },
            as_lang_fr: { type: 'str', prompt: 'Translate to French' },
            as_lang_th: { type: 'str', prompt: 'Translate to Thai' },
            as_lang_esperanto: { type: 'str', prompt: 'A full sentence in Esperanto translating, "The number is exactly: <value>"' },
            as_lang_traditionalChinese: { type: 'str', prompt: 'Translate to Traditional Chinese' },
            as_bool_odd: { type: 'bool', prompt: 'True if the number is odd, False if even' },
            as_bool_power_of_two: { type: 'bool', prompt: 'True if the number is a power of two, False otherwise' },
            as_str: { type: 'str', prompt: 'Timestamp in ISO format, representing this value number of minutes since Jan 1 2025 Zulu time' },
            as_set_factors: { type: 'set', prompt: 'The set of all factors the number, excluding 1 and the number itself' },
            as_one_parity: { type: 'choice', prompt: 'Choose exactly one: {name}', choices: ['even', 'odd'], null: false, multi: false },
            as_maybe_speaking: { type: 'choice', prompt: 'Choose zero or one: {name}', choices: ['One syllable when spoken in English', 'Two syllables when spoken in English'], null: true, multi: false },
            as_multi_math_facts: { type: 'choice', prompt: 'Choose one or more: {name}', choices: ['even', 'odd', 'prime', 'composite', 'fibonacci', 'perfect square', 'power of two'], null: false, multi: true },
            as_any_other_facts: { type: 'choice', prompt: 'Choose zero or more: {name}', choices: ['prime', 'mersenne prime', 'first digit is 3'], null: true, multi: true }
          },
          value: null
        }
      }
    };
    this._done = false;
  }

  _name() { return this._chatfield.type; }
  _fields() { return Object.keys(this._chatfield.fields); }
  _alice_role_name() { return this._chatfield.roles.alice.type; }
  _bob_role_name() { return this._chatfield.roles.bob.type; }
  _alice_role() { return this._chatfield.roles.alice; }
  _bob_role() { return this._chatfield.roles.bob; }
  
  _get_chat_field(name) {
    return this._chatfield.fields[name];
  }
  
  _copy_from(other) {
    this._chatfield = JSON.parse(JSON.stringify(other._chatfield));
    this._done = other._done;
  }
  
  _pretty() {
    const lines = [];
    lines.push(`${this._name()}:`);
    
    for (const [name, field] of Object.entries(this._chatfield.fields)) {
      const value = field.value?.value || 'None';
      lines.push(`  ${name}: ${value}`);
      
      // Show transformations if present
      if (field.value) {
        for (const [key, val] of Object.entries(field.value)) {
          if (key !== 'value' && key !== 'context' && key !== 'as_quote') {
            lines.push(`    ${key}: ${val}`);
          }
        }
      }
    }
    
    return lines.join('\n');
  }
}

/**
 * Merge two Interview instances
 */
function mergeInterviews(a, b) {
  if (a && b) {
    // Copy over any new field values from b to a
    for (const fieldName of Object.keys(b._chatfield.fields)) {
      const bValue = b._chatfield.fields[fieldName].value;
      if (bValue !== undefined && bValue !== null) {
        a._chatfield.fields[fieldName].value = bValue;
      }
    }
    a._done = b._done || a._done;
    return a;
  }
  return b || a;
}

/**
 * State annotation for LangGraph
 */
const InterviewState = Annotation.Root({
  messages: Annotation({
    reducer: (x, y) => [...(x || []), ...(y || [])],
    default: () => []
  }),
  interview: Annotation({
    reducer: mergeInterviews
  })
});

/**
 * Interviewer class using LangGraph.js
 */
class Interviewer {
  constructor(interview, threadId) {
    this.interview = interview;
    this.checkpointer = new MemorySaver();
    this.config = {
      configurable: {
        thread_id: threadId || uuidv4()
      }
    };

    // Initialize LLM
    this.llm = new ChatOpenAI({
      modelName: 'gpt-4o',
      temperature: 0.0
    });

    this.toolName = `update_${this.interview._name()}`;
    this.setupGraph();
  }

  setupGraph() {
    const theAlice = this.interview._alice_role_name();
    const theBob = this.interview._bob_role_name();

    // Create tool for updating interview fields
    const toolDescription = `Record valid information stated by the ${theBob} about the ${this.interview._name()}`;
    
    // Create the tool with simplified schema
    const updateTool = tool(
      async (args) => {
        console.log('Tool called with:', args);
        
        try {
          // Process the tool input
          for (const [fieldName, fieldValue] of Object.entries(args)) {
            if (fieldValue && typeof fieldValue === 'object') {
              console.log(`Setting field ${fieldName}:`, fieldValue);
              if (this.interview._chatfield.fields[fieldName]) {
                this.interview._chatfield.fields[fieldName].value = fieldValue;
              }
            }
          }
          return 'Success';
        } catch (error) {
          return `Error: ${error.message}`;
        }
      },
      {
        name: this.toolName,
        description: toolDescription,
        schema: z.record(z.any())
      }
    );

    // Bind tools to LLM
    this.llmWithTools = this.llm.bindTools([updateTool]);

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
      .addEdge('listen', END)  // Listen ends the graph run, waiting for user input
      .addEdge('tools', 'think')
      .addEdge('teardown', END);

    // Compile the graph
    this.graph = builder.compile({ checkpointer: this.checkpointer });
  }

  async initialize(state) {
    console.log('Initialize:', this.interview._name());
    return {};
  }

  async think(state) {
    console.log('Think:', this.interview._name());
    
    const newMessages = [];
    
    // Add system message if this is the start
    if (!state.messages || state.messages.length === 0) {
      console.log('Starting conversation in thread:', this.config.configurable.thread_id);
      const systemPrompt = this.makeSystemPrompt(state);
      newMessages.push(new SystemMessage(systemPrompt));
    }

    // Determine which LLM to use (with or without tools)
    let llm = this.llmWithTools;
    const latestMessage = newMessages[newMessages.length - 1] || 
                         (state.messages && state.messages[state.messages.length - 1]);
    
    if (latestMessage instanceof SystemMessage) {
      llm = this.llm; // No tools after system message
    } else if (latestMessage instanceof ToolMessage && latestMessage.content === 'Success') {
      llm = this.llm; // No tools after successful tool response
    }

    // Invoke LLM
    const allMessages = [...(state.messages || []), ...newMessages];
    const response = await llm.invoke(allMessages);
    newMessages.push(response);

    return { messages: newMessages };
  }

  async listen(state) {
    console.log('Listen:', this.interview._name());
    
    // Copy state back to interview
    if (state.interview) {
      this.interview._copy_from(state.interview);
    }

    // Get the last AI message
    const lastMessage = state.messages[state.messages.length - 1];
    if (!(lastMessage instanceof AIMessage)) {
      throw new Error('Expected last message to be AIMessage');
    }

    // For JavaScript version, we'll handle the interrupt differently
    // The graph will pause here and wait for user input
    // which will be provided when go() is called again
    return {};
  }

  async toolsNode(state) {
    console.log('Tools node');
    
    // Get the last message (should have tool calls)
    const lastMessage = state.messages[state.messages.length - 1];
    
    if (lastMessage.tool_calls && lastMessage.tool_calls.length > 0) {
      const toolCall = lastMessage.tool_calls[0];
      
      // Process the tool call
      try {
        for (const [fieldName, fieldValue] of Object.entries(toolCall.args || {})) {
          if (fieldValue && typeof fieldValue === 'object') {
            console.log(`Setting field ${fieldName}:`, fieldValue);
            if (this.interview._chatfield.fields[fieldName]) {
              this.interview._chatfield.fields[fieldName].value = fieldValue;
            }
          }
        }
        
        const toolMessage = new ToolMessage({
          content: 'Success',
          tool_call_id: toolCall.id || ''
        });
        
        return { 
          messages: [toolMessage],
          interview: this.interview
        };
      } catch (error) {
        const toolMessage = new ToolMessage({
          content: `Error: ${error.message}`,
          tool_call_id: toolCall.id || ''
        });
        
        return { messages: [toolMessage] };
      }
    }
    
    return {};
  }

  async teardown(state) {
    console.log('Teardown:', this.interview._name());
    
    // Copy final state back to interview
    if (state.interview) {
      this.interview._copy_from(state.interview);
    }
    
    return {};
  }

  routeThink(state) {
    console.log('Route think edge');
    
    // Check if last message has tool calls
    const lastMessage = state.messages[state.messages.length - 1];
    if (lastMessage instanceof AIMessage && lastMessage.tool_calls && lastMessage.tool_calls.length > 0) {
      return 'tools';
    }
    
    // Check if interview is done
    if (this.interview._done) {
      console.log('Route: to teardown');
      return 'teardown';
    }
    
    return 'listen';
  }

  makeSystemPrompt(state) {
    const interview = state.interview || this.interview;
    const collectionName = interview._name();
    const theAlice = interview._alice_role_name();
    const theBob = interview._bob_role_name();
    
    // Build field descriptions
    const fields = [];
    for (const fieldName of Object.keys(interview._chatfield.fields).reverse()) {
      const field = interview._chatfield.fields[fieldName];
      if (!field) continue;
      
      let fieldLabel = fieldName;
      if (field.desc) {
        fieldLabel += `: ${field.desc}`;
      }
      
      // Add specs if any
      const specs = [];
      if (field.specs) {
        for (const [specType, rules] of Object.entries(field.specs)) {
          for (const rule of rules) {
            specs.push(`    - ${specType}: ${rule}`);
          }
        }
      }
      
      const fieldPrompt = `- ${fieldLabel}`;
      if (specs.length > 0) {
        fields.push(fieldPrompt + '\n' + specs.join('\n'));
      } else {
        fields.push(fieldPrompt);
      }
    }
    
    // Build traits
    let aliceTraits = '';
    let bobTraits = '';
    
    const aliceRole = interview._alice_role();
    if (aliceRole.traits && aliceRole.traits.length > 0) {
      aliceTraits = `# Traits and Characteristics about the ${theAlice}\n\n`;
      aliceTraits += aliceRole.traits.map(t => `- ${t}`).reverse().join('\n');
    }
    
    const bobRole = interview._bob_role();
    if (bobRole.traits && bobRole.traits.length > 0) {
      bobTraits = `# Traits and Characteristics about the ${theBob}\n\n`;
      bobTraits += bobRole.traits.map(t => `- ${t}`).reverse().join('\n');
    }
    
    let withTraits = '';
    let aliceAndBob = '';
    if (aliceTraits || bobTraits) {
      withTraits = ` Participants' characteristics and traits will be described below.`;
      aliceAndBob = '\n\n';
      if (aliceTraits) aliceAndBob += aliceTraits;
      if (aliceTraits && bobTraits) aliceAndBob += '\n\n';
      if (bobTraits) aliceAndBob += bobTraits;
    }
    
    const useTools = ` Use tools to record information fields when you identify valid information to collect.`;
    
    return `You are the conversational ${theAlice} focused on gathering key information in conversation with the ${theBob}, into a collection called ${collectionName}, detailed below.${withTraits}${useTools} Although the ${theBob} may take the conversation anywhere, your response must fit the conversation and your respective roles while refocusing the discussion so that you can gather clear key ${collectionName} information from the ${theBob}.${aliceAndBob}

----

# Collection: ${collectionName}

${fields.join('\n\n')}
`;
  }

  async go(userInput) {
    console.log('Go: User input:', userInput);
    
    const currentState = await this.graph.getState(this.config);
    
    let graphInput;
    if (currentState.values && currentState.values.messages && currentState.values.messages.length > 0) {
      console.log('Continue conversation:', this.config.configurable.thread_id);
      // Add user message and continue
      const userMsg = userInput ? new HumanMessage(userInput) : null;
      graphInput = {
        messages: userMsg ? [userMsg] : []
      };
    } else {
      console.log('New conversation:', this.config.configurable.thread_id);
      const messages = userInput ? [new HumanMessage(userInput)] : [];
      graphInput = {
        messages,
        interview: this.interview
      };
    }
    
    let aiMessage = null;
    
    // Stream the graph execution
    const stream = await this.graph.stream(graphInput, this.config);
    
    for await (const event of stream) {
      // Log events for debugging
      console.log('Event:', Object.keys(event));
    }
    
    // Get the final state after execution
    const finalState = await this.graph.getState(this.config);
    
    // Check if we have messages and get the last AI message
    if (finalState.values && finalState.values.messages) {
      const lastMessage = finalState.values.messages[finalState.values.messages.length - 1];
      if (lastMessage instanceof AIMessage) {
        aiMessage = lastMessage.content;
      }
    }
    
    // Check if interview is done
    if (finalState.values && finalState.values.interview) {
      this.interview._copy_from(finalState.values.interview);
    }
    
    return aiMessage;
  }
}

/**
 * Main interview loop
 */
async function interviewLoop() {
  // Create interview instance
  const interview = new NotableNumbers();
  console.log(`The main interview object: ${interview._name()}`);

  // Create thread ID
  const threadId = process.pid.toString();
  console.log(`Thread ID: ${threadId}`);

  // Create interviewer
  const interviewer = new Interviewer(interview, threadId);

  // Create readline interface
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  // Helper function to get user input
  const getUserInput = (prompt) => {
    return new Promise((resolve) => {
      rl.question(prompt, (answer) => {
        resolve(answer.trim());
      });
    });
  };

  let userInput = undefined;

  while (true) {
    try {
      // Process one conversation turn
      const message = await interviewer.go(userInput);

      // Display AI message if present
      if (message) {
        console.log('=-=-=-=-=-=-=-=-=-=-=-=-=-=-');
        console.log(message);
        console.log('=-=-=-=-=-=-=-=-=-=-=-=-=-=-');
      }

      // Check if interview is done
      if (interview._done) {
        console.log('Hooray! User request is done.');
        break;
      }

      // Get user input
      userInput = await getUserInput('Your response> ');
      
      // Check for exit
      if (userInput === null || userInput === '') {
        console.log('Exit');
        break;
      }

    } catch (error) {
      console.error('Error:', error);
      break;
    }
  }

  // Close readline interface
  rl.close();

  // Display final results
  console.log('---------------------------');
  console.log('Dialogue finished:');
  console.log(interview._pretty());
  console.log('');
  
  // Display LangSmith trace URL if available
  const traceUrl = `https://smith.langchain.com/o/92e94533-dd45-4b1d-bc4f-4fd9476bb1e4/projects/p/1991a1b2-6dad-4d39-8a19-bbc3be33a8b6?searchModel=%7B%22filter%22%3A%22and%28eq%28metadata_key%2C+%5C%22thread_id%5C%22%29%2C+eq%28metadata_value%2C+%5C%22${threadId}%5C%22%29%29%22%7D&runtab=0&timeModel=%7B%22duration%22%3A%227d%22%7D`;
  console.log(`Trace:\n${traceUrl}`);
}

/**
 * Main entry point
 */
async function main() {
  try {
    await interviewLoop();
  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}