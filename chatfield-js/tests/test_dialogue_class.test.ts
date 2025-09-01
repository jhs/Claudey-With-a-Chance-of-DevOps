/**
 * Test the Interview base class inheritance pattern.
 * Mirrors Python's test_dialogue_class.py
 */

import { chatfield } from '../src/builders/gatherer-builder'

describe('TestInterviewInheritancePattern', () => {
  test('test_simple_interview', () => {
    const instance = chatfield()
      .type('SimpleInterview')
      .desc('Test interview')
      .field('name').desc('Your name')
      .field('email').desc('Your email')
      .build()

    const meta = instance._chatfield

    // Should have metadata
    expect(meta.desc).toBe('Test interview')
    expect('name' in meta.fields).toBe(true)
    expect('email' in meta.fields).toBe(true)
  })

  test('test_interview_with_field_decorators', () => {
    const instance = chatfield()
      .type('DecoratedInterview')
      .desc('Test with decorators')
      .field('problem')
        .desc('Your problem')
        .must('be specific')
        .reject('vague')
      .field('solution')
        .desc('Your solution')
        .hint('Think carefully')
      .build()

    const meta = instance._chatfield

    // Check problem field
    const problemField = meta.fields.problem
    expect(problemField.specs.must).toContain('be specific')
    expect(problemField.specs.reject).toContain('vague')

    // Check solution field
    const solutionField = meta.fields.solution
    expect(solutionField.specs.hint).toContain('Think carefully')
  })

  test('test_interview_with_class_decorators', () => {
    const instance = chatfield()
      .type('DecoratedInterview')
      .desc('Role-based interview')
      .alice().type('Interviewer')
      .bob().type('Candidate')
      .field('question').desc('Your question')
      .build()

    const meta = instance._chatfield

    expect(meta.roles.alice.type).toBe('Interviewer')
    expect(meta.roles.bob.type).toBe('Candidate')
    expect('question' in meta.fields).toBe(true)
  })

  test('test_complex_interview', () => {
    const instance = chatfield()
      .type('ComplexInterview')
      .desc('Technical interview process')
      .alice()
        .type('Technical Interviewer')
        .trait('thorough')
      .bob()
        .type('Senior Developer')
        .trait('experienced')
      .field('experience')
        .desc('Describe your experience')
        .must('include specific examples')
        .reject('generic answers')
        .hint('Think about real-world scenarios')
      .field('goals')
        .desc('Your career goals')
        .must('be measurable')
      .build()

    const meta = instance._chatfield

    // Class metadata
    expect(meta.desc).toBe('Technical interview process')

    // Roles
    expect(meta.roles.alice.type).toBe('Technical Interviewer')
    expect(meta.roles.alice.traits).toContain('thorough')
    expect(meta.roles.bob.type).toBe('Senior Developer')
    expect(meta.roles.bob.traits).toContain('experienced')

    // Fields
    expect('experience' in meta.fields).toBe(true)
    expect('goals' in meta.fields).toBe(true)

    // Field decorators
    const expField = meta.fields.experience
    expect(expField.specs.must).toContain('include specific examples')
    expect(expField.specs.reject).toContain('generic answers')
    expect(expField.specs.hint).toContain('Think about real-world scenarios')

    const goalsField = meta.fields.goals
    expect(goalsField.specs.must).toContain('be measurable')
  })
})