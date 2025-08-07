/**
 * Schema-based builder for creating gatherers from configuration objects
 */

import { GathererMeta } from '../core/metadata'
import { Gatherer } from '../core/gatherer'
import { GathererSchema, GathererOptions } from '../core/types'

/**
 * Create a gatherer from a schema configuration
 */
export function createGatherer(schema: GathererSchema, options?: GathererOptions): Gatherer {
  const meta = new GathererMeta()

  // Set docstring
  if (schema.docstring) {
    meta.setDocstring(schema.docstring)
  }

  // Add user context
  if (schema.userContext) {
    schema.userContext.forEach(context => meta.addUserContext(context))
  }

  // Add agent context
  if (schema.agentContext) {
    schema.agentContext.forEach(behavior => meta.addAgentContext(behavior))
  }

  // Add fields
  Object.entries(schema.fields).forEach(([name, fieldConfig]) => {
    const fieldMeta = meta.addField(name, fieldConfig.description)

    // Add validation rules
    if (fieldConfig.must) {
      fieldConfig.must.forEach(rule => fieldMeta.addMustRule(rule))
    }

    if (fieldConfig.reject) {
      fieldConfig.reject.forEach(rule => fieldMeta.addRejectRule(rule))
    }

    // Add hint
    if (fieldConfig.hint) {
      fieldMeta.setHint(fieldConfig.hint)
    }

    // Add conditional logic
    if (fieldConfig.when) {
      fieldMeta.setWhenCondition(fieldConfig.when)
    }
  })

  return new Gatherer(meta, options)
}

/**
 * Validate a schema configuration
 */
export function validateSchema(schema: GathererSchema): {
  isValid: boolean
  errors: string[]
} {
  const errors: string[] = []

  // Check if fields exist
  if (!schema.fields || Object.keys(schema.fields).length === 0) {
    errors.push('Schema must have at least one field')
  }

  // Validate field configurations
  Object.entries(schema.fields || {}).forEach(([name, fieldConfig]) => {
    if (!name || typeof name !== 'string') {
      errors.push('Field names must be non-empty strings')
    }

    if (!fieldConfig.description || typeof fieldConfig.description !== 'string') {
      errors.push(`Field '${name}' must have a description`)
    }

    // Validate must rules
    if (fieldConfig.must && !Array.isArray(fieldConfig.must)) {
      errors.push(`Field '${name}' must rules must be an array of strings`)
    }

    // Validate reject rules
    if (fieldConfig.reject && !Array.isArray(fieldConfig.reject)) {
      errors.push(`Field '${name}' reject rules must be an array of strings`)
    }

    // Validate hint
    if (fieldConfig.hint && typeof fieldConfig.hint !== 'string') {
      errors.push(`Field '${name}' hint must be a string`)
    }

    // Validate when condition
    if (fieldConfig.when && typeof fieldConfig.when !== 'function') {
      errors.push(`Field '${name}' when condition must be a function`)
    }
  })

  // Validate context arrays
  if (schema.userContext && !Array.isArray(schema.userContext)) {
    errors.push('userContext must be an array of strings')
  }

  if (schema.agentContext && !Array.isArray(schema.agentContext)) {
    errors.push('agentContext must be an array of strings')
  }

  // Validate docstring
  if (schema.docstring && typeof schema.docstring !== 'string') {
    errors.push('docstring must be a string')
  }

  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Merge multiple schemas together
 */
export function mergeSchemas(...schemas: GathererSchema[]): GathererSchema {
  const merged: GathererSchema = {
    fields: {},
    userContext: [],
    agentContext: [],
    docstring: ''
  }

  schemas.forEach(schema => {
    // Merge fields
    Object.assign(merged.fields, schema.fields)

    // Merge user context
    if (schema.userContext) {
      merged.userContext!.push(...schema.userContext)
    }

    // Merge agent context
    if (schema.agentContext) {
      merged.agentContext!.push(...schema.agentContext)
    }

    // Use last non-empty docstring
    if (schema.docstring) {
      merged.docstring = schema.docstring
    }
  })

  return merged
}

/**
 * Convert a gatherer back to schema format
 */
export function gathererToSchema(gatherer: Gatherer): GathererSchema {
  const meta = gatherer.getMeta()
  const schema: GathererSchema = {
    fields: {},
    userContext: meta.userContext.length > 0 ? [...meta.userContext] : undefined,
    agentContext: meta.agentContext.length > 0 ? [...meta.agentContext] : undefined,
    docstring: meta.docstring || undefined
  }

  // Convert fields
  meta.getFields().forEach(field => {
    schema.fields[field.name] = {
      description: field.description,
      must: field.mustRules.length > 0 ? [...field.mustRules] : undefined,
      reject: field.rejectRules.length > 0 ? [...field.rejectRules] : undefined,
      hint: field.hint || undefined,
      when: field.whenCondition || undefined
    }
  })

  return schema
}

/**
 * Common schema presets
 */
export const schemaPresets = {
  /**
   * Business plan gathering schema
   */
  businessPlan: (): GathererSchema => ({
    docstring: "I'll help you outline your business plan by gathering key information about your venture.",
    userContext: ["entrepreneur", "startup founder"],
    agentContext: ["patient and thorough", "business-focused"],
    fields: {
      concept: {
        description: "What's your business concept or main product/service?",
        must: ["specific description"],
        hint: "Describe what you're building and who it's for"
      },
      market: {
        description: "Who is your target market?",
        must: ["target audience"],
        hint: "Be specific about demographics, size, and characteristics"
      },
      problem: {
        description: "What problem does your business solve?",
        must: ["clear problem statement"],
        hint: "Describe the pain point your customers currently experience"
      },
      solution: {
        description: "How does your product/service solve this problem?",
        must: ["solution description"],
        hint: "Explain your unique approach or methodology"
      },
      revenue: {
        description: "How will you make money?",
        must: ["revenue model"],
        hint: "Subscription, one-time purchase, advertising, etc."
      }
    }
  }),

  /**
   * Bug report gathering schema
   */
  bugReport: (): GathererSchema => ({
    docstring: "Let's gather information about the bug you've encountered so we can fix it quickly.",
    userContext: ["software user", "experiencing issues"],
    agentContext: ["focused on technical details", "systematic"],
    fields: {
      summary: {
        description: "What's a brief summary of the issue?",
        must: ["concise description"],
        hint: "One sentence describing what went wrong"
      },
      steps: {
        description: "What steps can we follow to reproduce this bug?",
        must: ["step-by-step instructions"],
        hint: "List the exact actions that lead to the problem"
      },
      expected: {
        description: "What did you expect to happen?",
        must: ["expected behavior"],
        hint: "Describe the correct behavior you were expecting"
      },
      actual: {
        description: "What actually happened instead?",
        must: ["actual behavior"],
        hint: "Describe what went wrong or what you saw instead"
      },
      environment: {
        description: "What system are you using?",
        must: ["system details"],
        hint: "OS, browser, app version, etc."
      }
    }
  }),

  /**
   * User feedback gathering schema
   */
  userFeedback: (): GathererSchema => ({
    docstring: "Your feedback helps us improve! Let's gather your thoughts and suggestions.",
    userContext: ["product user", "providing feedback"],
    agentContext: ["appreciative", "constructive", "follow-up focused"],
    fields: {
      experience: {
        description: "How would you rate your overall experience?",
        must: ["rating or description"],
        hint: "Scale of 1-10 or descriptive feedback"
      },
      likes: {
        description: "What do you like most about the product?",
        hint: "Features, design, functionality, etc."
      },
      dislikes: {
        description: "What could be improved?",
        hint: "Pain points, confusing features, missing functionality"
      },
      suggestions: {
        description: "Do you have any specific suggestions?",
        hint: "New features, changes, or improvements you'd like to see"
      },
      recommend: {
        description: "Would you recommend this to others? Why or why not?",
        must: ["yes/no with reasoning"],
        hint: "Consider what you'd tell a friend or colleague"
      }
    }
  })
}