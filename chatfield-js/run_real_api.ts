#!/usr/bin/env node
/**
 * Test real OpenAI API calls with full logging
 * TypeScript port of Python run_real_api.py
 */

import * as dotenv from 'dotenv'
import * as readline from 'readline'
import {
  Interview,
  alice,
  bob,
  must,
  reject,
  hint,
  as_int,
  as_str,
  as_float,
  as_bool,
  as_percent,
  as_list,
  as_set,
  as_dict,
  as_lang,
  as_one,
  as_maybe,
  as_multi,
  as_any
} from './src/core/interview'
import { Interviewer } from './src/core/interviewer'

// Load environment variables from parent directory
import * as path from 'path'
dotenv.config({ 
  path: path.resolve(__dirname, '../.env'),
  override: true 
})

/**
 * NotableNumbers Interview class
 */
class NotableNumbers extends Interview {
  static description = 'Numbers important to you'

  favorite() {
    return 'what is your favorite number?'
  }
}

// Apply decorators manually to avoid TypeScript decorator issues
// TODO: Fix decorator typing for class-level decorators
(NotableNumbers as any)._alice_role = 'Alice';
(NotableNumbers as any)._alice_traits = ['talks in Cockney rhyming slang'];
(NotableNumbers as any)._bob_role = 'Albert Einstein'

// Apply field decorators manually
const proto = NotableNumbers.prototype
const fieldMeta = {
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
  }
}
Reflect.defineMetadata('chatfield', fieldMeta, proto, 'favorite')

/**
 * Create readline interface for user input
 */
function createReadlineInterface(): readline.Interface {
  return readline.createInterface({
    input: process.stdin,
    output: process.stdout
  })
}

/**
 * Main interview loop
 */
async function interviewLoop() {
  // Create interview instance
  const interview = new NotableNumbers()
  console.log(`The main interview object: ${interview._name()}`)

  // Create thread ID
  const threadId = process.pid.toString()
  console.log(`Thread ID: ${threadId}`)

  // Create interviewer
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
    try {
      // Process one conversation turn
      const message = await interviewer.go(userInput)

      // Display AI message if present
      if (message) {
        console.log('=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
        console.log(message)
        console.log('=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
      }

      // Check if interview is done
      if (interview._done) {
        console.log('Hooray! User request is done.')
        break
      }

      // Get user input
      userInput = await getUserInput('Your response> ')
      
      // Check for exit
      if (userInput === null || userInput === '') {
        console.log('Exit')
        break
      }

    } catch (error) {
      if (error instanceof Error && error.message.includes('Interrupt')) {
        // This is expected - handle the interrupt
        console.log('Interrupted for user input')
        userInput = await getUserInput('Your response> ')
        if (userInput === null || userInput === '') {
          console.log('Exit')
          break
        }
      } else {
        console.error('Error:', error)
        break
      }
    }
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
  try {
    await interviewLoop()
  } catch (error) {
    console.error('Fatal error:', error)
    process.exit(1)
  }
}

// Run if executed directly
if (require.main === module) {
  main()
}