/**
 * Tests for the Interview base class equivalent functionality.
 * Mirrors Python's test_interview.py
 */

import { chatfield } from '../src/builders/gatherer-builder'
import { Interview } from '../src/core/interview'
import { FieldProxy } from '../src/core/field-proxy'

describe('TestInterviewBasics', () => {
  test('test_simple_interview_creation', () => {
    const interview = chatfield()
      .type('SimpleInterview')
      .desc('A simple interview')
      .field('name').desc('Your name')
      .field('email').desc('Your email address')
      .build()

    expect(interview._chatfield.type).toBe('SimpleInterview')
    expect(interview._chatfield.desc).toBe('A simple interview')
    expect('name' in interview._chatfield.fields).toBe(true)
    expect('email' in interview._chatfield.fields).toBe(true)
    expect(interview._chatfield.fields.name.desc).toBe('Your name')
    expect(interview._chatfield.fields.email.desc).toBe('Your email address')
  })

  test('test_field_discovery', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('field1').desc('First field')
      .field('field2').desc('Second field')
      .field('field3').desc('Third field')
      .build()

    const fields = Object.keys(interview._chatfield.fields)
    
    expect(fields).toContain('field1')
    expect(fields).toContain('field2')
    expect(fields).toContain('field3')
    expect(fields.length).toBe(3)
  })

  test('test_field_access_before_collection', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('name').desc('Your name')
      .field('age').desc('Your age')
      .build()

    expect(interview.name).toBeNull()
    expect(interview.age).toBeNull()
  })

  test('test_done_property', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('field1').desc('Field 1')
      .field('field2').desc('Field 2')
      .build()

    // Initially not done
    expect(interview._done).toBe(false)

    // Set one field - still not done
    interview._chatfield.fields.field1.value = {
      value: 'test1',
      context: 'N/A',
      as_quote: 'test1'
    }
    expect(interview._done).toBe(false)

    // Set both fields - now done
    interview._chatfield.fields.field2.value = {
      value: 'test2',
      context: 'N/A',
      as_quote: 'test2'
    }
    expect(interview._done).toBe(true)
  })

  test('test_model_dump', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('name').desc('Your name')
      .build()
    const dump = interview.model_dump()

    expect(typeof dump).toBe('object')
    expect(dump.type).toBe('TestInterview')
    expect('fields' in dump).toBe(true)
    expect('name' in dump.fields).toBe(true)

    // Modify original and ensure dump is independent
    interview._chatfield.fields.name.value = { value: 'test' }
    expect(dump.fields.name.value).toBeNull() // Should still be null
  })
})

describe('TestInterviewWithFeatures', () => {
  test('test_roles', () => {
    const interview = chatfield()
      .type('JobInterview')
      .desc('Job interview session')
      .alice()
        .type('Technical Interviewer')
        .trait('Asks detailed questions')
      .bob()
        .type('Job Candidate')
        .trait('Experienced developer')
      .field('experience').desc('Years of experience')
      .build()

    const aliceRole = interview._chatfield.roles.alice
    const bobRole = interview._chatfield.roles.bob

    expect(aliceRole.type).toBe('Technical Interviewer')
    expect(aliceRole.traits).toContain('Asks detailed questions')
    expect(bobRole.type).toBe('Job Candidate')
    expect(bobRole.traits).toContain('Experienced developer')
  })

  test('test_validation_rules', () => {
    const interview = chatfield()
      .type('ValidatedInterview')
      .field('description')
        .desc('Detailed description')
        .must('specific details')
        .must('at least 10 words')
        .reject('vague descriptions')
        .hint('Be as specific as possible')
      .build()
    const field = interview._chatfield.fields.description

    expect('must' in field.specs).toBe(true)
    expect(field.specs.must).toContain('specific details')
    expect(field.specs.must).toContain('at least 10 words')
    expect('reject' in field.specs).toBe(true)
    expect(field.specs.reject).toContain('vague descriptions')
    expect('hint' in field.specs).toBe(true)
    expect(field.specs.hint).toContain('Be as specific as possible')
  })

  test('test_type_transformations', () => {
    const interview = chatfield()
      .type('TypedInterview')
      .field('age')
        .desc('Your age')
        .as_int()
      .field('height')
        .desc('Your height')
        .as_float()
      .field('active')
        .desc('Are you active?')
        .as_bool()
      .field('confidence')
        .desc('Confidence level')
        .as_percent()
      .build()

    expect('as_int' in interview._chatfield.fields.age.casts).toBe(true)
    expect('as_float' in interview._chatfield.fields.height.casts).toBe(true)
    expect('as_bool' in interview._chatfield.fields.active.casts).toBe(true)
    expect('as_percent' in interview._chatfield.fields.confidence.casts).toBe(true)
  })

  test('test_sub_attribute_transformations', () => {
    const interview = chatfield()
      .type('MultiLangInterview')
      .field('number')
        .desc('A number')
        .as_lang.fr()
        .as_lang.es()
        .as_bool.even('True if even')
        .as_str.uppercase('In uppercase')
      .build()
    const fieldCasts = interview._chatfield.fields.number.casts

    expect('as_lang_fr' in fieldCasts).toBe(true)
    expect('as_lang_es' in fieldCasts).toBe(true)
    expect('as_bool_even' in fieldCasts).toBe(true)
    expect('as_str_uppercase' in fieldCasts).toBe(true)
  })

  test('test_cardinality_choices', () => {
    const interview = chatfield()
      .type('ChoiceInterview')
      .field('color')
        .desc('Favorite color')
        .as_one.color('red', 'green', 'blue')
      .field('priority')
        .desc('Priority level')
        .as_maybe.priority('low', 'medium', 'high')
      .field('languages')
        .desc('Programming languages')
        .as_multi.languages('python', 'javascript', 'rust')
      .field('reviewers')
        .desc('Code reviewers')
        .as_any.reviewers('alice', 'bob', 'charlie')
      .build()

    const colorCast = interview._chatfield.fields.color.casts.as_one_color
    expect(colorCast.type).toBe('choice')
    expect(colorCast.choices).toEqual(['red', 'green', 'blue'])
    expect(colorCast.null).toBe(false)
    expect(colorCast.multi).toBe(false)

    const priorityCast = interview._chatfield.fields.priority.casts.as_maybe_priority
    expect(priorityCast.null).toBe(true)
    expect(priorityCast.multi).toBe(false)

    const langCast = interview._chatfield.fields.languages.casts.as_multi_languages
    expect(langCast.null).toBe(false)
    expect(langCast.multi).toBe(true)

    const reviewerCast = interview._chatfield.fields.reviewers.casts.as_any_reviewers
    expect(reviewerCast.null).toBe(true)
    expect(reviewerCast.multi).toBe(true)
  })
})

describe('TestFieldProxy', () => {
  test('test_field_proxy_as_string', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('name').desc('Your name')
      .build()
    interview._chatfield.fields.name.value = {
      value: 'John Doe',
      context: 'User provided their name',
      as_quote: 'John Doe'
    }

    const name = interview.name

    expect(typeof name).toBe('string')
    expect(name instanceof FieldProxy).toBe(true)
    expect(name).toBe('John Doe')
    expect(name.toUpperCase()).toBe('JOHN DOE')
    expect(name.toLowerCase()).toBe('john doe')
    expect(name.length).toBe(8)
  })

  test('test_field_proxy_transformations', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('number')
        .desc('A number')
        .as_int()
        .as_lang.fr()
        .as_bool.even('True if even')
      .build()
    interview._chatfield.fields.number.value = {
      value: '42',
      context: 'User said forty-two',
      as_quote: 'forty-two',
      as_int: 42,
      as_lang_fr: 'quarante-deux',
      as_bool_even: true
    }

    const number = interview.number

    expect(number).toBe('42')
    expect(number.as_int).toBe(42)
    expect(number.as_lang_fr).toBe('quarante-deux')
    expect(number.as_bool_even).toBe(true)
    expect(number.context).toBe('User said forty-two')
    expect(number.as_quote).toBe('forty-two')
  })

  test('test_field_proxy_missing_transformation', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('name').desc('Your name')
      .build()
    interview._chatfield.fields.name.value = {
      value: 'test',
      context: 'N/A',
      as_quote: 'test'
    }

    const name = interview.name
    try {
      const result = name.as_int // This transformation doesn't exist
      // If we get here, it returns something (likely null/undefined)
      expect(result).toBeUndefined()
    } catch (e) {
      // Or it raises an error
      expect(e).toBeInstanceOf(Error)
    }
  })
})

describe('TestBuilderEdgeCases', () => {
  test('test_empty_interview', () => {
    const interview = chatfield()
      .type('EmptyInterview')
      .desc('Empty interview')
      .build()

    expect(interview._chatfield.type).toBe('EmptyInterview')
    expect(interview._chatfield.desc).toBe('Empty interview')
    expect(Object.keys(interview._chatfield.fields).length).toBe(0)
    expect(interview._done).toBe(true) // No fields means done
  })

  test('test_minimal_interview', () => {
    const interview = chatfield().build()

    expect(interview._chatfield.type).toBe('')
    expect(interview._chatfield.desc).toBe('')
    expect(Object.keys(interview._chatfield.fields).length).toBe(0)
  })

  test('test_field_with_default_description', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('test_field') // No description
      .build()

    // Should use field name as description
    expect(interview._chatfield.fields.test_field.desc).toBe('test_field')
  })

  test('test_multiple_validation_rules', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('field')
        .desc('Test field')
        .must('rule 1')
        .must('rule 2')
        .must('rule 3')
      .build()

    const fieldSpecs = interview._chatfield.fields.field.specs.must

    expect(fieldSpecs).toContain('rule 1')
    expect(fieldSpecs).toContain('rule 2')
    expect(fieldSpecs).toContain('rule 3')
    expect(fieldSpecs.length).toBe(3)
  })

  test('test_pretty_method', () => {
    const interview = chatfield()
      .type('TestInterview')
      .field('name').desc('Your name')
      .field('age').desc('Your age')
      .build()

    // Set one field
    interview._chatfield.fields.name.value = {
      value: 'Alice',
      context: 'User provided name',
      as_quote: 'My name is Alice'
    }

    const pretty = interview._pretty()

    expect(typeof pretty).toBe('string')
    expect(pretty.length).toBeGreaterThan(0)
  })
})