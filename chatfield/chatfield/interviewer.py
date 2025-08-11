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
    dialogue_data: Dict[str, Any]  # Serialized dialogue data (msgpack-compatible)


class Interviewer:
    """
    Interviewer that manages conversation flow.
    """
    
    def __init__(self, dialogue: Interview):
        self.dialogue = dialogue
        self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()
        self.thread_id = str(uuid.uuid4())
        # self.llm = init_chat_model("openai:gpt-4.1")
        self.llm = init_chat_model("openai:gpt-5")

        self.state = State(
            messages=[], 
            dialogue_data=dialogue.to_msgpack_dict(),
        )
        
    def _build_graph(self):
        builder = StateGraph(State)

        builder.add_node('initialize', self.initialize)
        builder.add_node('think'     , self.think)
        builder.add_node('listen'    , self.listen)

        builder.add_edge             (START       , 'initialize')
        builder.add_edge             ('initialize', 'think')
        builder.add_conditional_edges('think'     , self.route_think)
        builder.add_edge             ('listen'    , 'think')

        graph = builder.compile(checkpointer=self.checkpointer)
        return graph
        
    def initialize(self, state:State) -> State:
        print(f'Node> Initialize')
        # print(f'State: {state!r}')
        print(f'  Data model: {self.dialogue!r}')
        # Update state with current dialogue data
        state["dialogue_data"] = self.dialogue.to_msgpack_dict()
        return state
        
    def think(self, state: State) -> State:
        print(f'Node> Think')
        print(f'{json.dumps(state["dialogue_data"], indent=2)}')
        messages = state['messages']
        if len(messages) == 0:
            print(f'  No messages yet, starting with a system message.')
            messages.append({"role": "system", "content": "You are a helpful assistant. Begin by saying the word Cheetah!"})

        new_message = self.llm.invoke(messages)
        print(f'  New message: {new_message!r}')
        state['messages'] = [new_message] # Only need the latest message
        return state
    
    def route_think(self, state: State) -> str:
        print(f'Edge> Route think')
        print(f'    > State: {state!r}')
        return 'listen'
        
    def listen(self, state: State) -> State:
        print(f'Node> Listen')
        print(f'    > Interrupt')
        find_me = {'foo': 'What is the value of XXX Foo?', 'st':state['messages'][-1].content}
        res = interrupt(find_me)
        # When things are working, this node will run a second time and interrupt will return the human input.
        print(f'    > Interrupt result is type {type(res)}: {res!r}')
        # Probably just append the user message and jump back to 'think'
        return state
        
    def go(self):
        # This function needs to return whatever the user needs to do UI, e.g. messages, etc.
        # Also they will call go repeatedly until the conversation is done, I think need a Command object
        self.config = {"configurable": {"thread_id": self.thread_id}}
        config = self.config

        # Unclear if this is the correct thing to do here.
        graph_input = self.state

        result = None
        for event in self.graph.stream(graph_input, config=config):
            # print(f'ev> {event!r}')
            for value in event.values():
                # print("Assistant:", value["messages"][-1].content)
                # print(f'  >> {type(value)} {value!r}')
                for obj in value:
                    # print(f'    >> {type(obj)} {obj!r}')
                    if isinstance(obj, Interrupt):
                        result = obj.value # No idea if there could me multiple.
        return result

        # Return the final state after processing