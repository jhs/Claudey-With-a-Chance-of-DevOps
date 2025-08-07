/**
 * Schema-based gatherer examples
 */

import { createGatherer, schemaPresets } from '../src'
import { GathererSchema } from '../src'

// Example 1: Using built-in presets
const BusinessPlanGatherer = createGatherer(schemaPresets.businessPlan())
const BugReportGatherer = createGatherer(schemaPresets.bugReport())
const FeedbackGatherer = createGatherer(schemaPresets.userFeedback())

// Example 2: Custom schema definition
const JobApplicationSchema: GathererSchema = {
  docstring: "I'll help you complete your job application by gathering all the necessary information.",
  userContext: ["job applicant", "professional seeking new opportunities"],
  agentContext: [
    "professional and supportive",
    "help present qualifications in the best light",
    "ask for specific examples and details"
  ],
  fields: {
    position: {
      description: "What position are you applying for?",
      must: ["specific job title", "company name"],
      hint: "Include both the role and the company you're applying to"
    },
    experience: {
      description: "How many years of relevant experience do you have?",
      must: ["specific number of years"],
      hint: "Count both professional and significant personal projects"
    },
    skills: {
      description: "What are your key skills for this role?",
      must: ["at least 3 specific skills"],
      reject: ["generic statements like 'good communicator'"],
      hint: "Focus on technical skills, tools, and specific competencies"
    },
    achievements: {
      description: "What is your most relevant professional achievement?",
      must: ["specific accomplishment", "measurable impact"],
      hint: "Include numbers, percentages, or concrete outcomes"
    },
    motivation: {
      description: "Why are you interested in this specific role?",
      must: ["connection to company/role"],
      reject: ["generic reasons like 'good opportunity'"],
      hint: "Show you've researched the company and role"
    },
    salary: {
      description: "What are your salary expectations?",
      must: ["specific range or number"],
      when: (data) => data.position && !data.position.toLowerCase().includes("intern"),
      hint: "Research market rates for this role in your location"
    },
    availability: {
      description: "When can you start?",
      must: ["specific timeframe"],
      hint: "Consider any notice period with current employer"
    },
    questions: {
      description: "What questions do you have about the role or company?",
      hint: "Asking thoughtful questions shows genuine interest"
    }
  }
}

// Example 3: Event planning schema
const EventPlanningSchema: GathererSchema = {
  docstring: "Let's plan your event! I'll gather all the details needed to make it successful.",
  userContext: ["event organizer", "planning a special occasion"],
  agentContext: [
    "enthusiastic and detail-oriented",
    "help think through logistics",
    "suggest alternatives for constraints"
  ],
  fields: {
    event_type: {
      description: "What type of event are you planning?",
      must: ["specific event type"],
      hint: "Wedding, birthday party, corporate meeting, conference, etc."
    },
    date: {
      description: "When would you like to hold the event?",
      must: ["specific date or timeframe"],
      hint: "Include preferred date and backup options"
    },
    duration: {
      description: "How long will the event last?",
      must: ["specific duration"],
      hint: "Hours for the main event, plus setup/cleanup time"
    },
    attendees: {
      description: "How many people will attend?",
      must: ["estimated number"],
      hint: "Include expected range (minimum to maximum)"
    },
    venue: {
      description: "Where would you like to hold the event?",
      hint: "Specific venue, type of location, or 'need help choosing'"
    },
    budget: {
      description: "What is your budget for this event?",
      must: ["budget range or maximum amount"],
      hint: "Include all costs: venue, catering, entertainment, decorations"
    },
    catering: {
      description: "What food and drink arrangements do you want?",
      when: (data) => parseInt(data.attendees || "0") > 5,
      hint: "Full meal, appetizers, drinks only, dietary restrictions, etc."
    },
    entertainment: {
      description: "What entertainment or activities will you have?",
      when: (data) => {
        const type = data.event_type?.toLowerCase() || ""
        return type.includes("party") || type.includes("wedding") || type.includes("celebration")
      },
      hint: "Music, DJ, games, speakers, special activities"
    },
    special_requirements: {
      description: "Any special requirements or considerations?",
      hint: "Accessibility, parking, equipment, decorations, themes"
    }
  }
}

// Example 4: Customer onboarding schema
const CustomerOnboardingSchema: GathererSchema = {
  docstring: "Welcome! Let's get your account set up with everything you need to succeed.",
  userContext: ["new customer", "getting started with the product"],
  agentContext: [
    "welcoming and helpful",
    "ensure they understand each step",
    "set them up for success"
  ],
  fields: {
    company: {
      description: "What's your company name?",
      must: ["company name"],
      hint: "This will appear on your account and invoices"
    },
    role: {
      description: "What's your role at the company?",
      must: ["job title or role description"],
      hint: "This helps us customize your experience"
    },
    company_size: {
      description: "How many employees does your company have?",
      must: ["number or range"],
      hint: "This helps us recommend the right plan"
    },
    use_case: {
      description: "What do you plan to use our product for?",
      must: ["specific use case or goal"],
      hint: "The more specific you are, the better we can help you succeed"
    },
    timeline: {
      description: "When do you need to have this up and running?",
      must: ["timeframe"],
      hint: "Immediate, within a week, within a month, etc."
    },
    integration: {
      description: "What other tools do you need this to integrate with?",
      when: (data) => {
        const role = data.role?.toLowerCase() || ""
        return role.includes("tech") || role.includes("it") || role.includes("engineer")
      },
      hint: "CRM, email marketing, analytics, databases, etc."
    },
    team_size: {
      description: "How many people will be using this initially?",
      must: ["number of users"],
      hint: "We'll set up the right number of user accounts"
    },
    support: {
      description: "What level of support would you like?",
      when: (data) => parseInt(data.company_size || "0") > 50,
      hint: "Self-service, email support, phone support, dedicated account manager"
    },
    training: {
      description: "Would you like training for your team?",
      when: (data) => parseInt(data.team_size || "0") > 3,
      hint: "Online tutorials, live training sessions, documentation"
    }
  }
}

// Example 5: Using schema validation and merging
const BaseContactSchema: GathererSchema = {
  fields: {
    name: { description: "Your name" },
    email: { description: "Your email" }
  }
}

const ExtendedContactSchema: GathererSchema = {
  fields: {
    phone: { description: "Your phone number" },
    company: { description: "Your company" }
  },
  userContext: ["business contact"],
  agentContext: ["professional tone"]
}

// Merge schemas
import { mergeSchemas, validateSchema } from '../src'

const CombinedContactSchema = mergeSchemas(BaseContactSchema, ExtendedContactSchema)

// Validate before using
const validation = validateSchema(CombinedContactSchema)
if (!validation.isValid) {
  console.error("Schema validation failed:", validation.errors)
} else {
  const CombinedContactGatherer = createGatherer(CombinedContactSchema)
  console.log("Contact gatherer created successfully")
}

// Example 6: Dynamic schema generation
function createSurveySchema(questions: Array<{
  id: string
  question: string
  required?: boolean
  hint?: string
}>): GathererSchema {
  const fields: GathererSchema['fields'] = {}
  
  questions.forEach(q => {
    fields[q.id] = {
      description: q.question,
      must: q.required ? ["provide an answer"] : undefined,
      hint: q.hint
    }
  })
  
  return {
    docstring: "Survey questions",
    userContext: ["survey participant"],
    agentContext: ["neutral and efficient"],
    fields
  }
}

// Usage example
const surveyQuestions = [
  { id: "q1", question: "How satisfied are you with our service?", required: true },
  { id: "q2", question: "What could we improve?", hint: "Be specific about areas for improvement" },
  { id: "q3", question: "Would you recommend us to others?", required: true }
]

const DynamicSurvey = createGatherer(createSurveySchema(surveyQuestions))

// Export all examples
export {
  BusinessPlanGatherer,
  BugReportGatherer,
  FeedbackGatherer,
  JobApplicationSchema,
  EventPlanningSchema,
  CustomerOnboardingSchema,
  CombinedContactSchema,
  DynamicSurvey,
  createSurveySchema
}

// Demonstration function
async function demonstrateSchemas() {
  console.log("=== Schema-based Gatherer Examples ===\n")
  
  // Show field preview for job application
  const jobGatherer = createGatherer(JobApplicationSchema)
  console.log("Job Application Fields:")
  jobGatherer.getFieldPreview().forEach((field, index) => {
    console.log(`${index + 1}. ${field.name}: ${field.description}`)
    if (field.hint) console.log(`   💡 ${field.hint}`)
    if (field.hasValidation) console.log(`   ✓ Has validation rules`)
  })
  
  console.log("\n" + "=".repeat(50) + "\n")
  
  // Show event planning fields
  const eventGatherer = createGatherer(EventPlanningSchema)
  console.log("Event Planning Fields:")
  eventGatherer.getFieldPreview().forEach((field, index) => {
    console.log(`${index + 1}. ${field.name}: ${field.description}`)
    if (field.hint) console.log(`   💡 ${field.hint}`)
  })
  
  console.log("\n" + "=".repeat(50) + "\n")
  
  // Demonstrate validation
  console.log("Schema Validation Example:")
  const invalidSchema: GathererSchema = {
    fields: {
      bad_field: {} as any // Missing description
    }
  }
  
  const result = validateSchema(invalidSchema)
  if (!result.isValid) {
    console.log("❌ Schema validation failed:")
    result.errors.forEach(error => console.log(`   - ${error}`))
  }
  
  console.log("\n" + "=".repeat(50) + "\n")
  
  // Show preset usage
  console.log("Using Built-in Presets:")
  const businessPlan = schemaPresets.businessPlan()
  console.log("Business Plan Fields:", Object.keys(businessPlan.fields).join(", "))
  
  const bugReport = schemaPresets.bugReport()
  console.log("Bug Report Fields:", Object.keys(bugReport.fields).join(", "))
  
  const feedback = schemaPresets.userFeedback()
  console.log("User Feedback Fields:", Object.keys(feedback.fields).join(", "))
}

// Run if executed directly
if (require.main === module) {
  demonstrateSchemas().catch(console.error)
}