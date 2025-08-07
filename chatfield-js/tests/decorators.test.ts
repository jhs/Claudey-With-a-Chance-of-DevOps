/**
 * Tests for decorator functionality
 */

import { gather, field, must, reject, hint, user, agent } from '../src/decorators'
import { MockLLMBackend } from '../src/backends/llm-backend'

describe('Decorator API', () => {
  describe('Basic decorator functionality', () => {
    test('should create gatherer with single field', () => {
      @gather
      class SimpleGatherer {
        @field("Your name")
        name!: string
      }

      const meta = SimpleGatherer._chatfield_meta
      expect(meta).toBeDefined()
      expect(meta.getFieldNames()).toEqual(['name'])
      
      const nameField = meta.getField('name')
      expect(nameField?.description).toBe('Your name')
    })

    test('should handle multiple fields', () => {
      @gather
      class MultiFieldGatherer {
        @field("Your name")
        name!: string

        @field("Your email")  
        email!: string

        @field("Your message")
        message!: string
      }

      const meta = MultiFieldGatherer._chatfield_meta
      expect(meta.getFieldNames()).toEqual(['name', 'email', 'message'])
      
      expect(meta.getField('name')?.description).toBe('Your name')
      expect(meta.getField('email')?.description).toBe('Your email')
      expect(meta.getField('message')?.description).toBe('Your message')
    })

    test('should handle validation decorators', () => {
      @gather
      class ValidatedGatherer {
        @field("Your name")
        @must("include first and last name")
        @must("be specific")
        @reject("generic names")
        @hint("Use your real name")
        name!: string
      }

      const meta = ValidatedGatherer._chatfield_meta
      const nameField = meta.getField('name')!
      
      expect(nameField.mustRules).toEqual(['include first and last name', 'be specific'])
      expect(nameField.rejectRules).toEqual(['generic names'])
      expect(nameField.hint).toBe('Use your real name')
      expect(nameField.hasValidationRules()).toBe(true)
    })

    test('should handle user and agent context', () => {
      @gather
      @user("startup founder")
      @user("technical background")
      @agent("be patient")
      @agent("ask follow-up questions")
      class ContextGatherer {
        @field("Your idea")
        idea!: string
      }

      const meta = ContextGatherer._chatfield_meta
      expect(meta.userContext).toEqual(['startup founder', 'technical background'])
      expect(meta.agentContext).toEqual(['be patient', 'ask follow-up questions'])
    })
  })

  describe('Field decorator options', () => {
    test('should handle field with inline options', () => {
      @gather
      class InlineOptionsGatherer {
        @field("Your email", {
          must: "valid email format",
          reject: "temporary emails",
          hint: "Use your work email"
        })
        email!: string
      }

      const meta = InlineOptionsGatherer._chatfield_meta
      const emailField = meta.getField('email')!
      
      expect(emailField.mustRules).toEqual(['valid email format'])
      expect(emailField.rejectRules).toEqual(['temporary emails'])
      expect(emailField.hint).toBe('Use your work email')
    })

    test('should handle field with multiple inline rules', () => {
      @gather
      class MultiRulesGatherer {
        @field("Your project", {
          must: ["include timeline", "mention budget"],
          reject: ["vague descriptions", "unrealistic goals"]
        })
        project!: string
      }

      const meta = MultiRulesGatherer._chatfield_meta
      const projectField = meta.getField('project')!
      
      expect(projectField.mustRules).toEqual(['include timeline', 'mention budget'])
      expect(projectField.rejectRules).toEqual(['vague descriptions', 'unrealistic goals'])
    })
  })

  describe('Decorator stacking and combinations', () => {
    test('should combine field decorator with separate validation decorators', () => {
      @gather
      class CombinedDecoratorsGatherer {
        @field("Your concept")
        @must("include target market")
        @reject("vague ideas")
        @hint("Be specific")
        concept!: string
      }

      const meta = CombinedDecoratorsGatherer._chatfield_meta
      const conceptField = meta.getField('concept')!
      
      expect(conceptField.description).toBe('Your concept')
      expect(conceptField.mustRules).toEqual(['include target market'])
      expect(conceptField.rejectRules).toEqual(['vague ideas'])
      expect(conceptField.hint).toBe('Be specific')
    })

    test('should handle validation decorators without field decorator', () => {
      @gather
      class ValidationOnlyGatherer {
        @must("include timeline")
        @reject("be vague")
        @hint("Think about deadlines")
        project!: string
      }

      const meta = ValidationOnlyGatherer._chatfield_meta
      const projectField = meta.getField('project')!
      
      // Should fallback to field name as description
      expect(projectField.description).toBe('project')
      expect(projectField.mustRules).toEqual(['include timeline'])
      expect(projectField.rejectRules).toEqual(['be vague'])
      expect(projectField.hint).toBe('Think about deadlines')
    })
  })

  describe('Gatherer class methods', () => {
    test('should have static gather method', () => {
      @gather
      class TestGatherer {
        @field("Test field")
        test!: string
      }

      expect(typeof TestGatherer.gather).toBe('function')
    })

    test('should have getFieldPreview method', () => {
      @gather
      class PreviewGatherer {
        @field("Your name")
        @hint("Real name please")
        name!: string

        @field("Your email")
        @must("valid format")
        email!: string
      }

      const preview = PreviewGatherer.getFieldPreview()
      expect(preview).toHaveLength(2)
      
      expect(preview[0]).toEqual({
        name: 'name',
        description: 'Your name',
        hasValidation: false,
        hint: 'Real name please'
      })
      
      expect(preview[1]).toEqual({
        name: 'email', 
        description: 'Your email',
        hasValidation: true,
        hint: undefined
      })
    })

    test('should preserve class name', () => {
      @gather
      class MyCustomGatherer {
        @field("Test")
        test!: string
      }

      expect(MyCustomGatherer.name).toBe('MyCustomGatherer')
    })
  })

  describe('Complex examples', () => {
    test('should handle business plan gatherer', () => {
      @gather
      @user("startup founder")
      @agent("be patient and thorough")
      class BusinessPlan {
        @field("Your business concept")
        @must("include target market")
        @hint("What are you building and for whom?")
        concept!: string

        @field("What problem does it solve?")
        @must("specific problem statement")
        @reject("vague problems")
        problem!: string

        @field("How will you make money?")
        @must("revenue model")
        revenue!: string
      }

      const meta = BusinessPlan._chatfield_meta
      
      // Check context
      expect(meta.userContext).toEqual(['startup founder'])
      expect(meta.agentContext).toEqual(['be patient and thorough'])
      
      // Check fields
      expect(meta.getFieldNames()).toEqual(['concept', 'problem', 'revenue'])
      
      // Check concept field
      const conceptField = meta.getField('concept')!
      expect(conceptField.description).toBe('Your business concept')
      expect(conceptField.mustRules).toEqual(['include target market'])
      expect(conceptField.hint).toBe('What are you building and for whom?')
      
      // Check problem field
      const problemField = meta.getField('problem')!
      expect(problemField.mustRules).toEqual(['specific problem statement'])
      expect(problemField.rejectRules).toEqual(['vague problems'])
      
      // Check revenue field
      const revenueField = meta.getField('revenue')!
      expect(revenueField.mustRules).toEqual(['revenue model'])
    })

    test('should handle contact form gatherer', () => {
      @gather
      @user("potential customer")
      @agent("friendly and helpful")
      class ContactForm {
        @field("Your full name")
        @must("first and last name")
        name!: string

        @field("Your email address")
        @must("valid email format")
        @reject("temporary email providers")
        email!: string

        @field("Your message")
        @must("at least 20 characters")
        @hint("Please describe your inquiry")
        message!: string
      }

      const preview = ContactForm.getFieldPreview()
      expect(preview).toHaveLength(3)
      
      preview.forEach(field => {
        expect(field.hasValidation).toBe(true)
      })
      
      expect(preview[2].hint).toBe('Please describe your inquiry')
    })
  })

  describe('Error handling and edge cases', () => {
    test('should handle empty gatherer', () => {
      @gather
      class EmptyGatherer {
        // No fields
      }

      const meta = EmptyGatherer._chatfield_meta
      expect(meta.getFieldNames()).toEqual([])
      expect(meta.getFields()).toEqual([])
    })

    test('should handle gatherer with only context decorators', () => {
      @gather
      @user("test user")
      @agent("test agent")  
      class ContextOnlyGatherer {
        // No fields, only context
      }

      const meta = ContextOnlyGatherer._chatfield_meta
      expect(meta.userContext).toEqual(['test user'])
      expect(meta.agentContext).toEqual(['test agent'])
      expect(meta.getFieldNames()).toEqual([])
    })

    test('should handle multiple decorators on same field', () => {
      @gather
      class MultiDecoratorGatherer {
        @field("Your input")
        @must("rule 1")
        @must("rule 2") 
        @must("rule 3")
        @reject("bad thing 1")
        @reject("bad thing 2")
        @hint("helpful tip")
        input!: string
      }

      const meta = MultiDecoratorGatherer._chatfield_meta
      const inputField = meta.getField('input')!
      
      expect(inputField.mustRules).toEqual(['rule 1', 'rule 2', 'rule 3'])
      expect(inputField.rejectRules).toEqual(['bad thing 1', 'bad thing 2'])
      expect(inputField.hint).toBe('helpful tip')
    })
  })

  describe('Integration with conversation system', () => {
    test('should work with mock conversation', async () => {
      @gather
      class TestGatherer {
        @field("Your name")
        @must("be specific")
        name!: string
      }

      // Mock the conversation system would be integrated here
      // This tests that the metadata is properly structured
      const meta = TestGatherer._chatfield_meta
      expect(meta).toBeDefined()
      expect(meta.getField('name')?.hasValidationRules()).toBe(true)
    })
  })
})