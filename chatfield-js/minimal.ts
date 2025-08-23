#!/usr/bin/env node
/**
 * Test real OpenAI API calls with full logging
 * TypeScript port of Python run_real_api.py
 */

import * as path from 'path'
import * as dotenv from 'dotenv'
import * as readline from 'readline'
import { Interview } from './src/core/interview'
import { Interviewer } from './src/core/interviewer'


class NotableNumbers extends Interview {
  static description = 'Numbers important to you'

  favorite() {
    return 'what is your favorite number?'
  }
}

function createReadlineInterface(): readline.Interface {
  return readline.createInterface({
    input: process.stdin,
    output: process.stdout
  })
}

async function interviewLoop() {
  const interview = new NotableNumbers()
  console.log(`The main interview object: ${interview._name()}`)

  const threadId = process.pid.toString()
  console.log(`Thread ID: ${threadId}`)

  const interviewer = new Interviewer(interview, threadId)

  // Create readline interface
  const rl = createReadlineInterface()

  // Helper function to get user input
  const getUserInput = (prompt: string): Promise<string> => {
    return new Promise((resolve) => {
      rl.question(prompt, (answer) => {
        resolve(answer.trim())
      })
    })
  }

  let userInput: string | undefined = undefined

  while (true) {
    // Process one conversation turn
    const message = await interviewer.go(userInput)

    // Display AI message if present
    if (message) {
      console.log('=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
      console.log(message)
      console.log('=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
    }

    // Get user input
    userInput = await getUserInput('Your response> ')
    break
  }

  // Close readline interface
  rl.close()

  // Display final results
  console.log('---------------------------')
  console.log('Dialogue finished:')
  console.log(interview._pretty())
  console.log('')
  
  // Display LangSmith trace URL if available
  const traceUrl = `https://smith.langchain.com/o/92e94533-dd45-4b1d-bc4f-4fd9476bb1e4/projects/p/1991a1b2-6dad-4d39-8a19-bbc3be33a8b6?searchModel=%7B%22filter%22%3A%22and%28eq%28metadata_key%2C+%5C%22thread_id%5C%22%29%2C+eq%28metadata_value%2C+%5C%22${threadId}%5C%22%29%29%22%7D&runtab=0&timeModel=%7B%22duration%22%3A%227d%22%7D`
  console.log(`Trace:\n${traceUrl}`)
}

/**
 * Main entry point
 */
async function main() {
  dotenv.config({ 
    path: path.resolve(__dirname, '../.env'),
    override: true 
  })

  await interviewLoop()
}

// Run if executed directly
if (require.main === module) {
  main()
}