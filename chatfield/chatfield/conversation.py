"""LangGraph-based conversation management for Chatfield."""

from typing import Dict, List, Optional, Any
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from .socrates import SocratesMeta, SocratesInstance
from .agent import ChatfieldAgent, ConversationState


class Conversation:
    """Manages Socratic dialogue conversations using LangGraph agents."""
    
    def __init__(
        self, 
        meta: SocratesMeta,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        self.meta = meta
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model=model,
            temperature=temperature
        )
        
        # Create the agent
        self.agent = ChatfieldAgent(
            meta=meta,
            llm=self.llm,
            max_retries=max_retries
        )
        
        self.collected_data: Dict[str, str] = {}
        self.conversation_history: List[Any] = []
    
    def conduct_conversation(self) -> Dict[str, str]:
        """Run the Socratic dialogue to collect all data.
        
        This method uses the LangGraph agent to manage the Socratic conversation flow.
        """
        print(f"\n{self._get_opening_message()}\n")
        
        # Create initial state
        initial_state: ConversationState = {
            "meta": self.meta,
            "messages": [],
            "collected_data": {},
            "current_field": None,
            "validation_attempts": 0,
            "max_retries": self.agent.max_retries,
            "is_complete": False,
            "needs_validation": False,
            "validation_result": None
        }
        
        # Run the conversation graph interactively
        current_state = initial_state
        
        while not current_state["is_complete"]:
            # Run one step of the graph
            for event in self.agent.graph.stream(current_state):
                # Process each node's output
                for node_name, node_state in event.items():
                    current_state = node_state
                    
                    # If we just asked a question, get user input
                    if node_name == "ask_question" and current_state["messages"]:
                        last_message = current_state["messages"][-1]
                        if hasattr(last_message, 'content'):
                            print(f"\n{last_message.content}")
                            
                            # Get actual user input
                            user_response = input("Your answer: ").strip()
                            
                            if user_response:
                                # Add user response to state
                                current_state["messages"].append(
                                    HumanMessage(content=user_response)
                                )
                    
                    # If we have validation feedback, show it
                    elif node_name == "handle_validation" and current_state.get("validation_result"):
                        is_valid, feedback = current_state["validation_result"]
                        if not is_valid and feedback:
                            print(f"\n{feedback}")
                            print("Let me ask again...")
                    
                    # Check if we're complete
                    if current_state.get("is_complete", False):
                        break
            
            # Update collected data
            self.collected_data = current_state.get("collected_data", {})
            
            # Check completion
            if current_state.get("is_complete", False):
                break
        
        # Show completion message
        if len(self.collected_data) == len(self.meta.fields):
            print("\nGreat! I've collected all the information I need.")
        
        return self.collected_data
    
    def conduct_async_conversation(self, user_input_callback) -> Dict[str, str]:
        """Run the conversation with async user input.
        
        Args:
            user_input_callback: Async function that gets user input
        
        Returns:
            Dictionary of collected field data
        """
        # This would be implemented for async/streaming use cases
        raise NotImplementedError("Async conversation not yet implemented")
    
    def _get_opening_message(self) -> str:
        """Generate the opening message for the conversation."""
        messages = []
        
        if self.meta.docstring:
            messages.append(self.meta.docstring)
        
        if self.meta.agent_context:
            # Agent context is used internally but not shown to user
            pass
        
        if not messages:
            messages.append("Let me ask you a few questions to gather the information I need.")
        
        return "\n".join(messages)
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the Socratic dialogue so far."""
        if not self.collected_data:
            return "No data collected yet."
        
        summary_items = []
        for field_name, value in self.collected_data.items():
            field = self.meta.get_field(field_name)
            field_desc = field.description if field else field_name
            short_value = value[:50] + "..." if len(value) > 50 else value
            summary_items.append(f"- {field_desc}: {short_value}")
        
        return f"Collected so far:\n" + "\n".join(summary_items)
    
    def create_instance(self) -> SocratesInstance:
        """Create a SocratesInstance from collected data."""
        return SocratesInstance(self.meta, self.collected_data)