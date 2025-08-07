"""Conversation management for Chatfield."""

from typing import Dict, List, Optional, Tuple
from .gatherer import GathererMeta, FieldMeta
from .llm_backend import LLMBackend, OpenAIBackend


class ConversationMessage:
    """A single message in the conversation."""
    
    def __init__(self, role: str, content: str):
        self.role = role  # 'user', 'assistant', 'system'
        self.content = content
    
    def __repr__(self) -> str:
        return f"{self.role}: {self.content[:50]}..."


class Conversation:
    """Manages the conversation state and flow."""
    
    def __init__(self, meta: GathererMeta, llm_backend: Optional[LLMBackend] = None):
        self.meta = meta
        self.collected_data: Dict[str, str] = {}
        self.conversation_history: List[ConversationMessage] = []
        self.llm = llm_backend or OpenAIBackend()
        self.max_retry_attempts = 3
    
    def get_next_field(self) -> Optional[FieldMeta]:
        """Determine which field to ask about next."""
        for field_name in self.meta.get_field_names():
            if field_name not in self.collected_data:
                return self.meta.get_field(field_name)
        return None
    
    def get_uncollected_fields(self) -> List[str]:
        """Get list of fields that haven't been collected yet."""
        return [name for name in self.meta.get_field_names() 
                if name not in self.collected_data]
    
    def validate_response(self, field: FieldMeta, response: str) -> Tuple[bool, str]:
        """Check if response meets field requirements.
        
        Returns:
            Tuple of (is_valid, feedback_message)
        """
        if not field.has_validation_rules():
            return True, ""
        
        validation_prompt = self._build_validation_prompt(field, response)
        
        try:
            validation_result = self.llm.validate_response(validation_prompt)
            
            # Parse the LLM's validation response
            if validation_result.strip().upper().startswith('VALID'):
                return True, ""
            else:
                return False, validation_result
                
        except Exception as e:
            # If validation fails, be permissive and allow the response
            print(f"Validation error: {e}")
            return True, ""
    
    def _build_validation_prompt(self, field: FieldMeta, response: str) -> str:
        """Build a prompt for the LLM to validate a response."""
        rules = []
        
        if field.must_rules:
            rules.extend([f"- MUST include: {rule}" for rule in field.must_rules])
        
        if field.reject_rules:
            rules.extend([f"- MUST NOT include: {rule}" for rule in field.reject_rules])
        
        rules_text = "\\n".join(rules) if rules else "No specific validation rules."
        
        return f"""The user provided this answer: "{response}"

For the field "{field.description}", validate that the answer follows these rules:
{rules_text}

If the answer is valid, respond with "VALID".
If the answer is not valid, explain what's missing or wrong in a helpful way that will guide the user to provide a better answer."""
    
    def conduct_conversation(self) -> Dict[str, str]:
        """Conduct the full conversation to collect all data.
        
        Returns:
            Dictionary of collected field data
        """
        print(f"\\n{self._get_opening_message()}\\n")
        
        while True:
            next_field = self.get_next_field()
            if not next_field:
                break
            
            # Ask about the field
            success = self._ask_about_field(next_field)
            if not success:
                print("Conversation ended due to too many retry attempts.")
                break
        
        if len(self.collected_data) == len(self.meta.fields):
            print("\\nGreat! I've collected all the information I need.")
        
        return self.collected_data
    
    def _get_opening_message(self) -> str:
        """Generate the opening message for the conversation."""
        messages = []
        
        if self.meta.docstring:
            messages.append(self.meta.docstring)
        
        if self.meta.agent_context:
            # Don't show agent context to user, but use it internally
            pass
        
        if not messages:
            messages.append("Let me ask you a few questions to gather the information I need.")
        
        return "\\n".join(messages)
    
    def _ask_about_field(self, field: FieldMeta) -> bool:
        """Ask about a specific field and collect the response.
        
        Returns:
            True if successfully collected, False if too many retries
        """
        attempts = 0
        
        while attempts < self.max_retry_attempts:
            # Build the prompt for this field
            prompt = self._build_field_prompt(field)
            
            try:
                # Get user input (in a real implementation, this would be through the LLM)
                print(f"\\n{prompt}")
                if field.hints:
                    for hint in field.hints:
                        print(f"💡 {hint}")
                
                # For now, we'll simulate user input
                # In real implementation, this would be handled by the LLM conversation
                response = input("Your answer: ").strip()
                
                if not response:
                    print("Please provide an answer.")
                    attempts += 1
                    continue
                
                # Validate the response
                is_valid, feedback = self.validate_response(field, response)
                
                if is_valid:
                    self.collected_data[field.name] = response
                    self.conversation_history.append(
                        ConversationMessage("user", response)
                    )
                    return True
                else:
                    print(f"\\n{feedback}\\nLet me try asking again...")
                    attempts += 1
                    
            except Exception as e:
                print(f"Error during conversation: {e}")
                attempts += 1
        
        print(f"Too many attempts for field '{field.name}'. Skipping...")
        return False
    
    def _build_field_prompt(self, field: FieldMeta) -> str:
        """Build a conversational prompt for asking about a field."""
        # Start with the field description as a question
        prompt = field.description
        
        # Make it conversational if it doesn't end with a question mark
        if not prompt.rstrip().endswith('?'):
            prompt += "?"
        
        # Add context about what we've already collected
        if self.collected_data:
            context_items = []
            for collected_field, value in list(self.collected_data.items())[-2:]:  # Last 2 items
                short_value = value[:30] + "..." if len(value) > 30 else value
                context_items.append(f"{collected_field}: {short_value}")
            
            if context_items:
                prompt = f"Based on what you've told me ({', '.join(context_items)}), {prompt.lower()}"
        
        return prompt
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation so far."""
        if not self.collected_data:
            return "No data collected yet."
        
        summary_items = []
        for field_name, value in self.collected_data.items():
            field_desc = self.meta.get_field(field_name).description if self.meta.get_field(field_name) else field_name
            short_value = value[:50] + "..." if len(value) > 50 else value
            summary_items.append(f"- {field_desc}: {short_value}")
        
        return f"Collected so far:\\n" + "\\n".join(summary_items)