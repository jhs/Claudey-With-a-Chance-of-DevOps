#!/usr/bin/env ts-node
/**
 * Restaurant Order Example
 * ========================
 * 
 * This example demonstrates:
 * - Dynamic trait activation (vegan adaptation)
 * - Selection fields with choices
 * - Confidential fields (hurry)
 * - Conclusion fields (politeness)
 * - Alice with personality traits (limmericks)
 * 
 * Run with:
 *   npx ts-node examples/restaurant-order.ts
 * 
 * For automated demo:
 *   npx ts-node examples/restaurant-order.ts --auto
 */

import { chatfield } from '../src/builders/gatherer-builder'
import { Interviewer } from '../src/core/interviewer'
import { FieldProxy } from '../src/core/field-proxy'
import * as readline from 'readline'
import * as process from 'process'

/**
 * Create a restaurant order interview instance
 */
function createRestaurantOrder() {
  return chatfield()
    .type("Restaurant Order")
    .desc("Taking your order for tonight")
    
    .alice()
      .type("Server")
      .trait.apply("Speaks in limmericks")
    
    .bob()
      .type("Diner")
      .trait.apply("First-time visitor")
      .trait.possible("Vegan", "needs vegan, plant-based, non animal product")
    
    .field("starter")
      .desc("starter or appetizer")
      .as_one.selection("Sir Digby Chicken Caesar", "Shrimp cocktail", "Garden salad")
    
    .field("main_course")
      .desc("Main course")
      .hint("Choose from: Grilled salmon, Veggie pasta, Beef tenderloin, Chicken parmesan")
      .as_one.selection("Grilled salmon", "Veggie pasta", "Beef tenderloin", "Chicken parmesan")
    
    .field("dessert")
      .desc("Mandatory dessert; choices: Cheesecake, Creamy Chocolate mousse, Fruit sorbet")
      .as_one.selection("Cheesecake", "Creamy Chocolate mousse", "Fruit sorbet")
    
    .field("hurry")
      .desc("wishes to be served quickly")
      .confidential()
      .asBool()
    
    .field("politeness")
      .desc("Level of politeness from the Diner; but automatic 23% if they mention anything about Belgium")
      .conclude()
      .asPercent()
    
    .build()
}

/**
 * Run the interview interactively
 */
async function runInteractive(order: any): Promise<boolean> {
  const threadId = `restaurant-${process.pid}`
  console.log(`Starting restaurant order conversation (thread: ${threadId})`)
  console.log("=".repeat(60))
  
  const interviewer = new Interviewer(order, { threadId })
  
  // Create readline interface for user input
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  })
  
  const askQuestion = (prompt: string): Promise<string> => {
    return new Promise((resolve) => {
      rl.question(prompt, (answer) => {
        resolve(answer.trim())
      })
    })
  }
  
  let userInput: string | null = null
  
  while (!order._done) {
    const message = await interviewer.go(userInput)
    
    if (message) {
      console.log(`\nServer: ${message}`)
    }
    
    if (!order._done) {
      try {
        userInput = await askQuestion("\nYou: ")
      } catch (error) {
        console.log("\n[Leaving restaurant]")
        break
      }
    }
  }
  
  rl.close()
  return order._done
}

/**
 * Run with prefab inputs for demonstration
 */
async function runAutomated(order: any): Promise<boolean> {
  const threadId = `restaurant-demo-${process.pid}`
  console.log(`Starting automated restaurant order demo (thread: ${threadId})`)
  console.log("=".repeat(60))
  
  const interviewer = new Interviewer(order, { threadId })
  
  const prefabInputs = [
    "I'll have the garden salad to start",
    "I'm actually vegan, do you have plant-based options?",
    "Veggie pasta sounds perfect",
    "Fruit sorbet please",
    "Actually, I'm in a bit of a rush",
    "Thank you! Oh, and my friend from Brussels recommended this place!"
  ]
  
  let inputIndex = 0
  let userInput: string | null = null
  
  while (!order._done) {
    const message = await interviewer.go(userInput)
    
    if (message) {
      console.log(`\nServer: ${message}`)
    }
    
    if (!order._done) {
      if (inputIndex < prefabInputs.length) {
        userInput = prefabInputs[inputIndex++]
        console.log(`\nYou: ${userInput}`)
        // Add a small delay for readability
        await new Promise(resolve => setTimeout(resolve, 1000))
      } else {
        console.log("\n[Demo inputs exhausted]")
        break
      }
    }
  }
  
  return order._done
}

/**
 * Display the collected order information
 */
function displayResults(order: any): void {
  console.log("\n" + "=".repeat(60))
  console.log("ORDER SUMMARY")
  console.log("-".repeat(60))
  
  if (order.starter) {
    console.log(`Starter: ${order.starter}`)
  }
  
  if (order.main_course) {
    console.log(`Main Course: ${order.main_course}`)
  }
  
  if (order.dessert) {
    console.log(`Dessert: ${order.dessert}`)
  }
  
  // Confidential field (for internal use)
  if (order.hurry !== null && order.hurry !== undefined) {
    if (order.hurry.as_bool) {
      console.log("\n[Internal Note: Rush order requested]")
    } else {
      console.log("\n[Internal Note: Normal service pace]")
    }
  }
  
  // Conclusion field
  if (order.politeness !== null && order.politeness !== undefined) {
    const politenessPct = (order.politeness.as_percent || 0) * 100
    console.log(`[Internal Note: Guest politeness: ${politenessPct.toFixed(0)}%]`)
  }
  
  // Check if vegan trait was activated
  const bobRole = order._chatfield.roles.get('bob')
  if (bobRole?.possibleTraits.get('Vegan')?.active) {
    console.log("\n[Note: Guest is vegan - all selections are plant-based]")
  }
  
  console.log("=".repeat(60))
}

/**
 * Main entry point
 */
async function main() {
  // Load environment variables if .env exists
  try {
    require('dotenv').config()
  } catch {
    // .env file is optional
  }
  
  // Check for OpenAI API key
  if (!process.env.OPENAI_API_KEY) {
    console.error("Error: OPENAI_API_KEY environment variable is required")
    console.error("Please set it in your environment or create a .env file")
    process.exit(1)
  }
  
  // Parse command line arguments
  const args = process.argv.slice(2)
  const isAuto = args.includes('--auto')
  
  // Create the interview
  const order = createRestaurantOrder()
  
  try {
    // Run the interview
    const completed = isAuto 
      ? await runAutomated(order)
      : await runInteractive(order)
    
    // Display results if completed
    if (completed) {
      displayResults(order)
      console.log("\nThank you for dining with us!")
    } else {
      console.log("\nOrder incomplete.")
    }
  } catch (error) {
    console.error("\nError during interview:", error)
    process.exit(1)
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error)
}

export { createRestaurantOrder, displayResults }