#!/usr/bin/env python3
"""Demonstration of FieldValueProxy's string capabilities after subclassing str.

This example shows how field proxies now behave as full strings while still
providing access to transformations and match rules.
"""

from chatfield.field_proxy import FieldValueProxy
from chatfield.socrates import FieldMeta
import json


def demonstrate_string_capabilities():
    """Show off the new string capabilities of FieldValueProxy."""
    
    print("=" * 60)
    print("FIELDVALUEPROXY STRING CAPABILITIES")
    print("=" * 60)
    
    # Create a proxy with some data
    field_meta = FieldMeta(name="company_name", description="Company name")
    field_meta.transformations = {"as_list": {"description": "Split into words"}}
    field_meta.match_rules = {"is_tech_company": {"criteria": "technology company"}}
    
    proxy = FieldValueProxy(
        "OpenAI Technologies Inc",
        field_meta,
        evaluations={"is_tech_company": True},
        transformations={"as_list": ["OpenAI", "Technologies", "Inc"]}
    )
    
    print("\n1. PROXY IS A REAL STRING:")
    print("-" * 40)
    print(f"  isinstance(proxy, str): {isinstance(proxy, str)}")
    print(f"  proxy value: '{proxy}'")
    print()
    
    print("2. ALL STRING METHODS WORK:")
    print("-" * 40)
    print(f"  .upper():        '{proxy.upper()}'")
    print(f"  .lower():        '{proxy.lower()}'")
    print(f"  .replace():      '{proxy.replace('Technologies', 'Tech')}'")
    print(f"  .startswith():   {proxy.startswith('Open')}")
    print(f"  .split():        {proxy.split()}")
    print(f"  [0:6]:           '{proxy[0:6]}'")
    print()
    
    print("3. STRING OPERATIONS:")
    print("-" * 40)
    print(f"  Concatenation:   '{proxy + ' (NASDAQ: OPEN)'}'")
    print(f"  Format string:   '{f'Company: {proxy}'}'")
    print(f"  Multiplication:  '{proxy[:4] * 3}'")
    print()
    
    print("4. CUSTOM FEATURES STILL WORK:")
    print("-" * 40)
    print(f"  .as_list:          {proxy.as_list}")
    print(f"  .is_tech_company:  {proxy.is_tech_company}")
    print()
    
    print("5. USE AS DICT KEY:")
    print("-" * 40)
    companies = {proxy: "AI Research"}
    print(f"  Dict with proxy key: {companies}")
    print(f"  Access with string:  {companies['OpenAI Technologies Inc']}")
    print()
    
    print("6. JSON SERIALIZATION:")
    print("-" * 40)
    data = {
        "name": proxy,
        "type": "technology",
        "details": {"full_name": proxy, "words": proxy.as_list}
    }
    json_str = json.dumps(data, indent=2)
    print(f"  JSON output:\n{json_str}")
    print()
    
    print("7. PRACTICAL EXAMPLE - DATA VALIDATION:")
    print("-" * 40)
    
    # Create an email field
    email_meta = FieldMeta(name="email", description="Email address")
    email_meta.match_rules = {"is_corporate": {"criteria": "corporate email"}}
    
    email_proxy = FieldValueProxy(
        "john.doe@openai.com",
        email_meta,
        evaluations={"is_corporate": True}
    )
    
    # Now we can use string methods for validation
    print(f"  Email: {email_proxy}")
    print(f"  Domain: {email_proxy.split('@')[1] if '@' in email_proxy else 'Invalid'}")
    print(f"  Is corporate: {email_proxy.is_corporate}")
    print(f"  Valid format: {'@' in email_proxy and '.' in email_proxy}")
    print(f"  Username: {email_proxy[:email_proxy.index('@')] if '@' in email_proxy else 'N/A'}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("FieldValueProxy now subclasses str, providing:")
    print("✓ Full compatibility with any code expecting strings")
    print("✓ All string methods work out of the box")
    print("✓ Can be used as dict keys and in sets")
    print("✓ JSON serialization works seamlessly")
    print("✓ String operations (concat, format, slice) all work")
    print("✓ Custom .as_* and match attributes still accessible")
    print("\nThis makes the API more intuitive and Pythonic!")


if __name__ == "__main__":
    demonstrate_string_capabilities()