"""LangGraph-based evaluator for Chatfield conversations."""

import json
import uuid

from typing import Any, Dict, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt, Interrupt
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model


from .base import Interview


class State(TypedDict):
    messages: list[Dict[str, Any]]
    interview: Interview


class Interviewer:
    """
    Interviewer that manages conversation flow.
    """
    
    def __init__(self, interview: Interview):
        self.interview = interview
        self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()
        self.thread_id = str(uuid.uuid4()) # TODO: Let me pass a value or set an environment variable to make this easy to find in LangSmith
        self.llm = init_chat_model("openai:gpt-4.1")
        # self.llm = init_chat_model("openai:gpt-5")

        self.config = {"configurable": {"thread_id": self.thread_id}}

    def _build_graph(self):
        builder = StateGraph(State)

        builder.add_node('initialize', self.initialize)
        builder.add_node('think'     , self.think)
        builder.add_node('listen'    , self.listen)

        builder.add_edge             (START       , 'initialize')
        builder.add_edge             ('initialize', 'think')
        builder.add_conditional_edges('think'     , self.route_think)
        builder.add_edge             ('listen'    , 'think')

        # TODO: Needs a tool node to update the interview.
        graph = builder.compile(checkpointer=self.checkpointer)
        return graph
        
    def initialize(self, state:State) -> State:
        print(f'Node> Initialize')
        # print(f'State: {state!r}')
        # print(f'  Data model: {self.dialogue!r}')
        # Update state with current dialogue data
        # state["dialogue_data"] = self.dialogue.to_msgpack_dict()
        return state
        
    def think(self, state: State) -> State:
        print(f'Node> Think')
        # print(f'{state["interview"]}')
        messages = state['messages']
        if len(messages) == 0:
            print(f'  No messages yet, starting with a system message.')
            system_prompt = self.mk_system_prompt(state)
            messages.append({"role": "system", "content": system_prompt})

        new_message = self.llm.invoke(messages)
        print(f'  New message: {new_message!r}')
        state['messages'] = [new_message] # Only need the latest message
        return state
    
    def mk_system_prompt(self, state: State) -> str:
        interview = state['interview']

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
            field_label = f'**{field_name}**'
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

            field_specs = '\n'.join(f'    - {spec}' for spec in specs_prompts) if specs_prompts else ''
            field_casts = '\n'.join(f'    - {cast}' for cast in casts_prompts) if casts_prompts else ''

            field_prompt = (
                f'- {field_label}\n'
                f'{field_specs}'
                f'{field_casts}'
            )
            fields.append(field_prompt)
        fields = '\n'.join(fields)

        res = (
            f'You are a conversational {alice_role_type} focused on gathering key information in conversation with the {bob_role_type},'
            f' into a collection called {collection_name}, described in detail below.'
            f' Although the {bob_role_type} may take the conversation anywhere, your response must fit the conversation and your respective roles'
            f' while refocusing the discussion so that you can gather clear key {collection_name} information from the {bob_role_type}.'
            # TODO Traits of alice and bob
            f'\n\n----\n\n'
            f'# Collection: {collection_name}\n'
            f'\n'
            f'{fields}\n'
        )
        return res
    
    def route_think(self, state: State) -> str:
        print(f'Edge> Route think')
        print(f'    > State: {state!r}')
        return 'listen'
        
    def listen(self, state: State) -> State:
        print(f'Node> Listen')
        print(f'    > All messages in the state:\n{state!r}')
        request = {'ok':True}
        response = interrupt(request)
        # When things are working, this node will run a second time and interrupt will return the human input.
        print(f'    > Interrupt result is type {type(response)}: {response!r}')
        # Probably just append the user message and jump back to 'think'
        return state
        
    def go(self):
        # This function needs to return whatever the user needs to do UI, e.g. messages, etc.
        # Also they will call go repeatedly until the conversation is done, I think need a Command object

        # Unclear if this is the correct thing to do here.
        graph_input = State(
            messages=[], 
            interview=self.interview,
        )

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
            raise Exception(f'XXX Hey there, I got multiple interrupts: {interrupts!r}')

        return interrupts[0]