/**
 * Decorator-based Chatfield examples - matching Python API
 */

import { gather, field, must, reject, hint, user, agent } from '../src'
import { OpenAIBackend, MockLLMBackend } from '../src'

// Example 1: Simple contact form
@gather
@user("new customer") 
@agent("be friendly and efficient")
class ContactForm {
  @field("Your full name")
  @must("include first and last name")
  name!: string

  @field("Your email address") 
  @must("valid email format")
  @reject("temporary email addresses")
  email!: string

  @field("Your message")
  @must("at least 20 characters")
  @hint("Please describe your inquiry in detail")
  message!: string
}

// Example 2: Business plan gathering
@gather
@user("entrepreneur or startup founder")
@agent("be patient and thorough") 
@agent("ask follow-up questions when answers seem incomplete")
class BusinessPlan {
  @field("What is your business concept?")
  @must("include target market")
  @must("describe the product or service")
  @hint("Think about what you're building and who it's for")
  concept!: string

  @field("What specific problem does your business solve?")
  @must("clear problem statement")
  @reject("vague or generic problems")
  @hint("Describe the pain point your customers currently experience")
  problem!: string

  @field("How does your product/service solve this problem?")
  @must("explain unique approach")
  solution!: string

  @field("Who is your target market?")
  @must("specific demographics or market segment")
  @hint("Be specific about size, characteristics, and accessibility")
  market!: string

  @field("Who are your main competitors?")
  @must("name specific companies or alternatives") 
  @hint("Include both direct and indirect competitors")
  competition!: string

  @field("What is your competitive advantage?")
  @must("unique differentiator")
  advantage!: string

  @field("How will you make money?")
  @must("specific revenue model")
  @hint("Subscription, one-time purchase, advertising, commission, etc.")
  revenue!: string

  @field("How much funding do you need to get started?")
  @must("specific amount and time period")
  funding!: string
}

// Example 3: Bug report gathering
@gather
@user("software user experiencing issues")
@agent("focused on technical details")
@agent("systematic and thorough")
class BugReport {
  @field("What's a brief summary of the issue?")
  @must("concise description of the problem")
  @hint("One sentence describing what went wrong")
  summary!: string

  @field("What steps can we follow to reproduce this bug?")
  @must("step-by-step instructions")
  @must("specific actions and inputs")
  @hint("List the exact actions that lead to the problem")
  steps!: string

  @field("What did you expect to happen?")
  @must("clear expected behavior")
  @hint("Describe what should have happened normally")
  expected!: string

  @field("What actually happened instead?")
  @must("specific description of incorrect behavior")
  @hint("Include any error messages or unexpected results")
  actual!: string

  @field("How often does this happen?")
  @hint("Always, sometimes, rarely? Under what conditions?")
  frequency!: string

  @field("What system are you using?")
  @must("operating system")
  @must("browser or app version")
  @hint("OS version, browser, device type, etc.")
  environment!: string

  @field("Have you found any workarounds?")
  @hint("Any temporary solutions or ways to avoid the problem?")
  workaround!: string
}

// Example 4: User feedback collection
@gather
@user("product user providing feedback")
@agent("appreciative and constructive")
@agent("ask follow-up questions for clarity")
class UserFeedback {
  @field("How would you rate your overall experience?")
  @must("rating from 1-10 or descriptive feedback")
  @hint("Consider ease of use, functionality, and value")
  rating!: string

  @field("What do you like most about the product?")
  @hint("Features, design, performance, support, etc.")
  likes!: string

  @field("What could be improved?")
  @hint("Pain points, confusing features, missing functionality")
  dislikes!: string

  @field("Do you have any specific suggestions?")
  @hint("New features, changes, or improvements you'd like to see")
  suggestions!: string

  @field("How do you primarily use the product?")
  @must("specific use case or scenario")
  @hint("What tasks or goals are you trying to accomplish?")
  use_case!: string

  @field("What alternatives did you consider?")
  @hint("Other products or solutions you looked at")
  alternatives!: string

  @field("Would you recommend this to others?")
  @must("yes/no with reasoning")
  @hint("Consider what you'd tell a friend or colleague")
  recommend!: string
}

// Example 5: Job application
@gather
@user("job applicant")
@agent("professional and supportive")
@agent("help present qualifications in the best light")
class JobApplication {
  @field("What position are you applying for?")
  @must("specific job title")
  @must("company name")
  @hint("Include both the role and the company you're applying to")
  position!: string

  @field("How many years of relevant experience do you have?")
  @must("specific number of years")
  @hint("Count both professional and significant personal projects")
  experience!: string

  @field("What are your key skills for this role?")
  @must("at least 3 specific skills")
  @reject("generic statements like 'good communicator'")
  @hint("Focus on technical skills, tools, and specific competencies")
  skills!: string

  @field("What is your most relevant professional achievement?")
  @must("specific accomplishment")
  @must("measurable impact")
  @hint("Include numbers, percentages, or concrete outcomes")
  achievements!: string

  @field("Why are you interested in this specific role?")
  @must("connection to company/role")
  @reject("generic reasons like 'good opportunity'")
  @hint("Show you've researched the company and role")
  motivation!: string

  @field("What are your salary expectations?")
  @must("specific range or number")
  @hint("Research market rates for this role in your location")
  salary!: string

  @field("When can you start?")
  @must("specific timeframe")
  @hint("Consider any notice period with current employer")
  availability!: string

  @field("What questions do you have about the role or company?")
  @hint("Asking thoughtful questions shows genuine interest")
  questions!: string
}

// Example 6: Event planning
@gather
@user("event organizer")
@agent("enthusiastic and detail-oriented")
@agent("help think through logistics")
class EventPlanning {
  @field("What type of event are you planning?")
  @must("specific event type")
  @hint("Wedding, birthday party, corporate meeting, conference, etc.")
  event_type!: string

  @field("When would you like to hold the event?")
  @must("specific date or timeframe")
  @hint("Include preferred date and backup options")
  date!: string

  @field("How long will the event last?")
  @must("specific duration")
  @hint("Hours for the main event, plus setup/cleanup time")
  duration!: string

  @field("How many people will attend?")
  @must("estimated number")
  @hint("Include expected range (minimum to maximum)")
  attendees!: string

  @field("Where would you like to hold the event?")
  @hint("Specific venue, type of location, or 'need help choosing'")
  venue!: string

  @field("What is your budget for this event?")
  @must("budget range or maximum amount")
  @hint("Include all costs: venue, catering, entertainment, decorations")
  budget!: string

  @field("What food and drink arrangements do you want?")
  @hint("Full meal, appetizers, drinks only, dietary restrictions, etc.")
  catering!: string

  @field("What entertainment or activities will you have?")
  @hint("Music, DJ, games, speakers, special activities")
  entertainment!: string

  @field("Any special requirements or considerations?")
  @hint("Accessibility, parking, equipment, decorations, themes")
  special_requirements!: string
}

// Usage examples
async function demonstrateDecorators() {
  console.log('=== Chatfield Decorator API Examples ===\n')

  // Use with mock backend for demonstration
  const mockBackend = new MockLLMBackend()
  mockBackend.addValidationResponse('VALID')
  mockBackend.addValidationResponse('VALID')
  mockBackend.addValidationResponse('VALID')

  // Preview fields for business plan
  console.log('Business Plan Fields:')
  const businessPreview = BusinessPlan.getFieldPreview()
  businessPreview.forEach((field, index) => {
    console.log(`${index + 1}. ${field.name}: ${field.description}`)
    if (field.hint) console.log(`   💡 ${field.hint}`)
    if (field.hasValidation) console.log(`   ✓ Has validation rules`)
  })
  
  console.log('\n' + '='.repeat(50) + '\n')

  // In a real application, you would conduct the conversation:
  // const result = await BusinessPlan.gather()
  // console.log('Collected data:', result.getData())

  console.log('Contact Form Fields:')
  const contactPreview = ContactForm.getFieldPreview()
  contactPreview.forEach((field, index) => {
    console.log(`${index + 1}. ${field.description}`)
    if (field.hint) console.log(`   💡 ${field.hint}`)
  })

  console.log('\n' + '='.repeat(50) + '\n')

  console.log('Bug Report Fields:')
  const bugPreview = BugReport.getFieldPreview()
  bugPreview.forEach((field, index) => {
    console.log(`${index + 1}. ${field.description}`)
    if (field.hint) console.log(`   💡 ${field.hint}`)
  })

  console.log('\n' + '='.repeat(50) + '\n')

  // Show the decorator approach vs builder approach
  console.log('Decorator Approach Benefits:')
  console.log('✅ Clean, declarative syntax similar to Python')
  console.log('✅ Type-safe field definitions')
  console.log('✅ Excellent IDE support with decorators')
  console.log('✅ Familiar pattern for developers coming from other frameworks')
  console.log('✅ Direct parity with Python Chatfield API')

  console.log('\nTo conduct actual conversations, integrate with React components or call:')
  console.log('const result = await YourGathererClass.gather()')
}

// Export all examples
export {
  ContactForm,
  BusinessPlan,
  BugReport,
  UserFeedback,
  JobApplication,
  EventPlanning,
  demonstrateDecorators
}

// Run demonstration if this file is executed directly
if (require.main === module) {
  demonstrateDecorators().catch(console.error)
}