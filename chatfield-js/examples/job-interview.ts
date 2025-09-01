#!/usr/bin/env ts-node
/**
 * Job Interview Example
 * =====================
 * 
 * This example demonstrates:
 * - Possible traits that activate based on conversation
 * - Confidential fields (has_mentored, shows_leadership)
 * - Conclusion fields (preparedness and cultural_fit assessment)
 * - Regular fields with validation (@must)
 * 
 * Run with:
 *   npx ts-node examples/job-interview.ts
 * 
 * For automated demo:
 *   npx ts-node examples/job-interview.ts --auto
 */

import { chatfield } from '../src/builders/gatherer-builder'
import { Interviewer } from '../src/core/interviewer'
import * as readline from 'readline'
import * as process from 'process'

/**
 * Create a job interview for a software engineer position
 */
function createJobInterview() {
  return chatfield()
    .type("JobInterview")
    .desc("Software Engineer position interview")
    
    .alice()
      .type("Hiring Manager")
      .trait.apply("Professional and encouraging")
    
    .bob()
      .type("Candidate")
      .trait.possible("career-changer", "mentions different industry or transferable skills")
      .trait.possible("senior-level", "10+ years of experience or leadership roles")
    
    .field("experience")
      .desc("Tell me about your relevant experience")
      .must("specific examples or projects")
    
    .field("technical_skills")
      .desc("What programming languages and technologies are you proficient in?")
      .hint("Please mention specific languages, frameworks, and tools")
    
    // Confidential field - tracked but never mentioned
    .field("has_mentored")
      .desc("Gives specific evidence of professionally mentoring junior colleagues")
      .confidential()
      .asBool()
    
    // Another confidential field
    .field("shows_leadership")
      .desc("Demonstrates leadership qualities or initiatives")
      .confidential()
      .asBool()
    
    // Conclusion field - assessed at the end
    .field("preparedness")
      .desc("Evaluate candidate's preparation: research, questions, examples")
      .conclude()
      .as_one.assessment("unprepared", "somewhat prepared", "well prepared", "exceptionally prepared")
    
    .field("cultural_fit")
      .desc("Assessment of cultural fit based on values and communication style")
      .conclude()
      .as_one.assessment("poor fit", "potential fit", "good fit", "excellent fit")
    
    .build()
}

/**
 * Run the interview interactively
 */
async function runInteractive(interview: any): Promise<boolean> {
  const threadId = `job-interview-${process.pid}`
  console.log(`Starting job interview (thread: ${threadId})`)
  console.log("=".repeat(60))
  console.log("Software Engineer Position Interview")
  console.log("=".repeat(60))
  
  const interviewer = new Interviewer(interview, { threadId })
  
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
  console.log("\n[Interview begins]\n")
  
  while (!interview._done) {
    const message = await interviewer.go(userInput)
    
    if (message) {
      console.log(`\nInterviewer: ${message}`)
    }
    
    if (!interview._done) {
      try {
        userInput = await askQuestion("\nCandidate: ")
      } catch (error) {
        console.log("\n[Interview ended by user]")
        break
      }
    }
  }
  
  if (interview._done) {
    console.log("\n[Interview complete - Thank you for your time]")
  }
  
  rl.close()
  return interview._done
}

/**
 * Run with prefab inputs for demonstration
 */
async function runAutomated(interview: any): Promise<boolean> {
  const prefabInputs = [
    "I've spent 5 years in finance, but I've been passionate about programming since college. " +
    "I built an automated trading system in Python that saved our team 20 hours per week. " +
    "I also created a risk analysis dashboard using React and D3.js.",
    
    "I'm proficient in Python, JavaScript, and SQL. I've worked extensively with React, Node.js, " +
    "and Django. I also have experience with Docker, AWS, and CI/CD pipelines using GitHub Actions.",
    
    "In my previous role, I regularly mentored junior analysts on Python programming and data analysis. " +
    "I also led a cross-functional team to implement our new reporting system.",
    
    "I've researched your company's focus on fintech innovation and your recent Series B funding. " +
    "I'm particularly excited about your API-first approach and how my background in both finance " +
    "and engineering could contribute to bridging technical and business requirements. " +
    "What are the biggest technical challenges your team is currently facing?"
  ]
  
  const threadId = `job-demo-${process.pid}`
  console.log(`Running automated demo (thread: ${threadId})`)
  console.log("=".repeat(60))
  console.log("Software Engineer Position Interview (Demo)")
  console.log("=".repeat(60))
  
  const interviewer = new Interviewer(interview, { threadId })
  
  let inputIndex = 0
  let userInput: string | null = null
  
  console.log("\n[Interview begins]\n")
  
  while (!interview._done) {
    const message = await interviewer.go(userInput)
    
    if (message) {
      console.log(`\nInterviewer: ${message}`)
    }
    
    if (!interview._done) {
      if (inputIndex < prefabInputs.length) {
        userInput = prefabInputs[inputIndex++]
        console.log(`\nCandidate: ${userInput}`)
        // Add a small delay for readability
        await new Promise(resolve => setTimeout(resolve, 1500))
      } else {
        console.log("\n[Demo inputs exhausted]")
        break
      }
    }
  }
  
  return interview._done
}

/**
 * Display interview results and assessment
 */
function displayResults(interview: any): void {
  console.log("\n" + "=".repeat(60))
  console.log("INTERVIEW ASSESSMENT")
  console.log("-".repeat(60))
  
  // Regular fields
  if (interview.experience) {
    console.log("\nExperience Summary:")
    const preview = interview.experience.length > 100 
      ? interview.experience.substring(0, 100) + "..."
      : interview.experience
    console.log(`  ${preview}`)
  }
  
  if (interview.technical_skills) {
    console.log("\nTechnical Skills:")
    const preview = interview.technical_skills.length > 100
      ? interview.technical_skills.substring(0, 100) + "..."
      : interview.technical_skills
    console.log(`  ${preview}`)
  }
  
  // Check activated traits
  const bobRole = interview._chatfield.roles.get('bob')
  const traits: string[] = []
  
  if (bobRole?.possibleTraits.get('career-changer')?.active) {
    traits.push("Career Changer")
  }
  if (bobRole?.possibleTraits.get('senior-level')?.active) {
    traits.push("Senior Level")
  }
  
  if (traits.length > 0) {
    console.log("\nCandidate Profile:")
    traits.forEach(trait => console.log(`  • ${trait}`))
  }
  
  // Confidential assessments (internal only)
  console.log("\n[Internal Assessment]")
  
  if (interview.has_mentored !== null && interview.has_mentored !== undefined) {
    const mentored = interview.has_mentored.as_bool ? "Yes" : "No"
    console.log(`  Mentoring Experience: ${mentored}`)
  }
  
  if (interview.shows_leadership !== null && interview.shows_leadership !== undefined) {
    const leadership = interview.shows_leadership.as_bool ? "Yes" : "No"
    console.log(`  Leadership Qualities: ${leadership}`)
  }
  
  // Conclusion fields
  if (interview.preparedness) {
    console.log(`  Preparedness: ${interview.preparedness.as_one_assessment || interview.preparedness}`)
  }
  
  if (interview.cultural_fit) {
    console.log(`  Cultural Fit: ${interview.cultural_fit.as_one_assessment || interview.cultural_fit}`)
  }
  
  // Calculate overall recommendation
  console.log("\n[Recommendation]")
  const hasMentored = interview.has_mentored?.as_bool || false
  const showsLeadership = interview.shows_leadership?.as_bool || false
  const preparedness = interview.preparedness?.as_one_assessment
  const culturalFit = interview.cultural_fit?.as_one_assessment
  
  let recommendation = "Needs Review"
  if (preparedness === "exceptionally prepared" && culturalFit === "excellent fit") {
    recommendation = "Strong Hire"
  } else if (
    (preparedness === "well prepared" || preparedness === "exceptionally prepared") &&
    (culturalFit === "good fit" || culturalFit === "excellent fit")
  ) {
    recommendation = hasMentored || showsLeadership ? "Hire" : "Likely Hire"
  } else if (culturalFit === "poor fit") {
    recommendation = "No Hire"
  }
  
  console.log(`  Decision: ${recommendation}`)
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
  const interview = createJobInterview()
  
  try {
    // Run the interview
    const completed = isAuto 
      ? await runAutomated(interview)
      : await runInteractive(interview)
    
    // Display results if completed
    if (completed) {
      displayResults(interview)
    } else {
      console.log("\nInterview incomplete.")
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

export { createJobInterview, displayResults }