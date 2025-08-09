"""LangGraph agent implementation for Chatfield Socratic dialogue data gathering."""

from typing import Dict, List, Optional, Tuple, TypedDict, Annotated, Literal
from dataclasses import dataclass
from enum import Enum
import operator

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .socrates import SocratesMeta, FieldMeta


class ConversationState(TypedDict):
    """State for the Socratic dialogue graph."""
    meta: SocratesMeta
    messages: Annotated[List[BaseMessage], operator.add]
    collected_data: Dict[str, str]
    current_field: Optional[str]
    validation_attempts: int
    max_retries: int
    is_complete: bool
    needs_validation: bool
    validation_result: Optional[Tuple[bool, str]]


class FieldStatus(str, Enum):
    """Status of a field in the Socratic dialogue."""
    PENDING = "pending"
    ASKING = "asking"
    VALIDATING = "validating"
    COLLECTED = "collected"
    SKIPPED = "skipped"


class ValidationResult(BaseModel):
    """Result of field validation."""
    is_valid: bool
    feedback: str = ""
    
    
class ChatfieldAgent:
    """LangGraph-based Socratic dialogue agent for data gathering."""
    
    def __init__(
        self, 
        meta: SocratesMeta,
        llm: Optional[ChatOpenAI] = None,
        max_retries: int = 3,
        temperature: float = 0.7
    ):
        self.meta = meta
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature
        )
        self.max_retries = max_retries
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_conversation)
        workflow.add_node("select_field", self._select_next_field)
        workflow.add_node("ask_question", self._ask_field_question)
        workflow.add_node("process_response", self._process_user_response)
        workflow.add_node("validate_response", self._validate_response)
        workflow.add_node("handle_validation", self._handle_validation_result)
        workflow.add_node("complete", self._complete_conversation)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges
        workflow.add_edge("initialize", "select_field")
        
        # Conditional routing from select_field
        workflow.add_conditional_edges(
            "select_field",
            self._route_from_select,
            {
                "ask": "ask_question",
                "complete": "complete"
            }
        )
        
        workflow.add_edge("ask_question", "process_response")
        workflow.add_edge("process_response", "validate_response")
        workflow.add_edge("validate_response", "handle_validation")
        
        # Conditional routing from handle_validation
        workflow.add_conditional_edges(
            "handle_validation",
            self._route_from_validation,
            {
                "retry": "ask_question",
                "next": "select_field",
                "skip": "select_field"
            }
        )
        
        workflow.add_edge("complete", END)
        
        return workflow.compile()
    
    def _initialize_conversation(self, state: ConversationState) -> ConversationState:
        """Initialize the Socratic dialogue with opening message."""
        opening_message = self._build_opening_message()
        
        return {
            **state,
            "messages": [SystemMessage(content=opening_message)],
            "collected_data": {},
            "validation_attempts": 0,
            "is_complete": False,
            "needs_validation": False
        }
    
    def _select_next_field(self, state: ConversationState) -> ConversationState:
        """Select the next field to ask about."""
        uncollected = self._get_uncollected_fields(state)
        
        if not uncollected:
            return {
                **state,
                "current_field": None,
                "is_complete": True
            }
        
        next_field = uncollected[0]
        return {
            **state,
            "current_field": next_field,
            "validation_attempts": 0
        }
    
    def _ask_field_question(self, state: ConversationState) -> ConversationState:
        """Generate and ask a question about the current field."""
        if not state["current_field"]:
            return state
            
        field = self.meta.get_field(state["current_field"])
        if not field:
            return state
        
        # Build conversational prompt (includes hints)
        prompt = self._build_field_prompt(field, state["collected_data"])
        
        message = AIMessage(content=prompt)
        
        return {
            **state,
            "messages": state["messages"] + [message],
            "needs_validation": True
        }
    
    def _process_user_response(self, state: ConversationState) -> ConversationState:
        """Process the user's response to a field question."""
        # In a real implementation, this would handle actual user input
        # For now, we'll assume the response is in the last message
        last_message = state["messages"][-1] if state["messages"] else None
        
        if isinstance(last_message, HumanMessage):
            # User provided a response
            return state
        
        # Simulate getting user input (would be replaced with actual input handling)
        user_response = self._simulate_user_input(state)
        
        return {
            **state,
            "messages": state["messages"] + [HumanMessage(content=user_response)]
        }
    
    def _validate_response(self, state: ConversationState) -> ConversationState:
        """Validate the user's response against field rules."""
        if not state["current_field"]:
            return state
            
        field = self.meta.get_field(state["current_field"])
        if not field or not field.has_validation_rules():
            # No validation needed
            return {
                **state,
                "validation_result": (True, "")
            }
        
        # Get the last user message
        user_response = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_response = msg.content
                break
        
        if not user_response:
            return {
                **state,
                "validation_result": (False, "No response provided")
            }
        
        # Build validation prompt
        validation_prompt = self._build_validation_prompt(field, user_response)
        
        # Call LLM for validation
        validation_response = self.llm.invoke([
            SystemMessage(content=validation_prompt)
        ])
        
        # Parse validation result
        is_valid, feedback = self._parse_validation_result(validation_response.content)
        
        return {
            **state,
            "validation_result": (is_valid, feedback)
        }
    
    def _handle_validation_result(self, state: ConversationState) -> ConversationState:
        """Handle the result of validation."""
        if not state["validation_result"]:
            return state
            
        is_valid, feedback = state["validation_result"]
        
        if is_valid:
            # Collect the data
            user_response = None
            for msg in reversed(state["messages"]):
                if isinstance(msg, HumanMessage):
                    user_response = msg.content
                    break
            
            if user_response and state["current_field"]:
                return {
                    **state,
                    "collected_data": {
                        **state["collected_data"],
                        state["current_field"]: user_response
                    },
                    "validation_attempts": 0,
                    "needs_validation": False
                }
        else:
            # Validation failed
            new_attempts = state["validation_attempts"] + 1
            
            if new_attempts >= state.get("max_retries", self.max_retries):
                # Too many attempts, skip field
                skip_message = AIMessage(
                    content=f"Let's move on to the next question for now."
                )
                return {
                    **state,
                    "messages": state["messages"] + [skip_message],
                    "validation_attempts": 0,
                    "needs_validation": False
                }
            else:
                # Provide feedback and retry
                feedback_message = AIMessage(content=feedback)
                return {
                    **state,
                    "messages": state["messages"] + [feedback_message],
                    "validation_attempts": new_attempts
                }
        
        return state
    
    def _complete_conversation(self, state: ConversationState) -> ConversationState:
        """Complete the Socratic dialogue and return results."""
        completion_message = AIMessage(
            content="Great! I've collected all the information I need. Thank you!"
        )
        
        return {
            **state,
            "messages": state["messages"] + [completion_message],
            "is_complete": True
        }
    
    def _route_from_select(self, state: ConversationState) -> Literal["ask", "complete"]:
        """Route from field selection node."""
        if state["is_complete"] or not state["current_field"]:
            return "complete"
        return "ask"
    
    def _route_from_validation(self, state: ConversationState) -> Literal["retry", "next", "skip"]:
        """Route from validation handling node."""
        if not state["validation_result"]:
            return "next"
            
        is_valid, _ = state["validation_result"]
        
        if is_valid:
            return "next"
        elif state["validation_attempts"] >= state.get("max_retries", self.max_retries):
            return "skip"
        else:
            return "retry"
    
    def _build_opening_message(self) -> str:
        """Build the opening system message."""
        messages = []
        
        # Add class docstring
        if self.meta.docstring:
            messages.append(self.meta.docstring)
        
        # Add agent context
        if self.meta.agent_context:
            agent_context = "\n".join(self.meta.agent_context)
            messages.append(f"Agent behavior: {agent_context}")
        
        # Add user context
        if self.meta.user_context:
            user_context = "\n".join(self.meta.user_context)
            messages.append(f"User context: {user_context}")
        
        if not messages:
            messages.append("I'll help you gather some information through a conversation.")
        
        return "\n\n".join(messages)
    
    def _build_field_prompt(self, field: FieldMeta, collected_data: Dict[str, str]) -> str:
        """Build a conversational prompt for a field."""
        prompt = field.description
        
        # Make it conversational
        if not prompt.rstrip().endswith('?'):
            prompt += "?"
        
        # Add context from previously collected data
        if collected_data:
            recent_items = list(collected_data.items())[-2:]
            if recent_items:
                context = ", ".join([f"{k}: {v[:30]}..." if len(v) > 30 else f"{k}: {v}" 
                                    for k, v in recent_items])
                prompt = f"Based on what you've told me ({context}), {prompt.lower()}"
        
        # Add hints if available
        if field.hints:
            hints_text = "\n".join([f"💡 {hint}" for hint in field.hints])
            prompt = f"{prompt}\n{hints_text}"
        
        return prompt
    
    def _build_validation_prompt(self, field: FieldMeta, response: str) -> str:
        """Build a prompt for validating a response."""
        rules = []
        
        if field.must_rules:
            rules.extend([f"- MUST include: {rule}" for rule in field.must_rules])
        
        if field.reject_rules:
            rules.extend([f"- MUST NOT include: {rule}" for rule in field.reject_rules])
        
        rules_text = "\n".join(rules) if rules else "No specific validation rules."
        
        return f"""Validate this user response: "{response}"

For the field "{field.description}", check these rules:
{rules_text}

If valid, respond with exactly "VALID".
If not valid, provide helpful feedback to guide the user to a better answer.
Be encouraging and specific about what's needed."""
    
    def _parse_validation_result(self, response: str) -> Tuple[bool, str]:
        """Parse the LLM's validation response."""
        response = response.strip()
        
        if response.upper() == "VALID":
            return True, ""
        else:
            return False, response
    
    def _get_uncollected_fields(self, state: ConversationState) -> List[str]:
        """Get list of fields that haven't been collected yet."""
        all_fields = self.meta.get_field_names()
        collected = set(state["collected_data"].keys())
        return [f for f in all_fields if f not in collected]
    
    def _simulate_user_input(self, state: ConversationState) -> str:
        """Simulate user input for testing (would be replaced with actual input)."""
        # This is a placeholder for testing
        # In production, this would interface with actual user input
        return "Test response"
    
    def run(self, initial_data: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Run the Socratic dialogue and collect data."""
        initial_state: ConversationState = {
            "meta": self.meta,
            "messages": [],
            "collected_data": initial_data or {},
            "current_field": None,
            "validation_attempts": 0,
            "max_retries": self.max_retries,
            "is_complete": False,
            "needs_validation": False,
            "validation_result": None
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state["collected_data"]