/**
 * Basic usage examples for Chatfield
 */

import { chatfield, simpleGatherer } from '../src'
import { OpenAIBackend, MockLLMBackend } from '../src'

// Example 1: Simple contact form
const ContactForm = chatfield()
  .field('name', 'Your full name')
  .must('include first and last name')
  .field('email', 'Your email address')
  .must('valid email format')
  .reject('temporary email addresses')
  .field('message', 'Your message')
  .must('at least 20 characters')
  .hint('Please describe your inquiry in detail')
  .build()

// Example 2: Business plan gathering
const BusinessPlan = chatfield()
  .docstring("I'll help you outline your business plan by gathering key information about your venture.")
  .user('entrepreneur or startup founder')
  .agent('patient and thorough')
  .agent('ask follow-up questions when answers seem incomplete')
  
  .field('concept', 'What is your business concept?')
  .must('include target market')
  .must('describe the product or service')
  .hint('Think about what you\'re building and who it\'s for')
  
  .field('problem', 'What specific problem does your business solve?')
  .must('clear problem statement')
  .reject('vague or generic problems')
  .hint('Describe the pain point your customers currently experience')
  
  .field('solution', 'How does your product/service solve this problem?')
  .must('explain unique approach')
  .when(data => data.concept && data.problem) // Only ask if previous fields completed
  
  .field('market', 'Who is your target market?')
  .must('specific demographics or market segment')
  .hint('Be specific about size, characteristics, and accessibility')
  
  .field('competition', 'Who are your main competitors?')
  .must('name specific companies or alternatives')
  .hint('Include both direct and indirect competitors')
  
  .field('advantage', 'What is your competitive advantage?')
  .must('unique differentiator')
  .when(data => data.competition) // Only ask after competition is known
  
  .field('revenue', 'How will you make money?')
  .must('specific revenue model')
  .hint('Subscription, one-time purchase, advertising, commission, etc.')
  
  .field('funding', 'How much funding do you need to get started?')
  .must('specific amount and time period')
  .when(data => data.revenue) // Only ask after revenue model is clear
  
  .build()

// Example 3: Bug report gathering
const BugReport = chatfield()
  .docstring('Let\'s gather information about the bug you encountered so we can fix it quickly.')
  .user('software user experiencing issues')
  .agent('focused on technical details')
  .agent('systematic and thorough')
  
  .field('summary', 'What\'s a brief summary of the issue?')
  .must('concise description of the problem')
  .hint('One sentence describing what went wrong')
  
  .field('steps', 'What steps can we follow to reproduce this bug?')
  .must('step-by-step instructions')
  .must('specific actions and inputs')
  .hint('List the exact actions that lead to the problem')
  
  .field('expected', 'What did you expect to happen?')
  .must('clear expected behavior')
  .hint('Describe what should have happened normally')
  
  .field('actual', 'What actually happened instead?')
  .must('specific description of incorrect behavior')
  .hint('Include any error messages or unexpected results')
  
  .field('frequency', 'How often does this happen?')
  .hint('Always, sometimes, rarely? Under what conditions?')
  
  .field('environment', 'What system are you using?')
  .must('operating system')
  .must('browser or app version')
  .hint('OS version, browser, device type, etc.')
  
  .field('workaround', 'Have you found any workarounds?')
  .when(data => data.frequency && !data.frequency.toLowerCase().includes('always'))
  .hint('Any temporary solutions or ways to avoid the problem?')
  
  .build()

// Example 4: User feedback collection
const UserFeedback = chatfield()
  .docstring('Your feedback helps us improve! Let\'s gather your thoughts and suggestions.')
  .user('product user providing feedback')
  .agent('appreciative and constructive')
  .agent('ask follow-up questions for clarity')
  
  .field('rating', 'How would you rate your overall experience?')
  .must('rating from 1-10 or descriptive feedback')
  .hint('Consider ease of use, functionality, and value')
  
  .field('likes', 'What do you like most about the product?')
  .hint('Features, design, performance, support, etc.')
  
  .field('dislikes', 'What could be improved?')
  .hint('Pain points, confusing features, missing functionality')
  
  .field('suggestions', 'Do you have any specific suggestions?')
  .when(data => data.dislikes) // Only ask if they mentioned things to improve
  .hint('New features, changes, or improvements you\'d like to see')
  
  .field('use_case', 'How do you primarily use the product?')
  .must('specific use case or scenario')
  .hint('What tasks or goals are you trying to accomplish?')
  
  .field('alternatives', 'What alternatives did you consider?')
  .hint('Other products or solutions you looked at')
  
  .field('recommend', 'Would you recommend this to others?')
  .must('yes/no with reasoning')
  .hint('Consider what you\'d tell a friend or colleague')
  
  .build()

// Example 5: Simple helper usage
const QuickSurvey = simpleGatherer({
  age: 'What is your age?',
  location: 'What city are you in?',
  occupation: 'What do you do for work?',
  interests: 'What are your main interests or hobbies?'
}, {
  docstring: 'Quick demographic survey',
  userContext: ['survey participant'],
  agentContext: ['brief and efficient', 'respect privacy']
})

// Usage examples
async function demonstrateUsage() {
  // Use with OpenAI (requires API key)
  const openaiBackend = new OpenAIBackend({ 
    apiKey: process.env.OPENAI_API_KEY 
  })
  
  // Use with mock for testing
  const mockBackend = new MockLLMBackend()
  mockBackend.addResponse('Hello! I\'d be happy to help you with that.')
  mockBackend.addValidationResponse('VALID')
  
  // Example: Conduct business plan gathering
  console.log('Starting business plan gathering...')
  
  const businessGatherer = BusinessPlan.withOptions({
    llmBackend: mockBackend,
    maxRetryAttempts: 3
  })
  
  // In a real application, this would integrate with your UI
  // For now, we show the field preview
  const preview = businessGatherer.getFieldPreview()
  console.log('Fields to collect:')
  preview.forEach(field => {
    console.log(`- ${field.name}: ${field.description}`)
    if (field.hint) console.log(`  💡 ${field.hint}`)
    if (field.hasValidation) console.log(`  ✓ Has validation rules`)
  })
  
  // The actual conversation would happen through your UI
  // See React examples for integration patterns
  
  console.log('\nTo use with real conversations, integrate with React components or your preferred UI framework.')
}

// Export examples for use in other files
export {
  ContactForm,
  BusinessPlan,
  BugReport,
  UserFeedback,
  QuickSurvey,
  demonstrateUsage
}

// Run demonstration if this file is executed directly
if (require.main === module) {
  demonstrateUsage().catch(console.error)
}