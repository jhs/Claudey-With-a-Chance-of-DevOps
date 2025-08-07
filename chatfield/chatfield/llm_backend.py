"""LLM backend integrations for Chatfield."""

import os
import sys
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import json
import traceback
from pathlib import Path

# Load environment variables from .env file in project root
try:
    from dotenv import load_dotenv
    # Find the project root (parent of chatfield directory)
    current_file = Path(__file__).resolve()
    chatfield_dir = current_file.parent.parent  # chatfield/chatfield -> chatfield
    project_root = chatfield_dir.parent  # chatfield -> project root
    env_file = project_root / '.env'
    
    if env_file.exists():
        print(f"[LLM Backend] Loading environment from: {env_file}", file=sys.stderr)
        load_dotenv(env_file, override=True)
        print(f"[LLM Backend] Environment loaded successfully", file=sys.stderr)
    else:
        print(f"[LLM Backend] No .env file found at: {env_file}", file=sys.stderr)
except ImportError:
    print(f"[LLM Backend] python-dotenv not installed, skipping .env loading", file=sys.stderr)
except Exception as e:
    print(f"[LLM Backend] Error loading .env: {e}", file=sys.stderr)

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from .gatherer import GathererMeta, FieldMeta


class LLMBackend(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def create_conversation_prompt(
        self, 
        meta: GathererMeta, 
        field: FieldMeta, 
        history: List[Dict[str, str]]
    ) -> str:
        """Build the system and user prompts for conversation."""
        pass
    
    @abstractmethod
    def get_response(self, prompt: str) -> str:
        """Get LLM response to a prompt."""
        pass
    
    @abstractmethod
    def validate_response(self, validation_prompt: str) -> str:
        """Validate a user response using the LLM."""
        pass


class OpenAIBackend(LLMBackend):
    """OpenAI GPT implementation."""
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        print(f"[LLM Backend] Initializing OpenAI backend with model: {model}", file=sys.stderr)
        
        if not OPENAI_AVAILABLE:
            error_msg = "OpenAI package not available. Install with: pip install openai"
            print(f"[LLM Backend ERROR] {error_msg}", file=sys.stderr)
            raise ImportError(error_msg)
        
        self.model = model
        api_key_source = "parameter" if api_key else "environment"
        api_key_to_use = api_key or os.getenv("OPENAI_API_KEY")
        
        if api_key_to_use:
            # Log masked API key for debugging
            masked_key = api_key_to_use[:7] + "..." + api_key_to_use[-4:] if len(api_key_to_use) > 11 else "***"
            print(f"[LLM Backend] Using API key from {api_key_source}: {masked_key}", file=sys.stderr)
        else:
            print(f"[LLM Backend WARNING] No API key found in {api_key_source}", file=sys.stderr)
        
        self.client = OpenAI(api_key=api_key_to_use)
        
        if not self.client.api_key:
            error_msg = (
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
            print(f"[LLM Backend ERROR] {error_msg}", file=sys.stderr)
            raise ValueError(error_msg)
        
        print(f"[LLM Backend] Successfully initialized OpenAI client", file=sys.stderr)
    
    def create_conversation_prompt(
        self, 
        meta: GathererMeta, 
        field: FieldMeta, 
        history: List[Dict[str, str]]
    ) -> str:
        """Build the conversation prompt with full context."""
        print(f"[LLM Backend] Creating conversation prompt for field: {field.name}", file=sys.stderr)
        
        # Build system context
        context_parts = []
        
        # Add main context from docstring
        if meta.docstring:
            print(f"[LLM Backend] Adding docstring context: {meta.docstring[:100]}...", file=sys.stderr)
            context_parts.append(f"Context: {meta.docstring}")
        else:
            print(f"[LLM Backend] No docstring context available", file=sys.stderr)
        
        # Add user context
        if meta.user_context:
            user_info = " ".join(meta.user_context)
            print(f"[LLM Backend] Adding user context: {user_info[:100]}...", file=sys.stderr)
            context_parts.append(f"User: {user_info}")
        else:
            print(f"[LLM Backend] No user context provided", file=sys.stderr)
        
        # Add agent behavior
        if meta.agent_context:
            agent_info = " ".join(meta.agent_context)
            print(f"[LLM Backend] Adding agent behavior: {agent_info[:100]}...", file=sys.stderr)
            context_parts.append(f"Behavior: {agent_info}")
        else:
            print(f"[LLM Backend] No agent behavior specified", file=sys.stderr)
        
        # Add field-specific information
        print(f"[LLM Backend] Processing field '{field.name}' with description: {field.description}", file=sys.stderr)
        field_info = [f"Current question: {field.description}"]
        
        if field.hints:
            print(f"[LLM Backend] Adding {len(field.hints)} hints for field '{field.name}'", file=sys.stderr)
            for hint in field.hints:
                print(f"[LLM Backend]   - Hint: {hint}", file=sys.stderr)
                field_info.append(f"Helpful context: {hint}")
        
        if field.must_rules:
            print(f"[LLM Backend] Adding {len(field.must_rules)} MUST rules for field '{field.name}'", file=sys.stderr)
            for rule in field.must_rules:
                print(f"[LLM Backend]   - Must include: {rule}", file=sys.stderr)
            field_info.append(f"Answer must include: {', '.join(field.must_rules)}")
        
        if field.reject_rules:
            print(f"[LLM Backend] Adding {len(field.reject_rules)} REJECT rules for field '{field.name}'", file=sys.stderr)
            for rule in field.reject_rules:
                print(f"[LLM Backend]   - Should avoid: {rule}", file=sys.stderr)
            field_info.append(f"Answer should avoid: {', '.join(field.reject_rules)}")
        
        context_parts.extend(field_info)
        
        # Add conversation history
        if history:
            print(f"[LLM Backend] Adding conversation history ({len(history)} messages, showing last 3)", file=sys.stderr)
            history_text = "Previous conversation:\\n"
            for msg in history[-3:]:  # Last 3 exchanges
                truncated = msg['content'][:100]
                print(f"[LLM Backend]   - {msg['role']}: {truncated}...", file=sys.stderr)
                history_text += f"- {msg['role']}: {truncated}...\\n"
            context_parts.append(history_text)
        else:
            print(f"[LLM Backend] No conversation history yet", file=sys.stderr)
        
        final_prompt = "\\n\\n".join(context_parts)
        print(f"[LLM Backend] Final prompt length: {len(final_prompt)} characters", file=sys.stderr)
        print(f"[LLM Backend] Prompt preview: {final_prompt[:200]}...", file=sys.stderr)
        
        return final_prompt
    
    def get_response(self, prompt: str) -> str:
        """Get response from OpenAI."""
        print(f"[LLM Backend] Getting response from OpenAI model: {self.model}", file=sys.stderr)
        print(f"[LLM Backend] Request prompt length: {len(prompt)} characters", file=sys.stderr)
        
        system_message = "You are a helpful assistant conducting a conversational data gathering session. Ask clear questions and guide users to provide useful information."
        print(f"[LLM Backend] System message: {system_message[:100]}...", file=sys.stderr)
        
        try:
            start_time = time.time()
            print(f"[LLM Backend] Sending request to OpenAI API...", file=sys.stderr)
            
            messages = [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            print(f"[LLM Backend] Request parameters:", file=sys.stderr)
            print(f"[LLM Backend]   - Model: {self.model}", file=sys.stderr)
            print(f"[LLM Backend]   - Max tokens: 500", file=sys.stderr)
            print(f"[LLM Backend]   - Temperature: 0.7", file=sys.stderr)
            print(f"[LLM Backend]   - Messages: {len(messages)}", file=sys.stderr)
            
            # Log complete request payload
            print(f"[LLM Backend] ===== OPENAI API REQUEST =====", file=sys.stderr)
            print(f"[LLM Backend] Model: {self.model}", file=sys.stderr)
            for i, msg in enumerate(messages):
                print(f"[LLM Backend] Message {i+1} ({msg['role']}):", file=sys.stderr)
                print(f"[LLM Backend]   {msg['content']}", file=sys.stderr)
            print(f"[LLM Backend] ===== END REQUEST =====", file=sys.stderr)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            
            elapsed_time = time.time() - start_time
            print(f"[LLM Backend] Received response in {elapsed_time:.2f} seconds", file=sys.stderr)
            
            # Log response details
            print(f"[LLM Backend] Response details:", file=sys.stderr)
            print(f"[LLM Backend]   - Model used: {response.model}", file=sys.stderr)
            print(f"[LLM Backend]   - Choices: {len(response.choices)}", file=sys.stderr)
            print(f"[LLM Backend]   - Finish reason: {response.choices[0].finish_reason}", file=sys.stderr)
            
            if hasattr(response, 'usage'):
                print(f"[LLM Backend]   - Prompt tokens: {response.usage.prompt_tokens}", file=sys.stderr)
                print(f"[LLM Backend]   - Completion tokens: {response.usage.completion_tokens}", file=sys.stderr)
                print(f"[LLM Backend]   - Total tokens: {response.usage.total_tokens}", file=sys.stderr)
            
            content = response.choices[0].message.content.strip()
            print(f"[LLM Backend] Response content length: {len(content)} characters", file=sys.stderr)
            print(f"[LLM Backend] Response preview: {content[:200]}...", file=sys.stderr)
            
            # Log complete response
            print(f"[LLM Backend] ===== OPENAI API RESPONSE =====", file=sys.stderr)
            print(f"[LLM Backend] Full response content:", file=sys.stderr)
            print(f"[LLM Backend]   {content}", file=sys.stderr)
            print(f"[LLM Backend] ===== END RESPONSE =====", file=sys.stderr)
            
            return content
            
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            print(f"[LLM Backend ERROR] {error_msg}", file=sys.stderr)
            print(f"[LLM Backend ERROR] Exception type: {type(e).__name__}", file=sys.stderr)
            print(f"[LLM Backend ERROR] Traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            raise Exception(error_msg)
    
    def validate_response(self, validation_prompt: str) -> str:
        """Validate a response using OpenAI."""
        print(f"[LLM Backend] Starting validation with OpenAI model: {self.model}", file=sys.stderr)
        print(f"[LLM Backend] Validation prompt length: {len(validation_prompt)} characters", file=sys.stderr)
        print(f"[LLM Backend] Validation prompt preview: {validation_prompt[:200]}...", file=sys.stderr)
        
        system_message = (
            "You are a validator. Check if user responses meet specified requirements. "
            "If valid, respond 'VALID'. If not valid, explain what's missing in a helpful way."
        )
        print(f"[LLM Backend] Validation system message: {system_message}", file=sys.stderr)
        
        try:
            start_time = time.time()
            print(f"[LLM Backend] Sending validation request to OpenAI API...", file=sys.stderr)
            
            messages = [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": validation_prompt
                }
            ]
            
            print(f"[LLM Backend] Validation parameters:", file=sys.stderr)
            print(f"[LLM Backend]   - Model: {self.model}", file=sys.stderr)
            print(f"[LLM Backend]   - Max tokens: 200", file=sys.stderr)
            print(f"[LLM Backend]   - Temperature: 0.1 (low for consistency)", file=sys.stderr)
            
            # Log complete validation request
            print(f"[LLM Backend] ===== OPENAI VALIDATION REQUEST =====", file=sys.stderr)
            print(f"[LLM Backend] Model: {self.model}", file=sys.stderr)
            for i, msg in enumerate(messages):
                print(f"[LLM Backend] Message {i+1} ({msg['role']}):", file=sys.stderr)
                print(f"[LLM Backend]   {msg['content']}", file=sys.stderr)
            print(f"[LLM Backend] ===== END VALIDATION REQUEST =====", file=sys.stderr)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent validation
            )
            
            elapsed_time = time.time() - start_time
            print(f"[LLM Backend] Validation response received in {elapsed_time:.2f} seconds", file=sys.stderr)
            
            # Log validation response details
            print(f"[LLM Backend] Validation response details:", file=sys.stderr)
            print(f"[LLM Backend]   - Finish reason: {response.choices[0].finish_reason}", file=sys.stderr)
            
            if hasattr(response, 'usage'):
                print(f"[LLM Backend]   - Prompt tokens: {response.usage.prompt_tokens}", file=sys.stderr)
                print(f"[LLM Backend]   - Completion tokens: {response.usage.completion_tokens}", file=sys.stderr)
                print(f"[LLM Backend]   - Total tokens: {response.usage.total_tokens}", file=sys.stderr)
            
            result = response.choices[0].message.content.strip()
            is_valid = result.startswith("VALID")
            
            print(f"[LLM Backend] Validation result: {'VALID' if is_valid else 'INVALID'}", file=sys.stderr)
            print(f"[LLM Backend] Validation response: {result[:200]}...", file=sys.stderr)
            
            # Log complete validation response
            print(f"[LLM Backend] ===== OPENAI VALIDATION RESPONSE =====", file=sys.stderr)
            print(f"[LLM Backend] Full validation response:", file=sys.stderr)
            print(f"[LLM Backend]   {result}", file=sys.stderr)
            print(f"[LLM Backend] ===== END VALIDATION RESPONSE =====", file=sys.stderr)
            
            return result
            
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            print(f"[LLM Backend ERROR] {error_msg}", file=sys.stderr)
            print(f"[LLM Backend ERROR] Exception type: {type(e).__name__}", file=sys.stderr)
            print(f"[LLM Backend ERROR] Traceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            raise Exception(error_msg)


class MockLLMBackend(LLMBackend):
    """Mock LLM backend for testing."""
    
    def __init__(self):
        print(f"[LLM Backend MOCK] Initializing MockLLMBackend", file=sys.stderr)
        self.responses = []
        self.validation_responses = []
        self.call_count = 0
        self.validation_call_count = 0
        print(f"[LLM Backend MOCK] Mock backend ready", file=sys.stderr)
    
    def add_response(self, response: str) -> None:
        """Add a mock response."""
        print(f"[LLM Backend MOCK] Adding mock response #{len(self.responses) + 1}: {response[:100]}...", file=sys.stderr)
        self.responses.append(response)
    
    def add_validation_response(self, response: str) -> None:
        """Add a mock validation response."""
        print(f"[LLM Backend MOCK] Adding mock validation response #{len(self.validation_responses) + 1}: {response[:100]}...", file=sys.stderr)
        self.validation_responses.append(response)
    
    def create_conversation_prompt(
        self, 
        meta: GathererMeta, 
        field: FieldMeta, 
        history: List[Dict[str, str]]
    ) -> str:
        """Build conversation prompt (mock version)."""
        print(f"[LLM Backend MOCK] Creating mock conversation prompt for field: {field.name}", file=sys.stderr)
        
        parts = []
        
        if meta.docstring:
            print(f"[LLM Backend MOCK] Adding docstring: {meta.docstring[:50]}...", file=sys.stderr)
            parts.append(f"Context: {meta.docstring}")
        
        print(f"[LLM Backend MOCK] Adding field description: {field.description}", file=sys.stderr)
        parts.append(f"Field: {field.description}")
        
        if field.hints:
            print(f"[LLM Backend MOCK] Adding {len(field.hints)} hints", file=sys.stderr)
            for hint in field.hints:
                parts.append(f"Hint: {hint}")
        
        if history:
            print(f"[LLM Backend MOCK] History contains {len(history)} messages", file=sys.stderr)
        
        prompt = "\\n".join(parts)
        print(f"[LLM Backend MOCK] Final mock prompt length: {len(prompt)} characters", file=sys.stderr)
        
        return prompt
    
    def get_response(self, prompt: str) -> str:
        """Return a mock response."""
        print(f"[LLM Backend MOCK] Getting mock response (call #{self.call_count + 1})", file=sys.stderr)
        print(f"[LLM Backend MOCK] Prompt length: {len(prompt)} characters", file=sys.stderr)
        
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            print(f"[LLM Backend MOCK] Returning predefined response #{self.call_count + 1}: {response[:100]}...", file=sys.stderr)
            self.call_count += 1
            return response
        
        default_response = "Mock response"
        print(f"[LLM Backend MOCK] No more predefined responses, returning default: {default_response}", file=sys.stderr)
        self.call_count += 1
        return default_response
    
    def validate_response(self, validation_prompt: str) -> str:
        """Return a mock validation response."""
        print(f"[LLM Backend MOCK] Getting mock validation response (call #{self.validation_call_count + 1})", file=sys.stderr)
        print(f"[LLM Backend MOCK] Validation prompt length: {len(validation_prompt)} characters", file=sys.stderr)
        
        if self.validation_call_count < len(self.validation_responses):
            response = self.validation_responses[self.validation_call_count]
            is_valid = response.startswith("VALID")
            print(f"[LLM Backend MOCK] Returning predefined validation #{self.validation_call_count + 1}: {'VALID' if is_valid else 'INVALID'}", file=sys.stderr)
            print(f"[LLM Backend MOCK] Validation response: {response[:100]}...", file=sys.stderr)
            self.validation_call_count += 1
            return response
        
        default_response = "VALID"
        print(f"[LLM Backend MOCK] No more predefined validations, returning default: {default_response}", file=sys.stderr)
        self.validation_call_count += 1
        return default_response