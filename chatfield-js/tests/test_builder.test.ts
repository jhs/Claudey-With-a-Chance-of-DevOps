/**
 * Unit tests for Chatfield builder pattern.
 * Mirrors Python's test_builder.py
 */

import { chatfield } from '../src/builders/gatherer-builder'

describe('TestBasicBuilder', () => {
  test('test_simple_interview', () => {
    const instance = chatfield()
      .type('SimpleInterview')
      .desc('A simple interview')
      .field('name').desc('Your name')
      .field('email').desc('Your email')
      .build()

    const meta = instance._chatfield
    expect(meta.type).toBe('SimpleInterview')
    expect(meta.desc).toBe('A simple interview')
    expect(Object.keys(meta.fields).length).toBe(2)
    expect('name' in meta.fields).toBe(true)
    expect('email' in meta.fields).toBe(true)
    expect(meta.fields.name.desc).toBe('Your name')
    expect(meta.fields.email.desc).toBe('Your email')
  })

  test('test_field_validation_rules', () => {
    const instance = chatfield()
      .type('ValidatedInterview')
      .field('field')
        .desc('Test field')
        .must('specific requirement')
        .reject('avoid this')
        .hint('Helpful tip')
      .build()

    const fieldMeta = instance._chatfield.fields.field
    expect(fieldMeta.specs.must).toContain('specific requirement')
    expect(fieldMeta.specs.reject).toContain('avoid this')
    expect(fieldMeta.specs.hint).toContain('Helpful tip')
  })

  test('test_multiple_validation_rules', () => {
    const instance = chatfield()
      .type('MultiRuleInterview')
      .field('field')
        .desc('Test field')
        .must('rule 1')
        .must('rule 2')
        .must('rule 3')
      .build()

    const fieldMeta = instance._chatfield.fields.field
    // Builder should maintain order
    expect(fieldMeta.specs.must).toEqual(['rule 1', 'rule 2', 'rule 3'])
  })

  test('test_multiple_hints', () => {
    const instance = chatfield()
      .type('MultiHintInterview')
      .field('field')
        .desc('Test field with multiple hints')
        .hint('First hint')
        .hint('Second hint')
        .hint('Third hint')
      .build()

    const fieldMeta = instance._chatfield.fields.field
    expect(fieldMeta.specs.hint).toEqual(['First hint', 'Second hint', 'Third hint'])
    expect(fieldMeta.specs.hint.length).toBe(3)
  })

  test('test_combined_field_features', () => {
    const instance = chatfield()
      .type('CombinedInterview')
      .field('complex_field')
        .desc('Complex field')
        .must('required info')
        .reject('forbidden content')
        .hint('Helpful guidance')
      .build()

    const fieldMeta = instance._chatfield.fields.complex_field

    expect(fieldMeta.desc).toBe('Complex field')
    expect(fieldMeta.specs.must).toContain('required info')
    expect(fieldMeta.specs.reject).toContain('forbidden content')
    expect(fieldMeta.specs.hint).toContain('Helpful guidance')
  })
})

describe('TestRoleConfiguration', () => {
  test('test_alice_role', () => {
    const instance = chatfield()
      .type('WithAlice')
      .alice().type('Senior Developer')
      .field('field').desc('Test field')
      .build()

    const meta = instance._chatfield
    expect(meta.roles.alice.type).toBe('Senior Developer')
  })

  test('test_alice_traits', () => {
    const instance = chatfield()
      .type('WithAliceTraits')
      .alice()
        .type('Interviewer')
        .trait('patient')
        .trait('thorough')
      .field('field').desc('Test field')
      .build()

    const meta = instance._chatfield
    expect(meta.roles.alice.type).toBe('Interviewer')
    expect(meta.roles.alice.traits).toContain('patient')
    expect(meta.roles.alice.traits).toContain('thorough')
  })

  test('test_bob_role', () => {
    const instance = chatfield()
      .type('WithBob')
      .bob().type('Job Candidate')
      .field('field').desc('Test field')
      .build()

    const meta = instance._chatfield
    expect(meta.roles.bob.type).toBe('Job Candidate')
  })

  test('test_bob_traits', () => {
    const instance = chatfield()
      .type('WithBobTraits')
      .bob()
        .type('User')
        .trait('technical')
        .trait('curious')
      .field('field').desc('Test field')
      .build()

    const meta = instance._chatfield
    expect(meta.roles.bob.type).toBe('User')
    expect(meta.roles.bob.traits).toContain('technical')
    expect(meta.roles.bob.traits).toContain('curious')
  })

  test('test_both_roles', () => {
    const instance = chatfield()
      .type('BothRoles')
      .alice()
        .type('Interviewer')
        .trait('professional')
      .bob()
        .type('Candidate')
        .trait('experienced')
      .field('field').desc('Test field')
      .build()

    const meta = instance._chatfield
    expect(meta.roles.alice.type).toBe('Interviewer')
    expect(meta.roles.alice.traits).toContain('professional')
    expect(meta.roles.bob.type).toBe('Candidate')
    expect(meta.roles.bob.traits).toContain('experienced')
  })
})

describe('TestTypeTransformations', () => {
  test('test_basic_type_transformations', () => {
    const instance = chatfield()
      .type('TypedInterview')
      .field('age')
        .desc('Your age')
        .as_int()
      .field('salary')
        .desc('Expected salary')
        .as_float()
      .field('active')
        .desc('Are you active?')
        .as_bool()
      .field('confidence')
        .desc('Confidence level')
        .as_percent()
      .build()

    expect('as_int' in instance._chatfield.fields.age.casts).toBe(true)
    expect('as_float' in instance._chatfield.fields.salary.casts).toBe(true)
    expect('as_bool' in instance._chatfield.fields.active.casts).toBe(true)
    expect('as_percent' in instance._chatfield.fields.confidence.casts).toBe(true)
  })

  test('test_language_transformations', () => {
    const instance = chatfield()
      .type('MultiLangInterview')
      .field('greeting')
        .desc('Say hello')
        .as_lang.fr()
        .as_lang.es()
        .as_lang.de()
      .build()

    const fieldCasts = instance._chatfield.fields.greeting.casts
    expect('as_lang_fr' in fieldCasts).toBe(true)
    expect('as_lang_es' in fieldCasts).toBe(true)
    expect('as_lang_de' in fieldCasts).toBe(true)
  })

  test('test_sub_attribute_transformations', () => {
    const instance = chatfield()
      .type('SubAttributeInterview')
      .field('number')
        .desc('A number')
        .as_bool.even('True if even')
        .as_bool.positive('True if positive')
        .as_str.uppercase('In uppercase')
        .as_str.lowercase('In lowercase')
      .build()

    const fieldCasts = instance._chatfield.fields.number.casts
    expect('as_bool_even' in fieldCasts).toBe(true)
    expect('as_bool_positive' in fieldCasts).toBe(true)
    expect('as_str_uppercase' in fieldCasts).toBe(true)
    expect('as_str_lowercase' in fieldCasts).toBe(true)
  })
})

describe('TestCardinalityChoices', () => {
  test('test_as_one_choice', () => {
    const instance = chatfield()
      .type('ChoiceInterview')
      .field('color')
        .desc('Favorite color')
        .as_one.color('red', 'green', 'blue')
      .build()

    const colorCast = instance._chatfield.fields.color.casts.as_one_color
    expect(colorCast.type).toBe('choice')
    expect(colorCast.choices).toEqual(['red', 'green', 'blue'])
    expect(colorCast.null).toBe(false)
    expect(colorCast.multi).toBe(false)
  })

  test('test_as_maybe_choice', () => {
    const instance = chatfield()
      .type('MaybeInterview')
      .field('priority')
        .desc('Priority level')
        .as_maybe.priority('low', 'medium', 'high')
      .build()

    const priorityCast = instance._chatfield.fields.priority.casts.as_maybe_priority
    expect(priorityCast.type).toBe('choice')
    expect(priorityCast.choices).toEqual(['low', 'medium', 'high'])
    expect(priorityCast.null).toBe(true)
    expect(priorityCast.multi).toBe(false)
  })

  test('test_as_multi_choice', () => {
    const instance = chatfield()
      .type('MultiInterview')
      .field('languages')
        .desc('Programming languages')
        .as_multi.languages('python', 'javascript', 'rust', 'go')
      .build()

    const langCast = instance._chatfield.fields.languages.casts.as_multi_languages
    expect(langCast.type).toBe('choice')
    expect(langCast.choices).toEqual(['python', 'javascript', 'rust', 'go'])
    expect(langCast.null).toBe(false)
    expect(langCast.multi).toBe(true)
  })

  test('test_as_any_choice', () => {
    const instance = chatfield()
      .type('AnyInterview')
      .field('reviewers')
        .desc('Code reviewers')
        .as_any.reviewers('alice', 'bob', 'charlie', 'diana')
      .build()

    const reviewerCast = instance._chatfield.fields.reviewers.casts.as_any_reviewers
    expect(reviewerCast.type).toBe('choice')
    expect(reviewerCast.choices).toEqual(['alice', 'bob', 'charlie', 'diana'])
    expect(reviewerCast.null).toBe(true)
    expect(reviewerCast.multi).toBe(true)
  })
})

describe('TestBuilderEdgeCases', () => {
  test('test_empty_interview', () => {
    const instance = chatfield()
      .type('EmptyInterview')
      .desc('Empty interview with no fields')
      .build()

    expect(instance._chatfield.type).toBe('EmptyInterview')
    expect(instance._chatfield.desc).toBe('Empty interview with no fields')
    expect(Object.keys(instance._chatfield.fields).length).toBe(0)
  })

  test('test_minimal_interview', () => {
    const instance = chatfield().build()

    expect(instance._chatfield.type).toBe('')
    expect(instance._chatfield.desc).toBe('')
    expect(Object.keys(instance._chatfield.fields).length).toBe(0)
  })

  test('test_field_order_preservation', () => {
    const instance = chatfield()
      .type('OrderedInterview')
      .field('first').desc('First field')
      .field('second').desc('Second field')
      .field('third').desc('Third field')
      .field('fourth').desc('Fourth field')
      .build()

    const fieldNames = Object.keys(instance._chatfield.fields)
    expect(fieldNames).toEqual(['first', 'second', 'third', 'fourth'])
  })

  test('test_mixed_features', () => {
    const instance = chatfield()
      .type('ComplexInterview')
      .desc('A complex interview with all features')
      .alice()
        .type('Senior Interviewer')
        .trait('thorough')
        .trait('patient')
      .bob()
        .type('Experienced Developer')
        .trait('technical')
      .field('experience')
        .desc('Years of experience')
        .must('be specific')
        .must('include examples')
        .reject('vague answers')
        .hint('Think about your best projects')
        .as_int()
        .as_lang.fr()
      .field('skills')
        .desc('Technical skills')
        .as_multi.skills('python', 'javascript', 'rust')
      .build()

    const meta = instance._chatfield

    // Check interview metadata
    expect(meta.type).toBe('ComplexInterview')
    expect(meta.desc).toBe('A complex interview with all features')

    // Check roles
    expect(meta.roles.alice.type).toBe('Senior Interviewer')
    expect(meta.roles.alice.traits).toContain('thorough')
    expect(meta.roles.alice.traits).toContain('patient')
    expect(meta.roles.bob.type).toBe('Experienced Developer')
    expect(meta.roles.bob.traits).toContain('technical')

    // Check fields
    const expField = meta.fields.experience
    expect(expField.desc).toBe('Years of experience')
    expect(expField.specs.must).toContain('be specific')
    expect(expField.specs.must).toContain('include examples')
    expect(expField.specs.reject).toContain('vague answers')
    expect(expField.specs.hint).toContain('Think about your best projects')
    expect('as_int' in expField.casts).toBe(true)
    expect('as_lang_fr' in expField.casts).toBe(true)

    const skillsField = meta.fields.skills
    expect('as_multi_skills' in skillsField.casts).toBe(true)
  })
})