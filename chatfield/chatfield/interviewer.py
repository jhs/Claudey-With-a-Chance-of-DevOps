"""LangGraph-based evaluator for Chatfield conversations."""

from concurrent.futures import thread
import json
from logging import config
import uuid

from pydantic import BaseModel, Field

from typing import Annotated, Any, Dict, Optional, TypedDict, List
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt, Interrupt
from langgraph.prebuilt import ToolNode, tools_condition, InjectedState
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

# from mcp import Tool


from .base import Interview


class State(TypedDict):
    messages: List[Any]
    interview: Interview


class Interviewer:
    """
    Interviewer that manages conversation flow.
    """
    
    def __init__(self, interview: Interview, thread_id: Optional[str] = None):
        self.checkpointer = InMemorySaver()

        self.config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}
        self.interview = interview

        # tool_id = 'openai:gpt-5'
        tool_id = 'openai:gpt-4.1'
        self.llm = init_chat_model(tool_id)

        # Define the tools used in the graph.
        tool_name = f'update_{self.interview.__class__.__name__}'
        tool_desc = f'Collect some information about the {self.interview.__class__.__name__}'

        # Use a Pydantic model to define the tool arguments.
        class ToolArgs(BaseModel):
            state: Annotated[dict, InjectedState]
            tool_call_id: Annotated[str, InjectedToolCallId]

            value: str = Field(description='The value to update the interview with.')
            as_int: int = Field(description='Cast the value as an integer.')
            as_float: float = Field(description='Cast the value as a float.')
            as_percent: float = Field(description='Cast the value as a percentage from 0.0-1.0.')
            as_longhand: str = Field(description='Cast the value as a longhand string.')
            as_longhand_french: str = Field(description='Cast the value as a longhand string in French.')
            # as_quote: Optional[str] = Field(None, description='Cast the value as a quote.')

        # XXX
        # Maybe 1 tool for storing validated fields and a second tool for updates but it's not yet valid.

        @tool(tool_name, description=tool_desc, args_schema=ToolArgs)
        def tool_wrapper(state, tool_call_id, **kwargs):
            print(f'tool_wrapper for id {tool_call_id}: {kwargs!r}')
            print(f'---- Yay got this from the LLM:\n' + json.dumps(kwargs, indent=2))

            tool_msg = ToolMessage(f'Success', tool_call_id=tool_call_id)
            state_update = {
                "messages": state['messages'] + [tool_msg],
            }
            return Command(update=state_update)

        tools_avilable = [tool_wrapper]
        self.llm_with_tools = self.llm.bind_tools(tools_avilable)
        tool_node = ToolNode(tools=tools_avilable) # , name='update_interview')

        builder = StateGraph(State)

        builder.add_node('initialize', self.initialize)
        builder.add_node('think'     , self.think)
        builder.add_node('listen'    , self.listen)
        builder.add_node('tools'     , tool_node)

        builder.add_edge             (START       , 'initialize')
        builder.add_edge             ('initialize', 'think')
        builder.add_conditional_edges('think'     , self.route_think)
        builder.add_edge             ('listen'    , 'think')
        builder.add_edge             ('tools'     , 'think')

        self.graph = builder.compile(checkpointer=self.checkpointer)
        
    def initialize(self, state:State) -> State:
        print(f'Initialize: {state["interview"].__class__.__name__}')
        return state
        
    def think(self, state: State) -> State:
        print(f'Think: {state["interview"].__class__.__name__}')
        
        if state['messages']:
            # I think ultimately the tools will be defined and the llm bound at this time.
            print(f'Messages already exist; continue conversation.')
            llm = self.llm_with_tools
        else:
            print(f'Start conversation in thread: {self.config["configurable"]["thread_id"]}')
            llm = self.llm

            system_prompt = self.mk_system_prompt(state)
            # print(f'----\n{system_msg.content}\n----')

            system_msg = SystemMessage(content=system_prompt)
            state['messages'].append(system_msg)

        llm_response_message = llm.invoke(state['messages'])
        # print(f'New message: {llm_response_message!r}')
        state['messages'].append(llm_response_message)

        return state
    
    def update_interview(self, query:str) -> str:
        """
        Update the interview with a new query.
        """
        print(f'Update interview> {query!r}')
        return f'Interview updated with query: {query}'
    
    def mk_system_prompt(self, state: State) -> str:
        interview = state['interview']
        # interview = self.interview._fromdict(interview)  # Reconstruct the interview object from the state

        collection_name = interview.__class__.__name__

        roles = getattr(interview, '_roles', {})
        alice_role = roles.get('alice', {})
        bob_role = roles.get('bob', {})

        alice_role_type = alice_role.get('type', 'Agent')
        bob_role_type = bob_role.get('type', 'User')

        fields = []
        for field_name in interview._fields():
            field = object.__getattribute__(interview, field_name)

            chatfield = getattr(field, '_chatfield', {})
            desc = chatfield.get('desc')
            field_label = f'{field_name}'
            if desc:
                field_label += f': {desc}'

            specs = chatfield.get('specs', {})
            specs_prompts = []
            for spec_name, predicates in specs.items():
                for predicate in predicates:
                    specs_prompts.append(f'{spec_name.capitalize()}: {predicate}')
            
            casts = chatfield.get('cast', {})
            casts_prompts = []
            for cast_name, cast_info in casts.items():
                cast_prompt = cast_info.get('prompt')
                if cast_prompt:
                    casts_prompts.append(f'{cast_name.capitalize()}: {cast_prompt}')

            field_specs = '\n'.join(f'    - {spec}' for spec in specs_prompts) + '\n' if specs_prompts else ''
            field_casts = '\n'.join(f'    - {cast}' for cast in casts_prompts) + '\n' if casts_prompts else ''

            field_prompt = (
                f'- {field_label}\n'
                f'{field_specs}'
                f'{field_casts}'
            )
            fields.append(field_prompt)
        fields = '\n'.join(fields)

        alice_traits = ''
        bob_traits = ''

        alice_role = roles.get('alice', {})
        traits = alice_role.get('traits', [])
        if traits:
            alice_traits = f'# Traits and Characteristics about the {alice_role_type}\n\n'
            # Maintain source-code order, since decorators apply bottom-up.
            alice_traits += '\n'.join(f'- {trait}' for trait in reversed(traits))

        bob_role = roles.get('bob', {})
        traits = bob_role.get('traits', [])
        if traits:
            bob_traits = f'# Traits and Characteristics about the {bob_role_type}\n\n'
            # Maintain source-code order, since decorators apply bottom-up.
            bob_traits += '\n'.join(f'- {trait}' for trait in reversed(traits))

        with_traits = f''
        if alice_traits or bob_traits:
            with_traits = f" Participants' characteristics and traits will be described below."
            
        alice_and_bob = ''
        if alice_traits or bob_traits:
            alice_and_bob = f'\n\n'
            alice_and_bob += alice_traits
            if alice_traits and bob_traits:
                alice_and_bob += '\n\n'
            alice_and_bob += bob_traits

        tool_name = 'update_interview'
        use_tools = (
            f' When you identify valid information to collect,'
            f' Use the {tool_name} tool, followed by a response to the {bob_role_type}.'
        )
        use_tools = '' # TODO finish this

        res = (
            f'You are a conversational {alice_role_type} focused on gathering key information in conversation with the {bob_role_type},'
            f' into a collection called {collection_name}, detailed below.'
            f'{with_traits}'
            f' You begin the conversation in the most suitable way.'
            f'{use_tools}'
            f' Although the {bob_role_type} may take the conversation anywhere, your response must fit the conversation and your respective roles'
            f' while refocusing the discussion so that you can gather clear key {collection_name} information from the {bob_role_type}.'
            f'{alice_and_bob}'
            f'\n\n----\n\n'
            f'# Collection: {collection_name}\n'
            f'\n'
            f'{fields}\n'
        )
        return res
    
    def route_think(self, state: State, *args, **kwargs) -> str:
        print(f'Route think edge: {state["interview"].__class__.__name__}')

        # TODO get rid of this
        if args or kwargs:
            print(f'  - args={args!r} kwargs={kwargs!r}')

        result = tools_condition(dict(state))
        if result == 'tools':
            print(f'Route: to tools')
            return 'tools'
        return 'listen'
        
    def listen(self, state: State) -> State:
        print(f'Listen: {state["interview"].__class__.__name__}')

        feedback = {'messages': state['messages']}
        update = interrupt(feedback)

        print(f'Interrupt result: {update!r}')
        user_input = update["user_input"]
        user_msg = HumanMessage(content=user_input)
        state['messages'].append(user_msg)
        return state
        
    def go(self, user_input: Optional[str] = None):
        print(f'Go: User input: {user_input!r}')
        state = self.graph.get_state(config=self.config)

        if state.values and state.values['messages']:
            print(f'Continue conversation: {self.config["configurable"]["thread_id"]}')
            graph_input = Command(update={}, resume={'user_input': user_input})
        else:
            print(f'New conversation: {self.config["configurable"]["thread_id"]}')
            user_message = HumanMessage(content=user_input) if user_input else None
            user_messages = [user_message] if user_message else []
            graph_input = State(messages=user_messages, interview=self.interview)

        interrupts = []
        for event in self.graph.stream(graph_input, config=self.config):
            # print(f'ev> {event!r}')
            for value in event.values():
                # print("Assistant:", value["messages"][-1].content)
                # print(f'  >> {type(value)} {value!r}')
                for obj in value:
                    # print(f'    >> {type(obj)} {obj!r}')
                    if isinstance(obj, Interrupt):
                        # Do I need to keep a reference to this Interrupt or its ID?
                        interrupts.append(obj.value)
        
        if not interrupts:
            return None
        
        if len(interrupts) > 1:
            # TODO: I think this can happen? Because of parallel execution?
            print(f'XXX Hey there, I got multiple interrupts: {interrupts!r}')
            raise Exception(f'XXX Hey there, I got multiple interrupts: {interrupts!r}')

        return interrupts[0]