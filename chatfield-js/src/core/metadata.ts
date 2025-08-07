/**
 * Core metadata classes for Chatfield gatherers
 */

export class FieldMeta {
  public name: string
  public description: string
  public mustRules: string[]
  public rejectRules: string[]
  public hint?: string
  public whenCondition?: (data: Record<string, string>) => boolean

  constructor(name: string, description: string) {
    this.name = name
    this.description = description
    this.mustRules = []
    this.rejectRules = []
  }

  /**
   * Add a validation requirement
   */
  addMustRule(rule: string): void {
    this.mustRules.push(rule)
  }

  /**
   * Add a validation rejection rule
   */
  addRejectRule(rule: string): void {
    this.rejectRules.push(rule)
  }

  /**
   * Set the hint tooltip
   */
  setHint(hint: string): void {
    this.hint = hint
  }

  /**
   * Set conditional visibility logic
   */
  setWhenCondition(condition: (data: Record<string, string>) => boolean): void {
    this.whenCondition = condition
  }

  /**
   * Check if this field has any validation rules
   */
  hasValidationRules(): boolean {
    return this.mustRules.length > 0 || this.rejectRules.length > 0
  }

  /**
   * Check if this field should be shown based on current data
   */
  shouldShow(collectedData: Record<string, string>): boolean {
    if (!this.whenCondition) {
      return true
    }
    return this.whenCondition(collectedData)
  }

  /**
   * Create a copy of this field metadata
   */
  clone(): FieldMeta {
    const clone = new FieldMeta(this.name, this.description)
    clone.mustRules = [...this.mustRules]
    clone.rejectRules = [...this.rejectRules]
    clone.hint = this.hint
    clone.whenCondition = this.whenCondition
    return clone
  }
}

export class GathererMeta {
  public userContext: string[]
  public agentContext: string[]
  public docstring: string
  public fields: Map<string, FieldMeta>
  private fieldOrder: string[]

  constructor() {
    this.userContext = []
    this.agentContext = []
    this.docstring = ''
    this.fields = new Map()
    this.fieldOrder = []
  }

  /**
   * Add user context information
   */
  addUserContext(context: string): void {
    this.userContext.push(context)
  }

  /**
   * Add agent behavior context
   */
  addAgentContext(context: string): void {
    this.agentContext.push(context)
  }

  /**
   * Set the class docstring
   */
  setDocstring(docstring: string): void {
    this.docstring = docstring.trim()
  }

  /**
   * Add a field and return its metadata object
   */
  addField(name: string, description: string): FieldMeta {
    const fieldMeta = new FieldMeta(name, description)
    this.fields.set(name, fieldMeta)
    
    // Maintain field order
    if (!this.fieldOrder.includes(name)) {
      this.fieldOrder.push(name)
    }
    
    return fieldMeta
  }

  /**
   * Get field metadata by name
   */
  getField(name: string): FieldMeta | undefined {
    return this.fields.get(name)
  }

  /**
   * Get all field names in order
   */
  getFieldNames(): string[] {
    return [...this.fieldOrder]
  }

  /**
   * Get all fields in order
   */
  getFields(): FieldMeta[] {
    return this.fieldOrder.map(name => this.fields.get(name)!).filter(Boolean)
  }

  /**
   * Check if this gatherer has any context information
   */
  hasContext(): boolean {
    return this.userContext.length > 0 || 
           this.agentContext.length > 0 || 
           this.docstring.length > 0
  }

  /**
   * Get fields that should be shown given current data
   */
  getVisibleFields(collectedData: Record<string, string>): FieldMeta[] {
    return this.getFields().filter(field => field.shouldShow(collectedData))
  }

  /**
   * Create a copy of this gatherer metadata
   */
  clone(): GathererMeta {
    const clone = new GathererMeta()
    clone.userContext = [...this.userContext]
    clone.agentContext = [...this.agentContext]
    clone.docstring = this.docstring
    clone.fieldOrder = [...this.fieldOrder]
    
    // Clone all fields
    for (const [name, field] of this.fields.entries()) {
      clone.fields.set(name, field.clone())
    }
    
    return clone
  }
}